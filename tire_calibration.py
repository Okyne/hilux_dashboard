"""
Correction vitesse/consommation/trip pour une taille de pneu non standard.

Le véhicule est calibré pour des pneus 255/70 R15 : sa vitesse et son
kilométrage sont dérivés du nombre de tours de roue multiplié par la
circonférence de roulement de cette taille de référence. Monter une taille
différente change la circonférence réelle sans que le véhicule le sache, ce
qui fausse vitesse, distance parcourue et consommation affichées.

Convention de taille de pneu : largeur (mm) / hauteur de flanc en % de la
largeur (aspect ratio) / diamètre de jante (pouces) — ex. 255/70 R15.
"""
import json
import os

REFERENCE_TIRE = {"width": 255, "aspect": 70, "rim": 15}

DEFAULT_SETTINGS_PATH = os.path.expanduser("~/.hilux_tire_settings.json")


def circumference_mm(width, aspect, rim):
    """Circonférence de roulement (mm) pour un pneu width/aspect Rrim."""
    diameter_mm = rim * 25.4 + 2 * (width * aspect / 100)
    return 3.141592653589793 * diameter_mm


def speed_ratio(width, aspect, rim, reference=REFERENCE_TIRE):
    """Facteur multiplicatif à appliquer à la vitesse/distance indiquées.

    > 1 : le pneu monté est plus grand que la référence -> le véhicule
    sous-estime vitesse et distance réelles (et sur-estime la consommation
    au L/100km, d'où la division par ce même ratio pour la corriger).
    """
    return circumference_mm(width, aspect, rim) / circumference_mm(**reference)


def load_settings(path=DEFAULT_SETTINGS_PATH):
    """Taille de pneu actuellement montée, persistée sur disque.

    Retourne une copie de REFERENCE_TIRE si le fichier n'existe pas ou est
    invalide, pour que l'app démarre toujours avec un ratio de 1.0.
    """
    try:
        with open(path) as f:
            data = json.load(f)
        return {
            "width": float(data["width"]),
            "aspect": float(data["aspect"]),
            "rim": float(data["rim"]),
        }
    except (OSError, ValueError, KeyError, TypeError):
        return dict(REFERENCE_TIRE)


def save_settings(width, aspect, rim, path=DEFAULT_SETTINGS_PATH):
    with open(path, "w") as f:
        json.dump({"width": width, "aspect": aspect, "rim": rim}, f)
