"""
Lecteur OBD-II (dongle ELM327) via la lib `python-OBD`.

Publie : coolant_temp, boost, oil_temp (si dispo), fuel_inst, fuel_avg.

IMPORTANT — Hilux 2008 diesel (1KD-FTV) :
  * coolant_temp : PID standard, quasi toujours dispo.
  * boost : dérivé du PID MAP (INTAKE_PRESSURE) - pression atmo (~1.0 bar).
            Si le PID n'est pas exposé, laisser sensors.boost_from_adc = true.
  * oil_temp : rarement exposé en OBD -> souvent fourni par sensors_reader.
  * conso : pas de PID FUEL_RATE fiable sur ce moteur en général.
            On tente FUEL_RATE ; sinon estimation via MAF + vitesse (approx.).
"""
import time
import threading


class ObdReader(threading.Thread):
    def __init__(self, cfg, pub, stop_event):
        super().__init__(daemon=True, name="obd")
        self.cfg = cfg
        self.pub = pub
        self.stop = stop_event
        self.simulate = cfg.get("simulate", False)
        self.density = cfg.get("diesel_density", 835.0)
        self.afr = cfg.get("afr", 18.0)
        self._fuel_hist = []          # pour la moyenne glissante
        self._supported = {}

    # --------------------------------------------------------------- #
    def run(self):
        if self.simulate:
            self._run_sim()
            return
        try:
            import obd
        except ImportError:
            print("[obd] python-OBD absent -> bascule en simulation")
            self._run_sim()
            return

        connection = obd.OBD(self.cfg["port"], baudrate=self.cfg.get("baudrate", 38400))
        if not connection.is_connected():
            print("[obd] connexion ELM327 impossible -> simulation")
            self._run_sim()
            return

        # Cache des commandes réellement supportées par le calculateur
        cmds = connection.supported_commands
        self._supported = {
            "coolant": obd.commands.COOLANT_TEMP in cmds,
            "map": obd.commands.INTAKE_PRESSURE in cmds,
            "oil": getattr(obd.commands, "OIL_TEMP", None) in cmds,
            "fuel_rate": getattr(obd.commands, "FUEL_RATE", None) in cmds,
            "maf": obd.commands.MAF in cmds,
            "speed": obd.commands.SPEED in cmds,
        }
        print(f"[obd] PID supportés : {self._supported}")

        period = 1.0 / self.cfg.get("rate", 3)
        while not self.stop.is_set():
            self._poll(obd, connection)
            time.sleep(period)
        connection.close()

    # --------------------------------------------------------------- #
    def _poll(self, obd, conn):
        def val(cmd):
            r = conn.query(cmd)
            return None if r.is_null() else r.value.magnitude

        if self._supported.get("coolant"):
            self.pub.publish("coolant_temp", val(obd.commands.COOLANT_TEMP))

        if self._supported.get("map"):
            map_kpa = val(obd.commands.INTAKE_PRESSURE)  # kPa absolu
            if map_kpa is not None:
                boost_bar = max(0.0, (map_kpa - 101.3) / 100.0)
                self.pub.publish("boost", boost_bar)

        if self._supported.get("oil"):
            self.pub.publish("oil_temp", val(obd.commands.OIL_TEMP))

        # ---- consommation ----
        inst = None
        speed = val(obd.commands.SPEED) if self._supported.get("speed") else None
        if self._supported.get("fuel_rate"):
            lph = val(obd.commands.FUEL_RATE)           # L/h
            inst = self._lph_to_l100(lph, speed)
        elif self._supported.get("maf"):
            maf = val(obd.commands.MAF)                 # g/s d'air
            if maf is not None:
                fuel_gps = maf / self.afr               # g/s de gazole (approx.)
                lph = fuel_gps / self.density * 3600.0
                inst = self._lph_to_l100(lph, speed)

        if inst is not None:
            self.pub.publish("fuel_inst", inst)
            self._fuel_hist.append(inst)
            self._fuel_hist = self._fuel_hist[-600:]    # ~ dernières minutes
            avg = sum(self._fuel_hist) / len(self._fuel_hist)
            self.pub.publish("fuel_avg", avg)

    @staticmethod
    def _lph_to_l100(lph, speed_kmh):
        if lph is None:
            return None
        if not speed_kmh or speed_kmh < 3:
            return 0.0            # à l'arrêt on n'exprime pas des L/100km
        return lph / speed_kmh * 100.0

    # --------------------------------------------------------------- #
    def _run_sim(self):
        import math
        t0 = time.time()
        while not self.stop.is_set():
            t = time.time() - t0
            self.pub.publish("coolant_temp", 88 + 4 * math.sin(t / 15))
            self.pub.publish("oil_temp", 90 + 8 * math.sin(t / 20))
            self.pub.publish("boost", max(0.0, 0.8 + 0.7 * math.sin(t / 3)))
            inst = max(0.0, 7 + 6 * math.sin(t / 4))
            self.pub.publish("fuel_inst", inst)
            self.pub.publish("fuel_avg", 8.5 + 0.5 * math.sin(t / 30))
            time.sleep(0.3)
