"""
Application KivyMD — tableau de bord Hilux (habillage Material Design).

Lancement (dev PC ou Pi) :
    HILUX_SOURCE=mqtt python main.py     # données via le broker
    python main.py                       # données factices autonomes

Dépendances : kivy 2.1 + kivymd 1.1.1
"""
import os
import time
from kivy.config import Config

Config.set("graphics", "width", "1024")
Config.set("graphics", "height", "600")
# Sur le Pi (kiosk plein écran), décommente :
# Config.set("graphics", "fullscreen", "auto")
# Config.set("graphics", "show_cursor", "0")

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, StringProperty

from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.screen import MDScreen

# Enregistre les widgets canvas pour le .kv
from widgets import VBarGauge, HBarGauge, HeadingArrow, TiltIndicator, TireDiagram  # noqa: F401
from data import DummyDataSource

import theme

# Ordre des onglets (doit correspondre aux `name:` des MDBottomNavigationItem
# dans hilux.kv) : pilote la navigation par swipe gauche/droite.
SCREEN_ORDER = ["engine", "tilt", "tires"]
SWIPE_THRESHOLD = dp(60)

_COMPASS_POINTS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]


def _cardinal(deg):
    """Point cardinal (8 directions) le plus proche d'un cap en degrés."""
    return _COMPASS_POINTS[int(deg % 360 / 45 + 0.5) % 8]


def _fr(value, fmt="{:.1f}"):
    """Formate un nombre avec une virgule décimale (convention française)."""
    return fmt.format(value).replace(".", ",")


class RootScreen(MDScreen):
    """Écran racine : ajoute le swipe gauche/droite entre les onglets.

    On ne consomme jamais le touch (toujours super()) pour ne pas casser
    les boutons/cartes ; on se contente d'observer le déplacement net
    entre l'appui et le relâchement.
    """

    def on_touch_down(self, touch):
        touch.ud["_swipe_x"] = touch.x
        touch.ud["_swipe_y"] = touch.y
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if "_swipe_x" in touch.ud:
            dx = touch.x - touch.ud["_swipe_x"]
            dy = touch.y - touch.ud["_swipe_y"]
            if abs(dx) > SWIPE_THRESHOLD and abs(dx) > abs(dy) * 1.5:
                App.get_running_app().swipe_tab(1 if dx < 0 else -1)
        return super().on_touch_up(touch)


