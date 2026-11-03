"""Sound: music and effects (block break, bomb explosion, death).

Sounds are loaded from FILES in client/sounds/ (.mp3, .ogg or .wav):
    music.mp3                - background music (loops)
    break.mp3                - any block breaking
    break_dirt.mp3, break_stone.mp3, break_slate.mp3, break_gold.mp3, break_brambles.mp3
                             - (optional) a sound for one specific block, replaces break.mp3
    explosion.mp3            - a bomb going off
    death.mp3                - the player dying
    death_wall.mp3, death_lava.mp3, death_bomb.mp3 - (optional) a sound for one specific death
A name can have several variants (break1.mp3, break2.mp3 ...): one is picked at random.

If the folder contains NO sound file at all, built-in synthesized sounds are used so the game is not silent.
If it contains at least one file, synthesized sounds are never used: whatever has no file stays silent.
Without an audio device everything silently does nothing and the game keeps running.
"""
import array
import math
import os
import random
import sys
import threading
import time

import pygame

MUSIC_VOLUME = 0.30
SFX_VOLUME = 0.55
MIN_GAP_MS = 45                 # minimum gap between two plays of the same sound
EXTS = ("mp3", "ogg", "wav")
BLOCK_NAMES = {1: "dirt", 2: "stone", 3: "slate", 4: "gold", 6: "brambles"}
DEATH_CAUSES = ("wall", "lava", "bomb")

# block kind -> (tone frequency, duration s, noise share, noise filter)
BREAK_SPECS = {
    1: (110, 0.10, 0.55, 0.35),     # dirt: dull
    2: (190, 0.12, 0.60, 0.55),     # stone: drier
    3: (80, 0.18, 0.50, 0.25),      # slate: heavy
    6: (0, 0.10, 1.00, 0.75),       # brambles: rustle
}

BPM = 132
# (bass note, chord tones) - Am F C G Am F G E
CHORDS = [(45, [57, 60, 64, 69]), (41, [53, 57, 60, 65]), (48, [55, 60, 64, 67]),
          (43, [55, 59, 62, 67]), (45, [57, 60, 64, 69]), (41, [53, 57, 60, 65]),
          (43, [55, 59, 62, 67]), (40, [52, 56, 59, 64])]
PATTERNS = ([0, 1, 2, 3, 2, 1, 2, 1], [3, 2, 1, 0, 1, 2, 3, 2])


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


