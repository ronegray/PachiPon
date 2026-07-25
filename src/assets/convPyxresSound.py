import pyxel

NOTE_NAMES = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"]


def note_to_name(n):
    if n < 0:
        return "r"
    return f"{NOTE_NAMES[n % 12]}{n // 12}"


def tone_to_char(t):
    return "tspn"[t] if t < 4 else str(t)


def effect_to_char(e):
    return "nsvfhq"[e] if e < 6 else "n"


pyxel.init(0, 0, headless=True)
pyxel.load("assets.pyxres")

for i, snd in enumerate(pyxel.sounds):
    notes = "".join(note_to_name(n) for n in snd.notes)
    tones = "".join(tone_to_char(t) for t in snd.tones)
    volumes = "".join(str(v) for v in snd.volumes)
    effects = "".join(effect_to_char(e) for e in snd.effects)
    print(f'{i}: "{notes}", "{tones}", "{volumes}", "{effects}", {snd.speed}')
