#!/bin/bash
# Lance l'interface Kivy en plein écran, branchée sur MQTT.
# Utilisé soit directement (dans une session X), soit via startx / autostart.

cd "$(dirname "$0")/.."          # -> dossier hilux_dash
source venv/bin/activate

# Source des données : mqtt (réel/simulé via le service) ou dummy (autonome)
export HILUX_SOURCE=mqtt

# Plein écran kiosk (masque aussi le curseur souris)
export HILUX_FULLSCREEN=1

# Masque le curseur souris pour un rendu kiosk propre
export KIVY_BCM_DISPMANX_ID=0

exec python main.py
