"""
Widgets personnalisés dessinés au canvas (légers pour le Pi 3) :
- VBarGauge      : jauge verticale segmentée (huile, niveau carburant — écran 1 ;
                   tangage, en colonnes miroir — écran 2)
- HBarGauge      : jauge horizontale segmentée (liquide de refroidissement — écran 1)
- HeadingArrow   : flèche de cap fixe (écran 1, écran 2)
- RollFanGauge   : aile en éventail pour le roulis, en miroir gauche/droite (écran 2)
- TireDiagram    : vue de dessus du véhicule + 4 pressions colorées (écran 3)
- TopBar         : barre globale (navigation + nuit / settings / shutdown)
"""
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.properties import (
    NumericProperty, StringProperty, BooleanProperty,
)
from kivy.graphics import (
    Color, Line, Rectangle, RoundedRectangle, Mesh,
    Rotate, PushMatrix, PopMatrix,
)
from kivy.metrics import dp
from kivy.app import App
from math import cos, pi


# --------------------------------------------------------------------------- #
#  Jauges segmentées (barre verticale / horizontale)
# --------------------------------------------------------------------------- #
class _SegmentedBarGauge(Widget):
    """Base commune : fraction remplie colorée selon la sévérité, le reste en gris."""
    value = NumericProperty(0.0)
    vmin = NumericProperty(0.0)
    vmax = NumericProperty(100.0)
    warn = NumericProperty(1e9)
    alarm = NumericProperty(1e9)
    invert = BooleanProperty(False)   # True : danger quand value est BAS (ex. carburant)
    segments = NumericProperty(11)

    def __init__(self, **kw):
        super().__init__(**kw)
        for p in ("pos", "size", "value"):
            self.bind(**{p: self._redraw})

    def _fraction(self):
        if self.vmax <= self.vmin:
            return 0.0
        return max(0.0, min(1.0, (self.value - self.vmin) / (self.vmax - self.vmin)))

    def _fill_color(self):
        app = App.get_running_app()
        v = self.value
        bad = (v <= self.alarm) if self.invert else (v >= self.alarm)
        mid = (v <= self.warn) if self.invert else (v >= self.warn)
        if bad:
            return app.c_alarm
        if mid:
            return app.c_warn
        return app.c_text


class VBarGauge(_SegmentedBarGauge):
    """Remplissage du bas vers le haut."""
    framed = BooleanProperty(False)  # cadre 2 lignes verticales (écran tilt)

    def _redraw(self, *_):
        self.canvas.clear()
        app = App.get_running_app()
        frac = self._fraction()
        fill = self._fill_color()
        n = int(self.segments)
        gap = self.height / n
        seg_h = gap * 0.2
        with self.canvas:
            for i in range(n):
                y = self.y + i * gap + (gap - seg_h) / 2
                Color(*(fill if (i + 0.5) / n <= frac else app.c_text_dim))
                RoundedRectangle(pos=(self.x, y), size=(self.width, seg_h),
                                  radius=[seg_h / 2])
            if self.framed:
                Color(*app.c_text_dim)
                Line(points=[self.x, self.y, self.x, self.top], width=dp(1))
                Line(points=[self.right, self.y, self.right, self.top], width=dp(1))


class HBarGauge(_SegmentedBarGauge):
    """Piste pleine (style progress bar) : la portion remplie est dessinée
    par-dessus la piste grise, sans espace entre les deux."""

    def _redraw(self, *_):
        self.canvas.clear()
        app = App.get_running_app()
        frac = self._fraction()
        fill = self._fill_color()
        r = self.height / 2
        fill_w = self.width * frac
        with self.canvas:
            Color(*app.c_text_dim)
            RoundedRectangle(pos=(self.x, self.y), size=(self.width, self.height),
                              radius=[r])
            if fill_w > 0:
                Color(*fill)
                RoundedRectangle(pos=(self.x, self.y), size=(fill_w, self.height),
                                  radius=[r])


# --------------------------------------------------------------------------- #
#  Flèche de cap (décorative, fixe)
# --------------------------------------------------------------------------- #
class HeadingArrow(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_):
        self.canvas.clear()
        app = App.get_running_app()
        # NB: on calcule le centre à partir de x/y/width/height plutôt que de
        # center_x/center_y — cette AliasProperty peut renvoyer une valeur
        # encore en cache au moment où ce callback (lié à pos/size) s'exécute.
        hw, hh = self.width * 0.5, self.height * 0.5
        cx, cy = self.x + hw, self.y + hh
        with self.canvas:
            Color(*app.c_alarm)
            Mesh(
                vertices=[cx, cy + hh, 0, 0,
                          cx - hw, cy - hh, 0, 0,
                          cx + hw, cy - hh, 0, 0],
                indices=[0, 1, 2],
                mode="triangles",
            )


# --------------------------------------------------------------------------- #
#  Jauge en éventail (roulis, ailes miroir)
# --------------------------------------------------------------------------- #
class RollFanGauge(Widget):
    """Une aile de jauge papillon : barres segmentées radiant depuis une
    ligne verticale de référence (0°) jusqu'à un arc gradué (+-vmax).
    Deux instances (mirror=False/True) partagent la même valeur `angle`
    pour former l'effet symétrique complet (écran 2)."""
    angle = NumericProperty(0.0)
    mirror = BooleanProperty(False)
    vmax = NumericProperty(45.0)
    warn = NumericProperty(15.0)
    alarm = NumericProperty(25.0)
    rows = NumericProperty(17)

    def __init__(self, **kw):
        super().__init__(**kw)
        for p in ("pos", "size", "angle"):
            self.bind(**{p: self._redraw})

    def _fill_color(self):
        app = App.get_running_app()
        v = abs(self.angle)
        if v >= self.alarm:
            return app.c_alarm
        if v >= self.warn:
            return app.c_warn
        return app.c_ok

    def _is_active(self):
        """mirror=True (roll_fan_r, droite) s'allume quand angle>0 (penche à
        droite) ; mirror=False (roll_fan_l, gauche) quand angle<0 (gauche) —
        convention de signe de `roll` définie dans data.py."""
        if self.angle == 0:
            return False
        return (self.angle > 0) == self.mirror

    def _redraw(self, *_):
        self.canvas.clear()
        app = App.get_running_app()
        n = int(self.rows)
        fill = self._fill_color()
        active = self._is_active()
        anchor_x = self.x if self.mirror else self.x + self.width
        sign = 1 if self.mirror else -1
        thickness = (self.height / (n - 1)) * 0.4
        with self.canvas:
            for i in range(n):
                row_angle = -self.vmax + i * (2 * self.vmax) / (n - 1)
                y = self.y + i * self.height / (n - 1)
                frac = abs(row_angle) / self.vmax
                bar_len = max(self.width * cos(frac * pi / 2), 1)
                lit = active and abs(row_angle) <= abs(self.angle)
                Color(*(fill if lit else app.c_text_dim))
                x_tip = anchor_x + sign * bar_len
                RoundedRectangle(
                    pos=(min(anchor_x, x_tip), y - thickness / 2),
                    size=(bar_len, thickness),
                    radius=[thickness / 2],
                )


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
