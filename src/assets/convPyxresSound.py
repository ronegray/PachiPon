import pyxel
import time

NOTE_NAMES = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]


def note_to_name(n):
    if n < 0:
        return "r"
    return f"{NOTE_NAMES[n % 12]}{n // 12}"


def tone_to_char(t):
    return "tspn"[t] if t < 4 else str(t)


def effect_to_char(e):
    return "nsvfhq"[e] if e < 6 else "n"


# pyxel.init(3, 3)#, headless=True)
# pyxel.load("assets.pyxres")
# time.sleep(3)
# for i, snd in enumerate(pyxel.sounds):
#     notes = "".join(note_to_name(n) for n in snd.notes)
#     tones = "".join(tone_to_char(t) for t in snd.tones)
#     volumes = "".join(str(v) for v in snd.volumes)
#     effects = "".join(effect_to_char(e) for e in snd.effects)
#     print(f'{i}: "{notes}", "{tones}", "{volumes}", "{effects}", {snd.speed}')
#     pyxel.play(0, snd)
#     while pyxel.channels[0].play_pos() is not None:
#         pass
#     time.sleep(0.5)
class App:
    def __init__(self):
        pyxel.init(256, 128)
        pyxel.load("assets.pyxres")
        self.snd_idx: int = 0
        self.is_start: bool = False
        self._snd = None

        pyxel.run(self.update, self.draw)

    def update(self):
        if not self.is_start:
            if pyxel.btnp(pyxel.KEY_RETURN):
                self.is_start = True
            return

        time.sleep(0.5)
        if pyxel.channels[0].play_pos() is None:
            self._snd = pyxel.sounds[self.snd_idx]
            pyxel.play(0, self._snd)
            self.snd_idx += 1

    def draw(self):
        pyxel.cls(0)
        if self._snd is not None:
            pyxel.text(
                0,
                0,
                f"notes={self._snd.notes}\ntones={self._snd.tones}\nvolumes={self._snd.volumes}\neffects={self._snd.effects}\nspeed={self._snd.speed}",
                pyxel.COLOR_WHITE,
            )


App()
