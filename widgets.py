"""
Widgets personnalisés dessinés au canvas (légers pour le Pi 3) :
- Gauge          : jauge circulaire à arc + valeur numérique (écran 1)
- TiltIndicator  : silhouette qui s'incline selon roll/pitch (écran 2)
- TireDiagram    : vue de dessus du véhicule + 4 pressions colorées (écran 3)
- TopBar         : barre globale (navigation + nuit / settings / shutdown)
"""
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.properties import (
    NumericProperty, StringProperty, ListProperty, BoundedNumericProperty,
)
from kivy.graphics import Color, Line, Ellipse, Rectangle, Rotate, PushMatrix, PopMatrix
from kivy.metrics import dp
from kivy.app import App
import math


# --------------------------------------------------------------------------- #
#  Jauge circulaire
# --------------------------------------------------------------------------- #
class Gauge(Widget):
    title = StringProperty("")
    unit = StringProperty("")
    value = NumericProperty(0.0)
    vmin = NumericProperty(0.0)
    vmax = NumericProperty(100.0)
    warn = NumericProperty(1e9)   # seuil alerte modérée
    alarm = NumericProperty(1e9)  # seuil alerte grave

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._redraw, size=self._redraw, value=self._redraw)

    def _color_for_value(self):
        app = App.get_running_app()
        if self.value >= self.alarm:
            return app.c_alarm
        if self.value >= self.warn:
            return app.c_warn
        return app.c_accent

    def _redraw(self, *_):
        self.canvas.clear()
        app = App.get_running_app()
        cx, cy = self.center_x, self.center_y
        r = min(self.width, self.height) * 0.40
        start, end = 135, -135          # arc de 270°
        span = start - end
        frac = 0.0
        if self.vmax > self.vmin:
            frac = max(0.0, min(1.0, (self.value - self.vmin) / (self.vmax - self.vmin)))
        with self.canvas:
            # piste de fond
            Color(*app.c_text_dim)
            Line(circle=(cx, cy, r, end, start), width=dp(6))
            # arc de valeur
            Color(*self._color_for_value())
            Line(circle=(cx, cy, r, start - span * frac, start), width=dp(6))

    def refresh(self):
        self._redraw()


# --------------------------------------------------------------------------- #
#  Indicateur d'inclinaison
# --------------------------------------------------------------------------- #
class TiltIndicator(Widget):
    """Affiche roll (latéral) ou pitch (longitudinal) via une silhouette."""
    angle = NumericProperty(0.0)     # degrés
    axis = StringProperty("roll")    # "roll" ou "pitch"

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._redraw, size=self._redraw, angle=self._redraw)

    def _redraw(self, *_):
        self.canvas.clear()
        app = App.get_running_app()
        cx, cy = self.center_x, self.center_y
        half = min(self.width, self.height) * 0.32
        with self.canvas:
            PushMatrix()
            Rotate(angle=-self.angle, origin=(cx, cy))
            # ligne d'horizon
            col = app.c_alarm if abs(self.angle) > 25 else (
                app.c_warn if abs(self.angle) > 15 else app.c_ok)
            Color(*col)
            Line(points=[cx - half, cy, cx + half, cy], width=dp(3))
            # marqueur de "toit" du véhicule
            Line(points=[cx, cy, cx, cy + half * 0.5], width=dp(3))
            PopMatrix()
            # repère fixe central
            Color(*app.c_text_dim)
            Line(circle=(cx, cy, dp(4)), width=dp(2))


# --------------------------------------------------------------------------- #
#  Schéma des 4 pneus
# --------------------------------------------------------------------------- #
class TireDiagram(Widget):
    fl = NumericProperty(0.0)
    fr = NumericProperty(0.0)
    rl = NumericProperty(0.0)
    rr = NumericProperty(0.0)
    target = NumericProperty(2.5)    # pression cible (bar)
    tol = NumericProperty(0.3)       # tolérance avant alerte

    def __init__(self, **kw):
        super().__init__(**kw)
        for p in ("pos", "size", "fl", "fr", "rl", "rr"):
            self.bind(**{p: self._redraw})

    def _tire_color(self, val):
        app = App.get_running_app()
        d = abs(val - self.target)
        if d > self.tol * 2:
            return app.c_alarm
        if d > self.tol:
            return app.c_warn
        return app.c_ok

    def _redraw(self, *_):
        self.canvas.clear()
        app = App.get_running_app()
        cx, cy = self.center_x, self.center_y
        bw = min(self.width, self.height) * 0.28   # demi largeur châssis
        bh = min(self.width, self.height) * 0.42   # demi hauteur châssis
        tw, th = dp(26), dp(46)                    # taille d'un pneu
        corners = {
            "fl": (cx - bw, cy + bh), "fr": (cx + bw, cy + bh),
            "rl": (cx - bw, cy - bh), "rr": (cx + bw, cy - bh),
        }
        with self.canvas:
            # châssis
            Color(*app.c_text_dim)
            Line(rectangle=(cx - bw, cy - bh, bw * 2, bh * 2), width=dp(2))
            # pneus
            for key, (x, y) in corners.items():
                Color(*self._tire_color(getattr(self, key)))
                Rectangle(pos=(x - tw / 2, y - th / 2), size=(tw, th))


# --------------------------------------------------------------------------- #
#  Barre globale
# --------------------------------------------------------------------------- #
class TopBar(BoxLayout):
    """Barre présente sur tous les écrans : navigation + actions globales."""
    pass
