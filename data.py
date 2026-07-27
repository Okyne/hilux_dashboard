"""
Source de données factice pour développer l'UI sans le véhicule.

En production, remplace `DummyDataSource` par un client MQTT qui s'abonne
aux topics publiés par le service d'acquisition (voir volet « Chaîne
d'acquisition + MQTT »). L'interface reste identique : l'UI lit
`source.values` que la Clock rafraîchit périodiquement.
"""
import math
import time
import random


class DummyDataSource:
    """Génère des valeurs plausibles qui bougent, pour tester l'affichage."""

    def __init__(self):
        self._t0 = time.time()
        self.values = {
            # écran 1 — moteur
            "oil_temp": 0.0,        # °C
            "coolant_temp": 0.0,    # °C
            "boost": 0.0,           # bar (relatif)
            "fuel_avg": 0.0,        # L/100km
            "fuel_inst": 0.0,       # L/100km
            "ext_temp": 0.0,        # °C
            "speed": 0.0,           # km/h (pas encore une source réelle, cf. CLAUDE.md)
            "heading": 0.0,         # degrés (0-359, cap boussole)
            "fuel_level": 0.0,      # fraction du réservoir (0-1)
            "fuel_range": 0.0,      # km d'autonomie estimée
            "battery_voltage": 0.0,  # V
            # écran 2 — inclinaison
            "roll": 0.0,            # deg (latéral +droite / -gauche)
            "pitch": 0.0,           # deg (+avant piqué / -arrière)
            # écran 3 — pneus (bar)
            "tire_fl": 0.0, "tire_fr": 0.0, "tire_rl": 0.0, "tire_rr": 0.0,
        }

    def update(self, *_):
        t = time.time() - self._t0
        v = self.values
        v["oil_temp"] = 90 + 8 * math.sin(t / 20)
        v["coolant_temp"] = 88 + 4 * math.sin(t / 15)
        v["boost"] = max(0.0, 0.8 + 0.7 * math.sin(t / 3))
        v["fuel_avg"] = 8.5 + 0.5 * math.sin(t / 30)
        v["fuel_inst"] = max(0.0, 7 + 6 * math.sin(t / 4))
        v["ext_temp"] = 21 + 3 * math.sin(t / 60)
        v["speed"] = max(0.0, 20 + 15 * math.sin(t / 25))
        v["heading"] = (t * 6) % 360
        v["fuel_level"] = 0.55 + 0.35 * math.sin(t / 90)
        v["fuel_range"] = max(0.0, v["fuel_level"] * 650)
        v["battery_voltage"] = 12.6 + 0.3 * math.sin(t / 40)
        v["roll"] = 12 * math.sin(t / 5)
        v["pitch"] = 8 * math.sin(t / 7)
        v["tire_fl"] = 2.5 + 0.05 * math.sin(t / 11)
        v["tire_fr"] = 2.5 + 0.05 * math.cos(t / 9)
        v["tire_rl"] = 2.8 + 0.05 * math.sin(t / 13)
        v["tire_rr"] = 2.2 + 0.05 * math.cos(t / 12)  # volontairement bas -> alerte
