#!/bin/bash
# Lance le service d'acquisition (tout en simulation tant que les capteurs
# ne sont pas branchés / config.yaml pas réglé).

cd "$(dirname "$0")/.."          # -> dossier hilux_dash
source venv/bin/activate
exec python acquisition/main.py
