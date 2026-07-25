"""
Gestion centralisée du thème (mode jour / nuit).

Les couleurs sont exposées comme propriétés Kivy sur l'App (voir
main.py::apply_theme), si bien qu'un simple changement de `night_mode`
propage instantanément les nouvelles couleurs à *tous* les widgets qui s'y
sont liés dans les fichiers .kv et dans widgets.py.
"""

# Palette JOUR : fond clair, texte foncé, accent bleu.
DAY = {
    "bg":        (0.93, 0.94, 0.96, 1),
    "surface":   (1.00, 1.00, 1.00, 1),
    "text":      (0.10, 0.11, 0.13, 1),
    "text_dim":  (0.35, 0.37, 0.40, 1),
    "accent":    (0.13, 0.45, 0.85, 1),
    "ok":        (0.16, 0.65, 0.34, 1),
    "warn":      (0.90, 0.60, 0.10, 1),
    "alarm":     (0.85, 0.20, 0.20, 1),
    "topbar":    (0.16, 0.18, 0.22, 1),
    "topbar_tx": (0.95, 0.96, 0.98, 1),
}

# Palette NUIT : quasi-noir chaud, ambre adouci. Les couleurs d'alerte sont
# volontairement assombries/désaturées par rapport au jour (et non de
# simples copies) pour rester lisibles sans éblouir de nuit. `alarm` reste
# le canal le plus lumineux des trois pour préserver la hiérarchie de
# sévérité (alarm > warn > ok).
NIGHT = {
    "bg":        (0.045, 0.035, 0.03, 1),
    "surface":   (0.09, 0.075, 0.06, 1),
    "text":      (0.62, 0.42, 0.16, 1),
    "text_dim":  (0.38, 0.26, 0.11, 1),
    "accent":    (0.58, 0.40, 0.14, 1),
    "ok":        (0.22, 0.38, 0.20, 1),
    "warn":      (0.55, 0.38, 0.10, 1),
    "alarm":     (0.58, 0.17, 0.14, 1),
    "topbar":    (0.03, 0.025, 0.02, 1),
    "topbar_tx": (0.62, 0.42, 0.16, 1),
}


def palette(night: bool) -> dict:
    return NIGHT if night else DAY
