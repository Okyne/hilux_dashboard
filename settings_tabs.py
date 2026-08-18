"""
Contenu de chaque onglet de l'écran réglages (voir <SettingsScreen> / <...Tab>
dans hilux.kv pour la mise en page). Chaque classe est un onglet MDTabs
indépendant : ``MDTabsBase`` lui donne son titre/icône, la classe parente
(MDBoxLayout) porte juste la disposition de son contenu.
"""
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.tab import MDTabsBase


class CalibrationTab(MDBoxLayout, MDTabsBase):
    """Offsets roulis/tangage de l'IMU (mêmes valeurs que le bouton de
    remise à zéro de l'onglet Inclinaison)."""


class TiresSettingsTab(MDBoxLayout, MDTabsBase):
    """Pression cible et tolérance utilisées par les jauges de pneus."""


class TireSizeTab(MDBoxLayout, MDTabsBase):
    """Taille de pneu montée, utilisée pour corriger vitesse, trip et
    consommation quand elle diffère de la taille d'origine du véhicule."""


class UnitsTab(MDBoxLayout, MDTabsBase):
    """Choix des unités affichées (placeholder, pas encore implémenté)."""


class NetworkTab(MDBoxLayout, MDTabsBase):
    """Infos broker MQTT / source de données actuellement utilisée."""


class TerminalTab(MDBoxLayout, MDTabsBase):
    """Terminal shell interactif (voir terminal.TerminalConsole)."""
