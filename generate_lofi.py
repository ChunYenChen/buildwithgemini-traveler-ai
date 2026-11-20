import numpy as np
import scipy.io.wavfile as wavfile
from scipy.signal import butter, lfilter

sample_rate = 44100
bpm = 80
beat_len = 60.0 / bpm  # 0.75 seconds per beat
bar_len = beat_len * 4  # 3.0 seconds per 4-beat bar
total_duration = 91.5  # duration to cover video
n_samples = int(sample_rate * total_duration)

t_all = np.arange(n_samples) / sample_rate
output = np.zeros(n_samples)

# 1. Warm Lo-Fi Chords Progression (ii7 - V7 - Imaj7 - VI7: Dm7 - G7 - Cmaj7 - Am7)
# Notes in Hz:
# Dm7: D3 (146.83), F3 (174.61), A3 (220.00), C4 (261.63), E4 (329.63)
# G7:  G2 (98.00),  F3 (174.61), B3 (246.94), D4 (293.66)
# Cmaj7: C3 (130.81), E3 (164.81), G3 (196.00), B3 (246.94), D4 (293.66)
# Am7: A2 (110.00), E3 (164.81), G3 (196.00), C4 (261.63)

progression = [
    [146.83, 174.61, 220.00, 261.63, 329.63], # Dm9
    [98.00,  174.61, 246.94, 293.66, 392.00], # G9
    [130.81, 164.81, 196.00, 246.94, 293.66], # Cmaj9
    [110.00, 164.81, 196.00, 261.63, 329.63], # Am9
]

# Generate Electric Piano / Rhodes chord pad
chord_track = np.zeros(n_samples)
bar_count = int(np.ceil(total_duration / bar_len))

for b in range(bar_count):
    chord_notes = progression[b % len(progression)]
    bar_start = int(b * bar_len * sample_rate)
    bar_samples = int(bar_len * sample_rate)
    t_bar = np.arange(bar_samples) / sample_rate

    # Soft tremolo/chorus
    tremolo = 1.0 + 0.15 * np.sin(2 * np.pi * 3.5 * t_bar)
    # Slow gentle decay envelope
    envelope = np.exp(-t_bar / (bar_len * 0.95)) * (1.0 - np.exp(-t_bar * 40))

    chord_wave = np.zeros(bar_samples)
    for freq in chord_notes:
        # Slight detune for warm vintage lo-fi chorus feel
        tone = (
            np.sin(2 * np.pi * freq * t_bar) * 0.5 +
            np.sin(2 * np.pi * (freq * 1.002) * t_bar) * 0.25 +
            np.sin(2 * np.pi * (freq * 0.998) * t_bar) * 0.25 +
            np.sin(2 * np.pi * (freq * 2) * t_bar) * 0.1
        )
        chord_wave += tone

    chord_wave = chord_wave * envelope * tremolo
    end_idx = min(bar_start + bar_samples, n_samples)
    chord_track[bar_start:end_idx] += chord_wave[:end_idx - bar_start]

# 2. Chill Lo-Fi Drum Beat (Kick, Snare/Rimshot, Hi-hat)
drum_track = np.zeros(n_samples)

def make_kick(duration=0.25):
    n = int(duration * sample_rate)
    t = np.arange(n) / sample_rate
    # Pitch drop from 120Hz to 40Hz
    freq = 40 + (120 - 40) * np.exp(-t * 25)
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    env = np.exp(-t * 15)
    return np.sin(phase) * env * 0.8

def make_snare(duration=0.22):
    n = int(duration * sample_rate)
    t = np.arange(n) / sample_rate
    body = np.sin(2 * np.pi * 180 * t) * np.exp(-t * 25) * 0.4
    noise = (np.random.rand(n) * 2 - 1) * np.exp(-t * 18) * 0.35
    return body + noise

def make_hat(duration=0.08):
    n = int(duration * sample_rate)
    t = np.arange(n) / sample_rate
    noise = (np.random.rand(n) * 2 - 1) * np.exp(-t * 45) * 0.15
    return noise

kick = make_kick()
snare = make_snare()
hat = make_hat()

total_beats = int(np.ceil(total_duration / beat_len))
for beat in range(total_beats):
    beat_time = beat * beat_len
    idx = int(beat_time * sample_rate)
    beat_in_bar = beat % 4

    # Kick on beat 1 and beat 2.5 (chill syncopation)
    if beat_in_bar == 0:
        k_end = min(idx + len(kick), n_samples)
        drum_track[idx:k_end] += kick[:k_end - idx]
    elif beat_in_bar == 2:
        # Off-beat kick
        off_idx = idx + int(beat_len * 0.5 * sample_rate)
        k_end = min(off_idx + len(kick), n_samples)
        if off_idx < n_samples:
            drum_track[off_idx:k_end] += kick[:k_end - off_idx] * 0.7

    # Snare on beats 2 and 4
    if beat_in_bar in (1, 3):
        s_end = min(idx + len(snare), n_samples)
        drum_track[idx:s_end] += snare[:s_end - idx]

    # Hi-hat on every 8th note with swing
    h1 = idx
    h2 = idx + int(beat_len * 0.53 * sample_rate)  # slight swing delay
    for h in (h1, h2):
        if h < n_samples:
            h_end = min(h + len(hat), n_samples)
            drum_track[h:h_end] += hat[:h_end - h]

# 3. Lo-Fi Vinyl Crackle & Tape Texture
vinyl = (np.random.rand(n_samples) * 2 - 1) * 0.02
# Occasional clicks
random_clicks = (np.random.rand(n_samples) > 0.9997).astype(float) * (np.random.rand(n_samples) * 0.15)
vinyl += random_clicks

# 4. Melodic Plucks / Lead (Gentle Pentatonic vibes)
melody_track = np.zeros(n_samples)
melody_notes = [523.25, 587.33, 659.25, 783.99, 880.00, 1046.50]  # C5, D5, E5, G5, A5, C6
for beat in range(8, total_beats - 4, 2):
    if np.random.rand() > 0.4:
        freq = np.random.choice(melody_notes)
        pluck_len = int(beat_len * 1.5 * sample_rate)
        t_pluck = np.arange(pluck_len) / sample_rate
        env = np.exp(-t_pluck * 5)
        pluck = (
            np.sin(2 * np.pi * freq * t_pluck) * 0.5 +
            np.sin(2 * np.pi * freq * 2 * t_pluck) * 0.2
        ) * env * 0.2
        p_idx = int(beat * beat_len * sample_rate)
        p_end = min(p_idx + pluck_len, n_samples)
        melody_track[p_idx:p_end] += pluck[:p_end - p_idx]

# Combine all elements
mix = chord_track * 0.45 + drum_track * 0.35 + melody_track * 0.25 + vinyl * 0.3

# Low-pass filter for vintage lo-fi warmth (cutoff ~4500 Hz)
nyq = 0.5 * sample_rate
b_lp, a_lp = butter(4, 4500.0 / nyq, btype='low')
mix = lfilter(b_lp, a_lp, mix)

# Normalize cleanly
mix = mix / (np.max(np.abs(mix)) + 1e-6) * 0.85

# Fade out last 3 seconds smoothly
fade_samples = int(3.0 * sample_rate)
fade_env = np.linspace(1.0, 0.0, fade_samples)
mix[-fade_samples:] *= fade_env

wavfile.write("/config/Desktop/BuildWithGemini/lofi_music.wav", sample_rate, (mix * 32767).astype(np.int16))
print("Lo-fi background music generated successfully!")
