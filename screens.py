"""
Les 5 écrans de l'application. La logique d'affichage vit surtout dans le
fichier hilux.kv ; on récupère ici les valeurs depuis la source de données
à chaque tick d'horloge et on les pousse dans les widgets.
"""
from kivy.uix.screenmanager import Screen
from kivy.app import App


class BaseScreen(Screen):
    """Chaque écran s'auto-rafraîchit quand il est visible."""

    def on_pre_enter(self, *_):
        self.refresh()

    def refresh(self):
        pass

    @property
    def data(self):
        return App.get_running_app().source.values


class EngineScreen(BaseScreen):
    def refresh(self):
        d = self.data
        ids = self.ids
        mapping = {
            "g_oil": "oil_temp", "g_coolant": "coolant_temp", "g_boost": "boost",
            "g_favg": "fuel_avg", "g_finst": "fuel_inst", "g_ext": "ext_temp",
        }
        for wid, key in mapping.items():
            if wid in ids:
                ids[wid].value = d[key]


class TiltScreen(BaseScreen):
    def refresh(self):
        d = self.data
        if "roll" in self.ids:
            self.ids.roll.angle = d["roll"]
        if "pitch" in self.ids:
            self.ids.pitch.angle = d["pitch"]


class TiresScreen(BaseScreen):
    def refresh(self):
        d = self.data
        if "tires" in self.ids:
            t = self.ids.tires
            t.fl, t.fr, t.rl, t.rr = d["tire_fl"], d["tire_fr"], d["tire_rl"], d["tire_rr"]


class DashcamScreen(BaseScreen):
    """
    Placeholder. Le flux caméra (OpenCV -> Texture) se branche ici, et on
    démarre/arrête la capture dans on_enter/on_leave pour ménager le Pi 3.
    """
    def on_enter(self, *_):
        pass   # TODO: démarrer la capture caméra

    def on_leave(self, *_):
        pass   # TODO: arrêter la capture caméra


class SettingsScreen(BaseScreen):
    pass
