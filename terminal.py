"""
Terminal shell interactif embarqué dans l'écran réglages.

Un vrai bash tourne dans un pty (mêmes droits que l'appli — pas de
sandbox, pas de confirmation par commande). On reste volontairement en
flux texte ligne à ligne, sans émulation VT100 complète : les
applications plein écran (top, vim, less...) ne s'affichent pas
correctement, mais les commandes de debug usuelles (systemctl,
journalctl, ping, df...) fonctionnent normalement.
"""
import os
import pty
import re
import select
import signal
import threading
from queue import Empty, Queue

from kivy.clock import Clock
from kivy.properties import StringProperty
from kivymd.uix.boxlayout import MDBoxLayout

# Séquences d'échappement ANSI (couleurs, déplacement curseur...) et
# caractères de contrôle : on les retire, faute d'émulation de terminal,
# pour ne pas afficher de bruit illisible dans le flux texte.
_ANSI_RE = re.compile(
    r"\x1b\[[0-9;?]*[a-zA-Z]"
    r"|\x1b\][^\x07]*(\x07|\x1b\\)"
    r"|[\x00-\x08\x0b\x0c\x0e-\x1f]"
)
_MAX_BUFFER = 20000  # caractères conservés dans le tampon affiché

_consoles = []  # instances actives, pour tout arrêter à la fermeture de l'appli


class TerminalConsole(MDBoxLayout):
    """Bash interactif : un fork/pty par instance, sortie diffusée en continu."""

    output_text = StringProperty("bash prêt — tapez une commande ci-dessous\n")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._out_queue = Queue()
        self._pid = None
        self._master_fd = None
        self._stop_flag = threading.Event()
        self._spawn_shell()
        _consoles.append(self)
        Clock.schedule_interval(self._drain_queue, 1 / 10.0)

    def _spawn_shell(self):
        env = dict(os.environ)
        env["TERM"] = "dumb"  # limite les codes couleur/curseur émis par le shell
        pid, fd = pty.fork()
        if pid == 0:
            try:
                os.execvpe("bash", ["bash"], env)
            except FileNotFoundError:
                os.execvpe("sh", ["sh"], env)
            os._exit(1)  # pragma: no cover - uniquement si exec échoue
        self._pid = pid
        self._master_fd = fd
        threading.Thread(target=self._read_loop, daemon=True).start()

    def _read_loop(self):
        fd = self._master_fd
        while not self._stop_flag.is_set():
            try:
                ready, _, _ = select.select([fd], [], [], 0.2)
            except (OSError, ValueError):
                break
            if fd in ready:
                try:
                    data = os.read(fd, 4096)
                except OSError:
                    break
                if not data:
                    break
                self._out_queue.put(data.decode("utf-8", errors="replace"))
        self._out_queue.put("\n[session terminée]\n")

    def _drain_queue(self, dt):
        parts = []
        while True:
            try:
                parts.append(self._out_queue.get_nowait())
            except Empty:
                break
        if not parts:
            return
        text = _ANSI_RE.sub("", "".join(parts))
        self.output_text = (self.output_text + text)[-_MAX_BUFFER:]
        Clock.schedule_once(self._scroll_to_bottom)

    def _scroll_to_bottom(self, dt):
        if "scroll" in self.ids:
            self.ids.scroll.scroll_y = 0

    def send_line(self, text):
        if self._master_fd is None:
            return
        try:
            os.write(self._master_fd, (text + "\n").encode())
        except OSError:
            pass

    def send_interrupt(self):
        if self._master_fd is None:
            return
        try:
            os.write(self._master_fd, b"\x03")  # Ctrl+C
        except OSError:
            pass

    def clear_output(self):
        self.output_text = ""

    def stop(self):
        self._stop_flag.set()
        if self._pid is not None:
            try:
                os.killpg(os.getpgid(self._pid), signal.SIGTERM)
            except OSError:
                pass


def stop_all():
    """Termine tous les shells actifs (appelé à la fermeture de l'appli)."""
    for console in _consoles:
        console.stop()
