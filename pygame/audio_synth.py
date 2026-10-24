"""
audio_synth.py - Procedural Real-Time Audio Synthesizer for Chroma-Strand.
Synthesizes celestial harp plucks, ambient cosmic pads, kinetic slingshot whooshes,
and acoustic resonance shockwaves using NumPy and Pygame mixer.
Zero external audio files required!
"""

import math
import pygame
import numpy as np

SAMPLE_RATE = 44100

class SoundEngine:
    def __init__(self):
        self.enabled = True
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
            pygame.mixer.set_num_channels(32)
            self.music_channel = pygame.mixer.Channel(0)
            self.sfx_channels = [pygame.mixer.Channel(i) for i in range(1, 32)]
            self.sfx_channel_idx = 0
            
            # Synthesize all sound effects into cached pygame Sound objects
            self.sounds = {}
            self._synthesize_all()
            self.ambient_track = self._generate_ambient_loop()
        except Exception as e:
            print(f"[SoundEngine] Audio init error: {e}. Audio disabled.")
            self.enabled = False

    def play_sfx(self, sound_name, volume=1.0):
        if not self.enabled or sound_name not in self.sounds:
            return
        sound = self.sounds[sound_name]
        sound.set_volume(max(0.0, min(1.0, volume)))
        chan = self.sfx_channels[self.sfx_channel_idx]
        self.sfx_channel_idx = (self.sfx_channel_idx + 1) % len(self.sfx_channels)
        chan.play(sound)

    def play_harp_note(self, pitch_index=0, volume=0.8):
        """Play a specific pentatonic pluck note based on string length or index."""
        if not self.enabled:
            return
        idx = max(0, min(len(self.pluck_notes) - 1, int(pitch_index)))
        sound = self.pluck_notes[idx]
        sound.set_volume(max(0.0, min(1.0, volume)))
        chan = self.sfx_channels[self.sfx_channel_idx]
        self.sfx_channel_idx = (self.sfx_channel_idx + 1) % len(self.sfx_channels)
        chan.play(sound)

    def start_music(self):
        if self.enabled and self.ambient_track:
            self.music_channel.play(self.ambient_track, loops=-1)
            self.music_channel.set_volume(0.55)

    def stop_music(self):
        if self.enabled:
            self.music_channel.stop()

    def toggle_mute(self):
        if not self.enabled:
            return False
        if self.music_channel.get_volume() > 0:
            self.music_channel.set_volume(0)
            for c in self.sfx_channels:
                c.set_volume(0)
            return True # muted
        else:
            self.music_channel.set_volume(0.55)
            for c in self.sfx_channels:
                c.set_volume(1.0)
            return False # unmuted

    # --- Waveform Generators ---

    def _to_stereo_sound(self, mono_samples):
        """Converts float numpy array (-1.0 to 1.0) to 16-bit signed stereo Pygame Sound."""
        clamped = np.clip(mono_samples, -1.0, 1.0)
        audio_int16 = (clamped * 32767).astype(np.int16)
        stereo = np.column_stack((audio_int16, audio_int16))
        return pygame.sndarray.make_sound(stereo)

    def _generate_pluck(self, freq, duration=0.8, damping=6.0):
        """Synthesize Karplus-Strong-like celestial pluck with rich harmonics."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        # Fundamental + subtle golden harmonics
        wave = (
            1.00 * np.sin(2 * np.pi * freq * t) +
            0.45 * np.sin(2 * np.pi * freq * 2.0 * t) +
            0.25 * np.sin(2 * np.pi * freq * 3.01 * t) +
            0.12 * np.sin(2 * np.pi * freq * 4.0 * t) +
            0.05 * np.sin(2 * np.pi * freq * 5.02 * t)
        )
        # Exponential decay envelope + rapid initial attack
        attack = np.minimum(t / 0.005, 1.0)
        envelope = attack * np.exp(-t * damping)
        return self._to_stereo_sound(wave * envelope * 0.75)

    def _generate_slingshot_whoosh(self):
        """Pitch-dropping dynamic whoosh with resonance for elastic slingshot."""
        duration = 0.45
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        # Exponential frequency drop from 600Hz down to 110Hz
        freq = 110 + 490 * np.exp(-t * 9.0)
        phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
        noise = (np.random.rand(len(t)) * 2 - 1) * 0.25
        wave = np.sin(phase) + noise
        envelope = np.sin(np.pi * (t / duration) ** 0.5) * np.exp(-t * 3.0)
        return self._to_stereo_sound(wave * envelope * 0.9)

    def _generate_harmonic_shatter(self):
        """Chime shatter sound when void entities combust."""
        duration = 0.5
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        freqs = [880, 1174, 1318, 1760] # A5, D6, E6, A6 chord
        wave = np.zeros_like(t)
        for f in freqs:
            wave += np.sin(2 * np.pi * f * t) * 0.25
        envelope = np.exp(-t * 7.5)
        return self._to_stereo_sound(wave * envelope * 0.8)

    def _generate_shockwave(self):
        """Deep acoustic resonance shockwave (sub-bass punch + low rumble)."""
        duration = 0.6
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        freq = 75 * np.exp(-t * 4.0)
        phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
        sub = np.sin(phase)
        noise = (np.random.rand(len(t)) * 2 - 1) * 0.15
        envelope = np.exp(-t * 5.0)
        return self._to_stereo_sound((sub + noise) * envelope * 0.95)

    def _generate_enclosure_purify(self):
        """Resonant celestial chord when an anchor polygon is closed."""
        duration = 1.1
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        # Lydian celestial chord: C5, E5, F#5, B5
        chord_freqs = [523.25, 659.25, 739.99, 987.77]
        wave = np.zeros_like(t)
        for i, f in enumerate(chord_freqs):
            offset_t = np.maximum(0, t - i * 0.06)
            wave += np.sin(2 * np.pi * f * offset_t) * np.exp(-offset_t * 3.5) * 0.3
        return self._to_stereo_sound(wave * 0.8)

    def _generate_supernova(self):
        """Grand celestial crescendo when Overdrive Supernova triggers."""
        duration = 1.4
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        # Rising glissando
        freq = 150 + 600 * (t / duration) ** 1.8
        phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
        shimmer = np.sin(2 * np.pi * 12 * t) * 0.2
        wave = (np.sin(phase) + shimmer) * np.minimum(t / 0.1, 1.0) * np.exp(-t * 1.5)
        return self._to_stereo_sound(wave * 0.85)

    def _generate_mote_collect(self):
        """High crystalline blip when collecting star motes."""
        duration = 0.12
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
        freq = 1760 + 880 * (t / duration)
        wave = np.sin(2 * np.pi * freq * t) * np.exp(-t * 22)
        return self._to_stereo_sound(wave * 0.5)

    def _generate_ambient_loop(self):
        """Generates an ethereal, seamless 10-second ambient chord progression loop."""
        duration = 10.0
        n_samples = int(SAMPLE_RATE * duration)
        t = np.linspace(0, duration, n_samples, False)
        ambient = np.zeros(n_samples)

        # Chords: Am9 -> Fmaj7#11 -> Cmaj9 -> G6 (Ethereal space progression)
        chords = [
            [220.0, 261.63, 329.63, 493.88], # Am9 (A, C, E, B)
            [174.61, 261.63, 329.63, 369.99], # Fmaj7#11 (F, C, E, F#)
            [261.63, 329.63, 392.00, 493.88], # Cmaj7 (C, E, G, B)
            [196.00, 246.94, 293.66, 392.00]  # G6 (G, B, D, G)
        ]
        segment_len = duration / len(chords)

        for c_idx, chord in enumerate(chords):
            c_start = c_idx * segment_len
            for freq in chord:
                # Pad oscillator with chorus detuning
                osc1 = np.sin(2 * np.pi * freq * t)
                osc2 = np.sin(2 * np.pi * (freq * 1.003) * t + 0.3)
                pad = (osc1 + osc2) * 0.5
                
                # Smooth sinusoidal window for each chord
                window = 0.5 * (1 - np.cos(2 * np.pi * (t - c_start) / (segment_len * 2)))
                # Mask to relevant time slice with crossfade
                mask = np.clip((t - c_start) / (segment_len * 0.2), 0, 1) * \
                       np.clip((c_start + segment_len * 1.2 - t) / (segment_len * 0.2), 0, 1)
                ambient += pad * window * mask * 0.08

        # Subtle sub-bass drone
        sub = np.sin(2 * np.pi * 55 * t) * 0.07 + np.sin(2 * np.pi * 110 * t) * 0.04
        ambient += sub

        # Normalize and loop seamlessly
        fade_samples = int(SAMPLE_RATE * 0.3)
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)
        ambient[:fade_samples] *= fade_in
        ambient[-fade_samples:] *= fade_out

        clamped = np.clip(ambient, -1.0, 1.0)
        audio_int16 = (clamped * 32767).astype(np.int16)
        stereo = np.column_stack((audio_int16, audio_int16))
        return pygame.sndarray.make_sound(stereo)

    def _synthesize_all(self):
        # 1. Harmonic Celestial Pluck Scale (Pentatonic Extended Scale across 2 octaves)
        # Frequencies: A3, C4, D4, E4, G4, A4, C5, D5, E5, G5, A5, C6
        scale_freqs = [
            220.00, 261.63, 293.66, 329.63, 392.00,
            440.00, 523.25, 587.33, 659.25, 783.99,
            880.00, 1046.50
        ]
        self.pluck_notes = [self._generate_pluck(f) for f in scale_freqs]

        # 2. Key Action Sounds
        self.sounds["slingshot"] = self._generate_slingshot_whoosh()
        self.sounds["shatter"] = self._generate_harmonic_shatter()
        self.sounds["shockwave"] = self._generate_shockwave()
        self.sounds["purify"] = self._generate_enclosure_purify()
        self.sounds["supernova"] = self._generate_supernova()
        self.sounds["mote"] = self._generate_mote_collect()
