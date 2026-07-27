"""
Application KivyMD — tableau de bord Hilux (habillage Material Design).

Lancement (dev PC ou Pi) :
    HILUX_SOURCE=mqtt python main.py     # données via le broker
    python main.py                       # données factices autonomes

Dépendances : kivy 2.1 + kivymd 1.1.1
"""
import os
from kivy.config import Config

Config.set("graphics", "width", "1024")
Config.set("graphics", "height", "600")
# Sur le Pi (kiosk plein écran), décommente :
# Config.set("graphics", "fullscreen", "auto")
# Config.set("graphics", "show_cursor", "0")

from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import BooleanProperty, ListProperty
from kivy.factory import Factory

from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.label import MDLabel

# Enregistre les widgets canvas pour le .kv
from widgets import Gauge, TiltIndicator, TireDiagram  # noqa: F401
from data import DummyDataSource

import theme


class HiluxApp(MDApp):
    night_mode = BooleanProperty(False)

    # Couleurs dérivées du thème, consommées par les widgets canvas (jauges...)
    c_bg = ListProperty([0, 0, 0, 1])
    c_surface = ListProperty([1, 1, 1, 1])
    c_text = ListProperty([0, 0, 0, 1])
    c_text_dim = ListProperty([0.4, 0.4, 0.4, 1])
    c_accent = ListProperty([0.13, 0.45, 0.85, 1])
    c_ok = ListProperty([0.16, 0.65, 0.34, 1])
    c_warn = ListProperty([0.90, 0.60, 0.10, 1])
    c_alarm = ListProperty([0.85, 0.20, 0.20, 1])

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

        root = Factory.Root()
        self.apply_theme()
        self._dialog = None
        Clock.schedule_interval(self._tick, 1 / 5.0)   # 5 Hz
        return root

    # ---------------- thème ----------------
    def apply_theme(self):
        p = theme.palette(self.night_mode)
        self.c_bg = list(p["bg"])
        self.c_surface = list(p["surface"])
        self.c_text = list(p["text"])
        self.c_text_dim = list(p["text_dim"])
        self.c_accent = list(p["accent"])
        self.c_ok = list(p["ok"])
        self.c_warn = list(p["warn"])
        self.c_alarm = list(p["alarm"])

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
            "g_oil": "oil_temp", "g_coolant": "coolant_temp", "g_boost": "boost",
            "g_favg": "fuel_avg", "g_finst": "fuel_inst", "g_ext": "ext_temp",
        }
        for wid, key in gauges.items():
            if wid in ids:
                ids[wid].value = v[key]
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
    Builder.load_file(os.path.join(os.path.dirname(__file__), "hilux.kv"))
    HiluxApp().run()
