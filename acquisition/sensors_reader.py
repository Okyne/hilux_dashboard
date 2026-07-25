"""
Lecteur des capteurs additionnels :
- ext_temp  : sonde 1-Wire DS18B20 (température extérieure)
- oil_temp  : sonde 1-Wire DS18B20 (si non fournie par l'OBD)
- boost     : capteur de pression sur ADC MCP3008 (si boost_from_adc = true)

Les DS18B20 se lisent via le driver noyau 1-Wire
(/sys/bus/w1/devices/28-xxxx/w1_slave). Activer dtoverlay=w1-gpio.
"""
import time
import threading


class SensorsReader(threading.Thread):
    def __init__(self, cfg, pub, stop_event):
        super().__init__(daemon=True, name="sensors")
        self.cfg = cfg
        self.pub = pub
        self.stop = stop_event
        self.simulate = cfg.get("simulate", False)

    def run(self):
        if self.simulate:
            self._run_sim()
            return

        read_temp = self._make_ds18b20_reader()
        read_boost = self._make_adc_reader() if self.cfg.get("boost_from_adc") else None

        period = 1.0 / self.cfg.get("rate", 1)
        while not self.stop.is_set():
            ext = read_temp(self.cfg.get("ext_temp_id"))
            if ext is not None:
                self.pub.publish("ext_temp", ext)
            oil = read_temp(self.cfg.get("oil_temp_id"))
            if oil is not None:
                self.pub.publish("oil_temp", oil)
            if read_boost is not None:
                self.pub.publish("boost", read_boost())
            time.sleep(period)

    # ---- DS18B20 ----
    def _make_ds18b20_reader(self):
        base = "/sys/bus/w1/devices"

        def read(dev_id):
            if not dev_id or "xxxx" in dev_id or "yyyy" in dev_id:
                return None
            try:
                with open(f"{base}/{dev_id}/w1_slave") as f:
                    lines = f.readlines()
                if not lines[0].strip().endswith("YES"):
                    return None
                pos = lines[1].find("t=")
                return int(lines[1][pos + 2:]) / 1000.0
            except Exception:
                return None
        return read

    # ---- MCP3008 (SPI) pour le boost ----
    def _make_adc_reader(self):
        try:
            import spidev
        except ImportError:
            print("[sensors] spidev absent -> boost ADC désactivé")
            return lambda: None
        spi = spidev.SpiDev()
        spi.open(0, 0)
        spi.max_speed_hz = 1350000
        ch = self.cfg.get("adc_channel", 0)

        def read():
            r = spi.xfer2([1, (8 + ch) << 4, 0])
            raw = ((r[1] & 3) << 8) | r[2]          # 0..1023
            volts = raw / 1023.0 * 3.3
            # à calibrer selon le capteur : ex. 0.5V=0bar ... 4.5V=3bar
            bar = max(0.0, (volts - 0.5) / (4.5 - 0.5) * 3.0)
            return bar
        return read

    def _run_sim(self):
        import math
        t0 = time.time()
        while not self.stop.is_set():
            t = time.time() - t0
            self.pub.publish("ext_temp", 21 + 3 * math.sin(t / 60))
            time.sleep(1.0)
