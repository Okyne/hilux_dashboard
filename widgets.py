"""
Widgets personnalisés dessinés au canvas (légers pour le Pi 3) :
- VBarGauge      : jauge verticale segmentée (huile, niveau carburant — écran 1)
- HBarGauge      : jauge horizontale segmentée (liquide de refroidissement — écran 1)
- HeadingArrow   : flèche de cap fixe (écran 1, écran 2)
- TiltIndicator  : silhouette qui s'incline selon roll/pitch (écran 2)
- TireDiagram    : vue de dessus du véhicule + 4 pressions colorées (écran 3)
- TopBar         : barre globale (navigation + nuit / settings / shutdown)
"""
import math

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
from kivy.core.window import Window


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
#  Indicateur d'inclinaison (cadran façon clinomètre)
# --------------------------------------------------------------------------- #
class TiltIndicator(Widget):
    """Cadran circulaire roll (latéral) ou pitch (longitudinal) : anneau
    bicolore haut/bas gradué de 0 (horizontale) à `vmax` (verticale), et une
    aiguille traversante qui tourne avec l'angle. L'échelle est volontairement
    étirée (0..vmax mappé sur 0..90° de rotation) plutôt que 1:1, pour rester
    lisible aux petits angles réellement rencontrés en conduite."""
    angle = NumericProperty(0.0)     # degrés, valeur brute du capteur
    axis = StringProperty("roll")    # "roll" ou "pitch"
    vmax = NumericProperty(40.0)     # valeur au bord du cadran (haut/bas)
    warn = NumericProperty(15.0)
    alarm = NumericProperty(25.0)
    ticks = NumericProperty(4)       # graduations par quart de cadran (hors 0)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._redraw, size=self._redraw, angle=self._redraw)

    def _needle_color(self):
        app = App.get_running_app()
        a = abs(self.angle)
        if a > self.alarm:
            return app.c_alarm
        if a > self.warn:
            return app.c_warn
        return app.c_ok

    def _redraw(self, *_):
        self.canvas.clear()
        app = App.get_running_app()
        cx, cy = self.center_x, self.center_y
        r = min(self.width, self.height) * 0.46
        with self.canvas:
            # anneau : moitié haute (montée / roulis droit) et basse (descente
            # / roulis gauche) dans deux teintes distinctes. Line(circle=...)
            # balaie les angles dans le sens horaire depuis l'est : 0-180 est
            # donc la moitié BASSE et 180-360 la moitié HAUTE.
            Color(*app.c_accent)
            Line(circle=(cx, cy, r, 0, 180), width=dp(3))
            Color(*app.c_warn)
            Line(circle=(cx, cy, r, 180, 360), width=dp(3))

            # graduations réparties tous les 90/ticks degrés autour du cadran
            n = max(1, int(self.ticks))
            tick_len = r * 0.12
            for i in range(4 * n):
                theta = math.radians(i * (90.0 / n))
                col = app.c_warn if math.sin(theta) >= 0 else app.c_accent
                Color(*col)
                x0, y0 = cx + r * math.cos(theta), cy + r * math.sin(theta)
                x1 = cx + (r - tick_len) * math.cos(theta)
                y1 = cy + (r - tick_len) * math.sin(theta)
                Line(points=[x0, y0, x1, y1], width=dp(1.5))

            # ligne de référence horizontale (0)
            Color(*app.c_text_dim)
            Line(points=[cx - r, cy, cx + r, cy], width=dp(1))

            # aiguille traversante : échelle étirée 0..vmax -> 0..90°
            # (signe inversé : un roulis/tangage positif doit faire tourner
            # l'aiguille visuellement dans le même sens que l'horizon réel)
            span = -90.0 * max(-self.vmax, min(self.vmax, self.angle)) / self.vmax
            Color(*self._needle_color())
            PushMatrix()
            Rotate(angle=span, origin=(cx, cy))
            Line(points=[cx - r * 0.92, cy, cx + r * 0.92, cy], width=dp(3))
            PopMatrix()


# --------------------------------------------------------------------------- #
#  Schéma des 4 pneus
# --------------------------------------------------------------------------- #
class TireDiagram(Widget):
    fl = NumericProperty(0.0)
    fr = NumericProperty(0.0)
    rl = NumericProperty(0.0)
    rr = NumericProperty(0.0)
    # températures (°C) : pas de rôle dans le dessin, juste portées ici pour
    # que hilux.kv puisse les référencer via `tires.fl_t` etc. à côté des
    # pressions sans ids de label supplémentaires.
    fl_t = NumericProperty(0.0)
    fr_t = NumericProperty(0.0)
    rl_t = NumericProperty(0.0)
    rr_t = NumericProperty(0.0)
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
#  Jauge de pression pneu (icône en éventail, écran 3)
# --------------------------------------------------------------------------- #
class TireFanGauge(Widget):
    """4 barres horizontales décroissantes ; le nombre de barres allumées
    suit la pression dans [vmin, vmax], leur couleur suit l'écart à la
    pression cible (même logique de sévérité que TireDiagram)."""
    value = NumericProperty(0.0)
    vmin = NumericProperty(1.5)
    vmax = NumericProperty(3.5)
    target = NumericProperty(2.5)
    tol = NumericProperty(0.3)
    segments = NumericProperty(4)
    # largeur de chaque barre (de la plus haute à la plus basse), en
    # fraction de la largeur du widget
    bar_widths = (1.0, 0.75, 0.5, 0.25)

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
        d = abs(self.value - self.target)
        if d > self.tol * 2:
            return app.c_alarm
        if d > self.tol:
            return app.c_warn
        return app.c_ok

    def _redraw(self, *_):
        self.canvas.clear()
        app = App.get_running_app()
        n = int(self.segments)
        frac = self._fraction()
        fill = self._fill_color()
        gap = self.height / n
        bar_h = gap * 0.45
        with self.canvas:
            for i in range(n):
                y = self.y + self.height - (i + 1) * gap + (gap - bar_h) / 2
                w = self.width * self.bar_widths[min(i, len(self.bar_widths) - 1)]
                x = self.x + (self.width - w) / 2
                # bas = pression faible, haut = pression forte : la barre du
                # bas (i le plus grand) s'allume la première quand frac augmente.
                lit = (n - 1 - i + 0.5) / n <= frac
                Color(*(fill if lit else app.c_text_dim))
                RoundedRectangle(pos=(x, y), size=(w, bar_h), radius=[bar_h / 2])


# --------------------------------------------------------------------------- #
#  Barre globale
# --------------------------------------------------------------------------- #
class TopBar(BoxLayout):
    """Barre présente sur tous les écrans : navigation + actions globales."""
    pass


# --------------------------------------------------------------------------- #
#  Extinction d'écran logicielle (pas d'arrêt de l'appli, juste un cache noir)
# --------------------------------------------------------------------------- #
class ScreenOffOverlay(Widget):
    """Recouvre toute la fenêtre en noir ; un simple tap la retire (réveil)."""

    def __init__(self, **kw):
        super().__init__(**kw)
        self.size = Window.size
        with self.canvas:
            Color(0, 0, 0, 1)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_rect, size=self._sync_rect)
        Window.bind(size=self._on_window_resize)

    def _on_window_resize(self, _window, size):
        self.size = size

    def _sync_rect(self, *_a):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def on_touch_down(self, touch):
        Window.remove_widget(self)
        return True
