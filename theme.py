"""
Gestion centralisée du thème (mode jour / nuit).

Les couleurs sont exposées comme propriétés Kivy sur l'App (voir
main.py::apply_theme), si bien qu'un simple changement de `night_mode`
propage instantanément les nouvelles couleurs à *tous* les widgets qui s'y
sont liés dans les fichiers .kv et dans widgets.py.
"""

# Palette JOUR : fond clair, texte foncé, accent bleu.
# accent/ok/warn/alarm repris de la charte (swatches Info/Success/Warning/Alert),
# surface/text_dim repris des swatches Primaire/Secondaire.
DAY = {
    "bg":        (0.93, 0.94, 0.96, 1),
    "surface":   (1.00, 1.00, 1.00, 1),
    "text":      (1, 1, 1, 1),
    "text_dim":  (0.412, 0.404, 0.404, 1),
    "accent":    (0.224, 0.357, 0.761, 1),
    "ok":        (0.400, 0.847, 0.255, 1),
    "warn":      (0.710, 0.427, 0.157, 1),
    "alarm":     (0.788, 0.192, 0.153, 1),
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
    "ok":        (0.251, 0.553, 0.192, 1),
    "warn":      (0.816, 0.616, 0.282, 1),
    "alarm":     (0.776, 0.314, 0.294, 1),
    "topbar":    (0.03, 0.025, 0.02, 1),
    "topbar_tx": (0.62, 0.42, 0.16, 1),
}


def palette(night: bool) -> dict:
    return NIGHT if night else DAY
