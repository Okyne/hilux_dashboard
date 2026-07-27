# Hilux Dashboard — squelette Kivy

Interface tactile plein écran (4 écrans) pour datalogger embarqué sur
Toyota Hilux 2008 + Raspberry Pi 3 B. Ce dépôt est le **squelette de l'UI** :
il tourne immédiatement avec des données factices, prêt à recevoir la vraie
chaîne d'acquisition.

## Contenu

| Fichier      | Rôle                                                       |
| ------------ | ---------------------------------------------------------- |
| `main.py`    | Application, ScreenManager, thème, navigation, shutdown    |
| `hilux.kv`   | Mise en page déclarative des 5 écrans + barre globale      |
| `widgets.py` | Widgets canvas : jauge, inclinomètre, schéma pneus, TopBar |
| `screens.py` | Logique de rafraîchissement des écrans                     |
| `theme.py`   | Palettes jour / nuit centralisées                          |
| `data.py`    | Source de données factice (à remplacer par un client MQTT) |

## Écrans

1. **Moteur** : 6 jauges (huile, liquide, boost, conso moy/inst, temp ext.)
2. **Inclinaison** : roulis + tangage (silhouette qui s'incline, code couleur)
3. **Pneus** : vue de dessus, 4 pressions colorées selon écart à la cible

Barre globale (sur tous les écrans) : navigation + **Nuit/Jour**, **Réglages**,
**Arrêt** (avec popup de confirmation).

## Installation

```bash
python3 -m venv venv
source venv/bin/activate
pip install "kivy[base]"
python main.py
```

Testé pensé pour desktop (dev) et Raspberry Pi. Sur le Pi, active le plein
écran dans `main.py` (`Config.set("graphics", "fullscreen", "auto")`).

## Brancher les vraies données

Dans `main.py`, remplace `DummyDataSource` par un client MQTT qui met à jour
le même dictionnaire `source.values`. Le reste de l'UI ne change pas.
Clés attendues : `oil_temp`, `coolant_temp`, `boost`, `fuel_avg`, `fuel_inst`,
`ext_temp`, `roll`, `pitch`, `tire_fl`, `tire_fr`, `tire_rl`, `tire_rr`.

## Démarrage auto (Pi, systemd) — exemple

```ini
# /etc/systemd/system/hilux-ui.service
[Unit]
Description=Hilux Dashboard UI
After=graphical.target hilux-acquisition.service

[Service]
User=pi
WorkingDirectory=/home/pi/hilux_dash
ExecStart=/home/pi/hilux_dash/venv/bin/python main.py
Restart=always

[Install]
WantedBy=graphical.target
```