class Audio:
    def __init__(self, base_dir):
        self.ok = False
        self.muted = False
        self.want_music = False
        self._music_playing = False
        self._music_sound = None
        self._music_file = None
        self.sounds = {}
        self._last = {}
        self.rate, self.channels = 44100, 2
        self.channel = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 2, 512)
            freq, size, chans = pygame.mixer.get_init()
            if size != -16:
                return                      # unsupported format: stay silent
            self.rate, self.channels = freq, chans
            pygame.mixer.set_reserved(1)    # channel 0 is reserved for music
            self.channel = pygame.mixer.Channel(0)
            self.ok = True
        except pygame.error:
            return

        self.dir = os.path.join(base_dir, "sounds")
        # synthesized sounds are used only if the folder has no sound file at all
        self.use_synth = not self._has_audio_files()
        self._load_effects()
        music = self._files("music")
        self._music_file = music[0] if music else None
        if self._music_file is None and self.use_synth:
            threading.Thread(target=self._build_music, daemon=True).start()
        self._report()

    # ------------------------------------------------------------ public
    def play_music(self):
        self.want_music = True

    def fade_music(self, ms=700):
        self.want_music = False
        if self.ok and self._music_playing:
            self._music_playing = False
            if self._music_file:
                pygame.mixer.music.fadeout(ms)
            else:
                self.channel.fadeout(ms)

    def toggle_mute(self):
        self.muted = not self.muted
        self._apply_volume()

    def update(self):
        """Call every frame: starts the music once it is ready."""
        if not self.ok or not self.want_music or self._music_playing:
            return
        if self._music_file:
            try:
                pygame.mixer.music.load(self._music_file)
                pygame.mixer.music.play(-1)
            except pygame.error as e:
                self._warn(self._music_file, e)
                self._music_file = None
                if self.use_synth:
                    threading.Thread(target=self._build_music, daemon=True).start()
                return
        elif self._music_sound is not None:
            self.channel.play(self._music_sound, loops=-1)
        else:
            return                          # still being synthesized
        self._music_playing = True
        self._apply_volume()

    def handle(self, events):
        """Handles game events: ("break", kind, tile), ("explode", tile), ("death", cause)."""
        if not self.ok:
            return
        for ev in events:
            name, arg = ev[0], ev[1]
            if name == "break":
                self._play(("break", arg))
            elif name == "explode":
                self._play(("explode", None), gap=0)
            elif name == "death":
                self.fade_music()
                self._play(("death", arg), gap=0)

    # ------------------------------------------------------------ internals
    def _apply_volume(self):
        if not self.ok:
            return
        vol = 0.0 if self.muted else MUSIC_VOLUME
        self.channel.set_volume(vol)
        pygame.mixer.music.set_volume(vol)

    def _play(self, key, gap=MIN_GAP_MS):
        variants = self.sounds.get(key)
        if self.muted or not variants:
            return
        now = pygame.time.get_ticks()
        if now - self._last.get(key, -10_000) < gap:
            return
        self._last[key] = now
        random.choice(variants).play()

    def _make_sound(self, samples, volume=SFX_VOLUME):
        data = array.array("h")
        for x in samples:
            v = int(max(-1.0, min(1.0, x)) * 32767)
            data.append(v)
            if self.channels == 2:
                data.append(v)
        snd = pygame.mixer.Sound(buffer=data.tobytes())
        snd.set_volume(volume)
        return snd

    def _has_audio_files(self):
        try:
            return any(f.lower().endswith(EXTS) for f in os.listdir(self.dir))
        except OSError:
            return False

    def _files(self, base):
        """All files named `base`, `base1`..`base9` (mp3/ogg/wav)."""
        found = []
        for name in [base] + [f"{base}{i}" for i in range(1, 10)]:
            for ext in EXTS:
                path = os.path.join(self.dir, f"{name}.{ext}")
                if os.path.exists(path):
                    found.append(path)
                    break
        return found

    def _warn(self, path, err):
        print(f"[sound] Could not load {os.path.basename(path)}: {err}", file=sys.stderr)

    def _load_sounds(self, paths):
        sounds = []
        for path in paths:
            try:
                snd = pygame.mixer.Sound(path)
                snd.set_volume(SFX_VOLUME)
                sounds.append(snd)
            except pygame.error as e:
                self._warn(path, e)
        return sounds

    def _load_effects(self):
        rng = random.Random(7)
        generic = self._load_sounds(self._files("break"))
        for kind, name in BLOCK_NAMES.items():
            snds = self._load_sounds(self._files(f"break_{name}")) or generic
            if not snds and self.use_synth:
                snds = [self._make_sound(self._synth_break(kind, rng)) for _ in range(3)]
            if snds:
                self.sounds[("break", kind)] = snds
        snds = self._load_sounds(self._files("explosion"))
        if not snds and self.use_synth:
            snds = [self._make_sound(self._synth_explosion(rng))]
        if snds:
            self.sounds[("explode", None)] = snds
        generic = self._load_sounds(self._files("death"))
        for cause in DEATH_CAUSES:
            snds = self._load_sounds(self._files(f"death_{cause}")) or generic
            if not snds and self.use_synth:
                snds = [self._make_sound(self._synth_death(cause, rng))]
            if snds:
                self.sounds[("death", cause)] = snds

    def _report(self):
        if self.use_synth:
            print("[sound] No files in client/sounds: using built-in synthesized sounds.")
            return
        music = os.path.basename(self._music_file) if self._music_file else "none"
        print(f"[sound] music: {music}; "
              f"block sounds: {'yes' if ('break', 1) in self.sounds else 'no'}; "
              f"explosion: {'yes' if ('explode', None) in self.sounds else 'no'}; "
              f"death sound: {'yes' if ('death', 'wall') in self.sounds else 'no'}")

    # ------------------------------------------------------------ synthesis
    def _noise(self, n, rng, a):
        """Low-pass filtered noise (small `a` = duller), normalised to about +-1."""
        scale = 1.0 / (math.sqrt(a / (2 - a)) * 0.577)
        y, out = 0.0, []
        for _ in range(n):
            y += a * (rng.uniform(-1, 1) - y)
            out.append(y * scale)
        return out

    @staticmethod
    def _normalize(samples, peak=0.9):
        top = max(abs(x) for x in samples) or 1.0
        return [x * peak / top for x in samples]

    def _synth_break(self, kind, rng):
        r = self.rate
        jitter = rng.uniform(0.9, 1.1)
        if kind == 4:                                   # gold: a little bell
            n = int(0.28 * r)
            tick = self._noise(600, rng, 0.8)
            out = []
            for i in range(n):
                t = i / r
                env = (1 - i / n) ** 1.6
                s = env * (0.55 * math.sin(2 * math.pi * 880 * jitter * t)
                           + 0.35 * math.sin(2 * math.pi * 1320 * jitter * t)
                           + 0.15 * math.sin(2 * math.pi * 1760 * jitter * t))
                if i < 600:
                    s += 0.3 * tick[i] * (1 - i / 600)
                out.append(s)
            return self._normalize(out)
        freq, dur, namt, a = BREAK_SPECS[kind]
        n = int(dur * r)
        noise = self._noise(n, rng, a)
        out = []
        for i in range(n):
            env = (1 - i / n) ** 2
            tone = math.sin(2 * math.pi * freq * jitter * (i / r) * (1 - 0.35 * i / n)) if freq else 0.0
            out.append(env * (tone * (1 - namt) + noise[i] * namt * 0.8))
        return self._normalize(out)

    def _synth_explosion(self, rng):
        """A bomb: low rumble, a falling thump and a burst of noise."""
        r = self.rate
        n = int(0.9 * r)
        rumble = self._noise(n, rng, 0.10)
        crack = self._noise(n, rng, 0.7)
        phase, out = 0.0, []
        for i in range(n):
            p = i / n
            phase += 2 * math.pi * (110 * (1 - p) + 28 * p) / r
            out.append((1 - p) ** 1.4 * (0.9 * rumble[i] + 0.8 * math.sin(phase))
                       + 0.7 * crack[i] * (1 - p) ** 6)
        return self._normalize(out)

    def _synth_death(self, cause, rng):
        r = self.rate
        lava = cause == "lava"
        n = int((1.2 if lava else 1.0) * r)
        f0, f1 = (520, 40) if lava else (330, 60)
        rumble = self._noise(n, rng, 0.05)
        hiss = self._noise(n, rng, 0.8) if lava else None
        phase, out = 0.0, []
        for i in range(n):
            p = i / n
            phase += 2 * math.pi * (f0 * (1 - p) + f1 * p) / r
            sq = 1.0 if math.sin(phase) > 0 else -1.0
            env = (1 - p) ** 1.2
            s = env * (0.30 * sq + 0.25 * math.sin(phase * 0.5) + 0.35 * rumble[i])
            if hiss:
                s += 0.25 * hiss[i] * (1 - p) ** 0.8
            out.append(s)
        return self._normalize(out)

    def _build_music(self):
        """Synthesizes a ~14 s looping chiptune tune (in the background, so startup is not delayed)."""
        try:
            r = self.rate
            beat = 60.0 / BPM
            eighth = int(beat / 2 * r)
            bar = eighth * 8
            buf = [0.0] * (bar * len(CHORDS))
            rng = random.Random(11)

            def add(start, samples):
                for k, v in enumerate(samples):
                    buf[start + k] += v

            for b, (bass, tones) in enumerate(CHORDS):
                base = b * bar
                pattern = PATTERNS[b % 2]
                for e in range(8):                      # melody: eighth-note arpeggio
                    f = hz(tones[pattern[e]] + 12)
                    n = int(eighth * 0.95)
                    note = []
                    for i in range(n):
                        sq = 1.0 if (i * f / r) % 1.0 < 0.5 else -1.0
                        env = min(1.0, i / 60) * (1 - 0.7 * i / n)
                        note.append(0.15 * sq * env)
                    add(base + e * eighth, note)
                for q in range(4):                      # bass: root / octave
                    f = hz(bass + (12 if q % 2 else 0))
                    n = eighth * 2
                    note = []
                    for i in range(n):
                        tri = 2 / math.pi * math.asin(math.sin(2 * math.pi * f * i / r))
                        note.append(0.30 * tri * (1 - 0.5 * i / n))
                    add(base + q * 2 * eighth, note)
                    if q % 2 == 0:                      # kick drum
                        kn = int(0.12 * r)
                        add(base + q * 2 * eighth,
                            [0.35 * math.sin(2 * math.pi * (120 - 70 * i / kn) * i / r) * (1 - i / kn) ** 2
                             for i in range(kn)])
                for e in (1, 3, 5, 7):                  # hi-hat
                    hn = int(0.03 * r)
                    nz = [rng.uniform(-1, 1) for _ in range(hn + 1)]
                    add(base + e * eighth,
                        [0.07 * (nz[i] - nz[i + 1]) * (1 - i / hn) for i in range(hn)])
                time.sleep(0.002)                       # give the main thread some time
            peak = max(abs(x) for x in buf) or 1.0
            self._music_sound = self._make_sound([x * 0.85 / peak for x in buf], volume=1.0)
        except Exception:
            self._music_sound = None
