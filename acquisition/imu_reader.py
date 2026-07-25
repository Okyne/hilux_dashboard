"""
Lecteur d'inclinaison via IMU MPU-6050 / MPU-9250 (I2C).

Publie : roll (roulis, + = penche à droite), pitch (tangage, + = nez en bas).

On calcule les angles à partir de l'accéléromètre (suffisant pour de
l'inclinaison statique de véhicule). Un filtre passe-bas lisse les vibrations.
Les offsets de calibration (véhicule à plat) viennent de config.yaml.
"""
import time
import math
import threading


MPU_ADDR_REG_PWR = 0x6B
ACCEL_XOUT_H = 0x3B


class ImuReader(threading.Thread):
    def __init__(self, cfg, pub, stop_event):
        super().__init__(daemon=True, name="imu")
        self.cfg = cfg
        self.pub = pub
        self.stop = stop_event
        self.simulate = cfg.get("simulate", False)
        self.off_roll = cfg.get("offset_roll", 0.0)
        self.off_pitch = cfg.get("offset_pitch", 0.0)
        self._roll = 0.0
        self._pitch = 0.0

    def run(self):
        if self.simulate:
            self._run_sim()
            return
        try:
            import smbus2
        except ImportError:
            print("[imu] smbus2 absent -> simulation")
            self._run_sim()
            return

        try:
            bus = smbus2.SMBus(self.cfg.get("i2c_bus", 1))
            addr = self.cfg.get("address", 0x68)
            bus.write_byte_data(addr, MPU_ADDR_REG_PWR, 0)   # réveil du capteur
        except Exception as e:
            print(f"[imu] init I2C impossible ({e}) -> simulation")
            self._run_sim()
            return

        period = 1.0 / self.cfg.get("rate", 20)
        alpha = 0.15   # coefficient du filtre passe-bas
        while not self.stop.is_set():
            try:
                ax, ay, az = self._read_accel(bus, addr)
                roll = math.degrees(math.atan2(ay, az))
                pitch = math.degrees(math.atan2(-ax, math.hypot(ay, az)))
                # lissage
                self._roll = (1 - alpha) * self._roll + alpha * roll
                self._pitch = (1 - alpha) * self._pitch + alpha * pitch
                self.pub.publish("roll", self._roll - self.off_roll)
                self.pub.publish("pitch", self._pitch - self.off_pitch)
            except Exception as e:
                print(f"[imu] lecture: {e}")
            time.sleep(period)

    def _read_accel(self, bus, addr):
        def word(reg):
            hi = bus.read_byte_data(addr, reg)
            lo = bus.read_byte_data(addr, reg + 1)
            v = (hi << 8) | lo
            return v - 65536 if v >= 0x8000 else v
        # pleine échelle par défaut ±2g -> 16384 LSB/g
        ax = word(ACCEL_XOUT_H) / 16384.0
        ay = word(ACCEL_XOUT_H + 2) / 16384.0
        az = word(ACCEL_XOUT_H + 4) / 16384.0
        return ax, ay, az

    def _run_sim(self):
        t0 = time.time()
        while not self.stop.is_set():
            t = time.time() - t0
            self.pub.publish("roll", 12 * math.sin(t / 5))
            self.pub.publish("pitch", 8 * math.sin(t / 7))
            time.sleep(0.1)