class HiluxApp(MDApp):
    night_mode = BooleanProperty(False)

    # Couleurs dérivées du thème, consommées par les widgets canvas (jauges...)
    c_surface = ListProperty([1, 1, 1, 1])
    c_text = ListProperty([0, 0, 0, 1])
    c_text_dim = ListProperty([0.4, 0.4, 0.4, 1])
    c_accent = ListProperty([0.13, 0.45, 0.85, 1])
    c_ok = ListProperty([0.16, 0.65, 0.34, 1])
    c_warn = ListProperty([0.90, 0.60, 0.10, 1])
    c_alarm = ListProperty([0.85, 0.20, 0.20, 1])

    bg_image = StringProperty("assets/bg_day.png")
    clock_str = StringProperty("--:--")

    def build(self):
        # Thème Material 3
        self.theme_cls.material_style = "M3"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.bind(theme_style=lambda *a: self.apply_theme())

        # Source de données
        if os.environ.get("HILUX_SOURCE") == "mqtt":
            from mqtt_source import MqttDataSource
            self.source = MqttDataSource()
        else:
            self.source = DummyDataSource()

        root = RootScreen()
        nav = root.ids.nav
        nav.remove_widget(nav.ids.bottom_panel)  # footer retiré (swipe only)

        self._topbar = root.ids.topbar
        self.apply_theme()
        self._dialog = None
        Clock.schedule_interval(self._tick, 1 / 5.0)   # 5 Hz
        return root

    def swipe_tab(self, direction):
        nav = self.root.ids.nav
        tab_manager = nav.ids.tab_manager
        if tab_manager.transition.is_active:
            return  # ignore le swipe tant que la transition en cours n'est pas finie
        idx = SCREEN_ORDER.index(tab_manager.current) + direction
        if 0 <= idx < len(SCREEN_ORDER):
            nav.switch_tab(SCREEN_ORDER[idx])

    # ---------------- thème ----------------
    def apply_theme(self):
        p = theme.palette(self.night_mode)
        self.c_surface = list(p["surface"])
        self.c_text = list(p["text"])
        self.c_text_dim = list(p["text_dim"])
        self.c_accent = list(p["accent"])
        self.c_ok = list(p["ok"])
        self.c_warn = list(p["warn"])
        self.c_alarm = list(p["alarm"])
        self.bg_image = "assets/bg_night.png" if self.night_mode else "assets/bg_day.png"
        # MDTopAppBar réaligne md_bg_color sur le primary_color du thème à
        # chaque changement de primary_palette (cf. son propre binding
        # interne) : on la repasse en transparent juste après, sinon la
        # barre redevient bleue/ambrée à chaque toggle_night().
        self._topbar.md_bg_color = (0, 0, 0, 0.01)

    def toggle_night(self):
        self.night_mode = not self.night_mode
        if self.night_mode:
            self.theme_cls.theme_style = "Dark"
            self.theme_cls.primary_palette = "Amber"   # ambre : vision nocturne
        else:
            self.theme_cls.theme_style = "Light"
            self.theme_cls.primary_palette = "Blue"
        self.apply_theme()

    # ---------------- boucle de rafraîchissement ----------------
    def _tick(self, dt):
        self.source.update()
        ids = self.root.ids
        v = self.source.values
        gauges = {
            "g_oil_bar": "oil_temp", "g_coolant_bar": "coolant_temp",
            "g_fuel_bar": "fuel_level",
        }
        for wid, key in gauges.items():
            if wid in ids:
                ids[wid].value = v.get(key, 0.0)
        if "g_ext" in ids:
            ids["g_ext"].text = "{:.0f}°".format(v["ext_temp"])
        self.clock_str = time.strftime("%H:%M")
        if "g_speed" in ids:
            ids["g_speed"].text = "{:.0f}".format(v.get("speed", 0.0))
        if "g_heading" in ids:
            ids["g_heading"].text = _cardinal(v.get("heading", 0.0))
        if "g_fuel_inst" in ids:
            ids["g_fuel_inst"].text = "[size=28sp][b]{}[/b][/size] l/100km".format(
                _fr(v["fuel_inst"]))
        if "g_fuel_avg" in ids:
            ids["g_fuel_avg"].text = "[size=28sp][b]{}[/b][/size] l/100km".format(
                _fr(v["fuel_avg"]))
        if "g_battery" in ids:
            ids["g_battery"].text = "{} [size=14sp]v[/size]".format(
                _fr(v.get("battery_voltage", 0.0)))
        if "g_range" in ids:
            ids["g_range"].text = "{:.0f} [size=14sp]km[/size]".format(
                v.get("fuel_range", 0.0))
        if "roll" in ids:
            ids["roll"].angle = v["roll"]
        if "pitch" in ids:
            ids["pitch"].angle = v["pitch"]
        if "tires" in ids:
            t = ids["tires"]
            t.fl, t.fr, t.rl, t.rr = (
                v["tire_fl"], v["tire_fr"], v["tire_rl"], v["tire_rr"])

    # ---------------- dialogues ----------------
    def open_settings(self):
        self._close_dialog()
        self._dialog = MDDialog(
            title="Réglages",
            text="Calibration IMU, seuils de pression, choix caméra, unités...\n"
                 "(à compléter)",
            buttons=[MDFlatButton(text="FERMER",
                                  on_release=lambda *_: self._close_dialog())],
        )
        self._dialog.open()

    def ask_shutdown(self):
        self._close_dialog()
        self._dialog = MDDialog(
            title="Éteindre le système ?",
            text="Le Raspberry Pi va s'arrêter proprement.",
            buttons=[
                MDFlatButton(text="ANNULER",
                             on_release=lambda *_: self._close_dialog()),
                MDRaisedButton(text="ÉTEINDRE",
                               on_release=lambda *_: self._do_shutdown()),
            ],
        )
        self._dialog.open()

    def _close_dialog(self):
        if self._dialog:
            self._dialog.dismiss()
            self._dialog = None

    def _do_shutdown(self):
        self._close_dialog()
        # Sur le Pi : arrêt propre (évite la corruption de la carte SD)
        # os.system("sudo shutdown -h now")
        print("[shutdown] demande d'arrêt (décommente os.system sur le Pi)")


if __name__ == "__main__":
    HiluxApp().run()
