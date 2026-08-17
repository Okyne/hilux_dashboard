"""
Lecteur TPMS (pression des 4 pneus).

La plupart des kits TPMS du commerce exposent un récepteur série (USB) qui
émet, par capteur, une trame contenant un identifiant de roue et la pression.
Le format exact dépend du kit -> adapte `_parse_line` à ta trame réelle.

Publie : tire_fl, tire_fr, tire_rl, tire_rr (bar) et
tire_fl_temp, tire_fr_temp, tire_rl_temp, tire_rr_temp (°C) quand le kit les
expose (beaucoup de capteurs TPMS remontent une température avec la pression).

Mapping id_capteur -> position de roue : à renseigner après appairage
(fais tourner une roue à la fois et note l'id qui varie).
"""
import time
import threading


class TpmsReader(threading.Thread):
    # À COMPLÉTER après appairage des capteurs :
    WHEEL_MAP = {
        # "0A1B2C": "tire_fl",
        # "0A1B2D": "tire_fr",
        # "0A1B2E": "tire_rl",
        # "0A1B2F": "tire_rr",
    }

    def __init__(self, cfg, pub, stop_event):
        super().__init__(daemon=True, name="tpms")
        self.cfg = cfg
        self.pub = pub
        self.stop = stop_event
        self.simulate = cfg.get("simulate", False)

    def run(self):
        if self.simulate or not self.WHEEL_MAP:
            if not self.simulate:
                print("[tpms] WHEEL_MAP vide -> simulation en attendant l'appairage")
            self._run_sim()
            return
        try:
            import serial
        except ImportError:
            print("[tpms] pyserial absent -> simulation")
            self._run_sim()
            return

        try:
            ser = serial.Serial(self.cfg["port"], self.cfg.get("baudrate", 9600),
                                timeout=2)
        except Exception as e:
            print(f"[tpms] port série indisponible ({e}) -> simulation")
            self._run_sim()
            return

        while not self.stop.is_set():
            try:
                line = ser.readline().decode(errors="ignore").strip()
                if not line:
                    continue
                parsed = self._parse_line(line)
                if parsed:
                    sensor_id, bar, temp_c = parsed
                    key = self.WHEEL_MAP.get(sensor_id)
                    if key:
                        self.pub.publish(key, bar)
                        if temp_c is not None:
                            self.pub.publish(f"{key}_temp", temp_c)
            except Exception as e:
                print(f"[tpms] {e}")

    @staticmethod
    def _parse_line(line):
        """
        Exemple de format hypothétique : "ID=0A1B2C;P=2.53;T=28"
        Retourne (sensor_id, pression_bar, temp_c_ou_None) ou None. À ADAPTER
        à ton kit.
        """
        try:
            fields = dict(p.split("=") for p in line.split(";") if "=" in p)
            temp_c = float(fields["T"]) if "T" in fields else None
            return fields["ID"], float(fields["P"]), temp_c
        except Exception:
            return None

    def _run_sim(self):
        import math
        t0 = time.time()
        while not self.stop.is_set():
            t = time.time() - t0
            self.pub.publish("tire_fl", 2.5 + 0.05 * math.sin(t / 11))
            self.pub.publish("tire_fr", 2.5 + 0.05 * math.cos(t / 9))
            self.pub.publish("tire_rl", 2.8 + 0.05 * math.sin(t / 13))
            self.pub.publish("tire_rr", 2.2 + 0.05 * math.cos(t / 12))
            self.pub.publish("tire_fl_temp", 28 + 4 * math.sin(t / 17))
            self.pub.publish("tire_fr_temp", 29 + 4 * math.cos(t / 14))
            self.pub.publish("tire_rl_temp", 30 + 4 * math.sin(t / 19))
            self.pub.publish("tire_rr_temp", 33 + 4 * math.cos(t / 16))
            time.sleep(2.0)
