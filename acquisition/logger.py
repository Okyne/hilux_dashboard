"""
Datalogging continu : s'abonne au broker MQTT et enregistre en SQLite.

- une ligne par intervalle (config logging.interval), avec la dernière
  valeur connue de chaque clé -> format large, facile à exploiter ;
- purge automatique des points trop anciens (retention_days).

Exploitation : la base est lisible avec n'importe quel outil SQLite, ou
exportable en CSV pour analyse (pandas, tableur...).
"""
import os
import time
import sqlite3
import threading

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import telemetry


class DataLogger(threading.Thread):
    def __init__(self, cfg, stop_event):
        super().__init__(daemon=True, name="logger")
        self.cfg = cfg
        self.stop = stop_event
        self.interval = cfg.get("interval", 1.0)
        self.retention = cfg.get("retention_days", 30)
        self.db_path = cfg.get("db_path", "telemetry.db")
        self.latest = {k: None for k in telemetry.KEYS}
        self._lock = threading.Lock()

    def run(self):
        import paho.mqtt.client as mqtt

        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        self._init_db(conn)

        client = mqtt.Client(client_id="hilux-logger")
        client.on_message = self._on_message
        client.connect(telemetry.BROKER_HOST, telemetry.BROKER_PORT, 30)
        client.subscribe(f"{telemetry.PREFIX}/#")
        client.loop_start()

        last_purge = 0
        while not self.stop.is_set():
            time.sleep(self.interval)
            self._write_row(conn)
            if self.retention and time.time() - last_purge > 3600:
                self._purge(conn)
                last_purge = time.time()

        client.loop_stop()
        conn.close()

    def _init_db(self, conn):
        cols = ", ".join(f"{k} REAL" for k in telemetry.KEYS)
        conn.execute(f"CREATE TABLE IF NOT EXISTS telemetry "
                     f"(ts INTEGER PRIMARY KEY, {cols})")
        conn.commit()

    def _on_message(self, client, userdata, msg):
        key = telemetry.key_from_topic(msg.topic)
        if key not in self.latest:
            return
        try:
            val = float(msg.payload.decode())
        except ValueError:
            val = None
        with self._lock:
            self.latest[key] = None if (val != val) else val   # écarte NaN

    def _write_row(self, conn):
        with self._lock:
            snapshot = dict(self.latest)
        cols = ["ts"] + telemetry.KEYS
        vals = [int(time.time())] + [snapshot[k] for k in telemetry.KEYS]
        placeholders = ", ".join("?" * len(cols))
        conn.execute(f"INSERT OR REPLACE INTO telemetry ({', '.join(cols)}) "
                     f"VALUES ({placeholders})", vals)
        conn.commit()

    def _purge(self, conn):
        cutoff = int(time.time()) - self.retention * 86400
        conn.execute("DELETE FROM telemetry WHERE ts < ?", (cutoff,))
        conn.commit()
