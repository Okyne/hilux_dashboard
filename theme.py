"""
Gestion centralisée du thème (mode jour / nuit).

Les couleurs sont exposées comme propriétés Kivy sur l'App, si bien qu'un
simple changement de `night_mode` propage instantanément les nouvelles
couleurs à *tous* les widgets qui s'y sont liés dans les fichiers .kv.
"""

# Palette JOUR : fond clair, texte foncé, accent bleu
DAY = {
    "bg":        (0.93, 0.94, 0.96, 1),   # fond principal
    "surface":   (1.00, 1.00, 1.00, 1),   # cartes / panneaux
    "text":      (0.10, 0.11, 0.13, 1),   # texte principal
    "text_dim":  (0.35, 0.37, 0.40, 1),   # texte secondaire
    "accent":    (0.13, 0.45, 0.85, 1),   # accent / sélection
    "ok":        (0.16, 0.65, 0.34, 1),   # valeur normale
    "warn":      (0.90, 0.60, 0.10, 1),   # alerte modérée
    "alarm":     (0.85, 0.20, 0.20, 1),   # alerte grave
    "topbar":    (0.16, 0.18, 0.22, 1),   # barre du haut
    "topbar_tx": (0.95, 0.96, 0.98, 1),   # texte barre du haut
}

# Palette NUIT : fond noir, texte/accent ambre pour ne pas éblouir
NIGHT = {
    "bg":        (0.03, 0.03, 0.04, 1),
    "surface":   (0.08, 0.08, 0.10, 1),
    "text":      (0.85, 0.55, 0.15, 1),   # ambre : préserve la vision nocturne
    "text_dim":  (0.55, 0.36, 0.10, 1),
    "accent":    (0.90, 0.60, 0.15, 1),
    "ok":        (0.30, 0.55, 0.25, 1),
    "warn":      (0.80, 0.50, 0.10, 1),
    "alarm":     (0.80, 0.20, 0.15, 1),
    "topbar":    (0.06, 0.06, 0.07, 1),
    "topbar_tx": (0.85, 0.55, 0.15, 1),
}


def palette(night: bool) -> dict:
    return NIGHT if night else DAY
