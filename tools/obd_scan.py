#!/usr/bin/env python3
"""
Outil de diagnostic OBD-II — à lancer une fois, dongle branché, MOTEUR TOURNANT.

But : découvrir précisément quels PID ton Hilux expose, pour remplir
config.yaml en connaissance de cause et savoir quels capteurs additionnels
sont réellement nécessaires (boost, huile, conso).

Ce script NE dépend PAS du reste du projet : il ne fait que lire l'OBD et
imprimer un rapport lisible.

Usage :
    python tools/obd_scan.py                 # auto-détection du port
    python tools/obd_scan.py /dev/ttyUSB0    # port forcé
    python tools/obd_scan.py /dev/rfcomm0    # dongle Bluetooth

Prérequis : pip install obd
"""
import sys
import time

try:
    import obd
except ImportError:
    sys.exit("python-OBD manquant : pip install obd")


# PID clés pour CE projet, regroupés par écran / usage
TARGETS = {
    "Refroidissement (ecran 1)": ["COOLANT_TEMP"],
    "Turbo / boost (ecran 1)":   ["INTAKE_PRESSURE", "BAROMETRIC_PRESSURE"],
    "Huile moteur (ecran 1)":    ["OIL_TEMP"],
    "Conso — direct (ecran 1)":  ["FUEL_RATE"],
    "Conso — estimation":        ["MAF", "SPEED", "RPM", "ENGINE_LOAD"],
    "Air admission":             ["INTAKE_TEMP", "AMBIANT_AIR_TEMP"],
}


def connect(port=None):
    print("Connexion au dongle (auto-détection du protocole)...")
    conn = obd.OBD(port) if port else obd.OBD()
    if not conn.is_connected():
        sys.exit("ECHEC : dongle non détecté. Vérifie le port, le contact mis, "
                 "et que le moteur tourne.")
    print(f"OK — protocole détecté : {conn.protocol_name()} "
          f"(id {conn.protocol_id()})")
    return conn


def sample(conn, cmd, tries=3):
    """Lit une commande plusieurs fois et renvoie une valeur non nulle si possible."""
    for _ in range(tries):
        r = conn.query(cmd, force=True)
        if not r.is_null():
            return r.value
        time.sleep(0.2)
    return None


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else None
    conn = connect(port)

    supported = conn.supported_commands
    print(f"\nNombre total de PID supportés par le véhicule : {len(supported)}\n")

    print("=" * 68)
    print("  RAPPORT CIBLÉ (ce dont le tableau de bord a besoin)")
    print("=" * 68)

    verdicts = {}
    for group, names in TARGETS.items():
        print(f"\n### {group}")
        for name in names:
            cmd = obd.commands.__dict__.get(name)
            if cmd is None or cmd not in obd.commands:
                print(f"  - {name:<22} : commande inconnue de python-OBD")
                continue
            if cmd not in supported:
                print(f"  - {name:<22} : NON supporté")
                verdicts[name] = False
                continue
            val = sample(conn, cmd)
            shown = "supporté (pas de valeur à l'arrêt ?)" if val is None else f"= {val}"
            print(f"  - {name:<22} : SUPPORTÉ   {shown}")
            verdicts[name] = True

    # ---- Conclusions automatiques ----
    print("\n" + "=" * 68)
    print("  CONCLUSIONS")
    print("=" * 68)

    def ok(n):
        return verdicts.get(n, False)

    print(f"- Temp. liquide refroid. : {'OBD ✔' if ok('COOLANT_TEMP') else 'CAPTEUR requis'}")

    if ok("INTAKE_PRESSURE"):
        print("- Turbo (boost)          : OBD ✔ (boost = INTAKE_PRESSURE - pression atmo)")
    else:
        print("- Turbo (boost)          : CAPTEUR de pression requis (ADC MCP3008)")

    print(f"- Temp. huile moteur     : {'OBD ✔' if ok('OIL_TEMP') else 'SONDE dédiée requise (DS18B20/thermocouple)'}")

    if ok("FUEL_RATE"):
        print("- Consommation           : OBD ✔ (PID FUEL_RATE direct, fiable)")
    elif ok("MAF") and ok("SPEED"):
        print("- Consommation           : ESTIMATION possible (MAF+vitesse, approximative)")
    else:
        print("- Consommation           : difficile (ni FUEL_RATE ni MAF) -> à rediscuter")

    print("\nAstuce : relance MOTEUR TOURNANT et roues en mouvement pour voir "
          "vitesse/MAF/boost varier réellement.")
    conn.close()


if __name__ == "__main__":
    main()
