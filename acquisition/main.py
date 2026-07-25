"""
Orchestrateur du service d'acquisition.

Démarre le broker-client, lance chaque lecteur activé dans son thread, plus
le datalogger, et attend proprement l'arrêt (Ctrl-C ou stop systemd).

Lancement :
    python -m acquisition.main            # depuis le dossier hilux_dash
    # ou
    python acquisition/main.py
"""
import os
import sys
import time
import signal
import threading

import yaml

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from acquisition.publisher import Publisher
from acquisition.obd_reader import ObdReader
from acquisition.imu_reader import ImuReader
from acquisition.sensors_reader import SensorsReader
from acquisition.tpms_reader import TpmsReader
from acquisition.logger import DataLogger


def load_config():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(here, "config.yaml")) as f:
        return yaml.safe_load(f)


def main():
    cfg = load_config()
    stop = threading.Event()

    pub = Publisher(host=cfg["mqtt"]["host"], port=cfg["mqtt"]["port"])

    threads = []
    if cfg["obd"].get("enabled", True):
        threads.append(ObdReader(cfg["obd"], pub, stop))
    if cfg["imu"].get("enabled", True):
        threads.append(ImuReader(cfg["imu"], pub, stop))
    if cfg["sensors"].get("enabled", True):
        threads.append(SensorsReader(cfg["sensors"], pub, stop))
    if cfg["tpms"].get("enabled", True):
        threads.append(TpmsReader(cfg["tpms"], pub, stop))

    for t in threads:
        t.start()
        print(f"[acq] thread démarré : {t.name}")

    def handle_stop(*_):
        print("\n[acq] arrêt demandé...")
        stop.set()
    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    while not stop.is_set():
        time.sleep(0.5)

    for t in threads:
        t.join(timeout=3)
    pub.close()
    print("[acq] arrêté proprement.")


if __name__ == "__main__":
    main()
