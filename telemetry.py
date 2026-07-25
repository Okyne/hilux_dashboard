"""
Contrat commun entre le service d'acquisition et l'UI.

Une seule source de vérité pour :
- l'adresse du broker MQTT,
- le préfixe et la liste des clés de télémétrie,
- le format des messages.

Convention de topic : "{PREFIX}/{cle}"  ->  ex. "hilux/coolant_temp"
Payload : un flottant encodé en texte UTF-8 (simple, lisible, léger).
Valeur spéciale "nan" = donnée indisponible (PID absent, capteur HS...).
"""

BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883
PREFIX = "hilux"

# Toutes les clés que l'UI sait afficher (identiques à data.py)
KEYS = [
    "oil_temp", "coolant_temp", "boost", "fuel_avg", "fuel_inst", "ext_temp",
    "roll", "pitch",
    "tire_fl", "tire_fr", "tire_rl", "tire_rr",
]


def topic(key: str) -> str:
    return f"{PREFIX}/{key}"


def key_from_topic(t: str) -> str:
    return t.split("/", 1)[-1]
