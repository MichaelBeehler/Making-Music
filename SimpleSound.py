import numpy as np
import sounddevice as sd

# --- Config ---
SAMPLE_RATE = 44100

# Note frequencies (A4 = 440 Hz)
def build_note_freqs():
    note_names = ["C", "C#", "D", "D#", "E", "F",
                  "F#", "G", "G#", "A", "A#", "B"]
    note_freqs = {}
    for midi in range(21, 109):  # A0 (21) to C8 (108)
        octave = (midi // 12) - 1
        name = note_names[midi % 12] + str(octave)
        freq = 440.0 * (2 ** ((midi - 69) / 12))
        note_freqs[name] = round(freq, 2)
    return note_freqs

NOTE_FREQS = build_note_freqs()

BPM = 150
SECONDS_PER_BEAT = 60 / BPM

def beats_to_seconds(beats):
    return beats * SECONDS_PER_BEAT


# --- Waveform generators ---
def sine_wave(f, d):
    t = np.linspace(0, d, int(SAMPLE_RATE*d), endpoint=False)
    return 0.5 * np.sin(2*np.pi*f*t)

def square_wave(f, d):
    t = np.linspace(0, d, int(SAMPLE_RATE*d), endpoint=False)
    return 0.5 * np.sign(np.sin(2*np.pi*f*t))

def triangle_wave(f, d):
    t = np.linspace(0, d, int(SAMPLE_RATE*d), endpoint=False)
    return 0.5 * (2*np.arcsin(np.sin(2*np.pi*f*t))/np.pi)

def noise_wave(d):
    return np.random.uniform(-0.5, 0.5, int(SAMPLE_RATE*d))

# Map waveform name to function
WAVES = {"sine": sine_wave, "square": square_wave, "triangle": triangle_wave, "noise": noise_wave}

# --- Note player ---
def play_note(note, duration=0.5, wave="sine"):
    if wave == "noise":
        samples = WAVES[wave](duration)
    else:
        freq = NOTE_FREQS.get(note)
        if freq is None:
            raise ValueError(f"Unknown note: {note}")
        samples = WAVES[wave](freq, duration)

    sd.play(samples, SAMPLE_RATE)
    sd.wait()

"""def play_song(sequence, wave="square"):
    song = np.array([], dtype=np.float32)
    for note, duration in sequence:
        if note == "REST":
            samples = np.zeros(int(SAMPLE_RATE * duration))
        elif wave == "noise":
            samples = noise_wave(duration)
        else:
            freq = NOTE_FREQS.get(note)
            if freq is None:
                raise ValueError(f"Unknown note: {note}")
            samples = WAVES[wave](freq, duration)
        song = np.concatenate([song, samples])
    sd.play(song, SAMPLE_RATE)
    sd.wait() """

def play_song(tracks, wave="square"):
    """
    tracks: list of sequences, e.g. [melody, bass]
    each sequence is a list of (note, duration) tuples
    """
    # Convert each track into a waveform
    track_waves = []
    for sequence in tracks:
        song = np.array([], dtype=np.float32)
        for note, beats in sequence:
            duration = beats_to_seconds(beats)
            if note == "REST":
                samples = np.zeros(int(SAMPLE_RATE * duration))
            elif wave == "noise":
                samples = noise_wave(duration)
            else:
                freq = NOTE_FREQS.get(note)
                if freq is None:
                    raise ValueError(f"Unknown note: {note}")
                samples = WAVES[wave](freq, duration)
            song = np.concatenate([song, samples])
        track_waves.append(song)

    # Pad shorter tracks so they're all equal length
    max_len = max(len(track) for track in track_waves)
    padded = [np.pad(track, (0, max_len - len(track))) for track in track_waves]

    # Mix by averaging
    mix = np.sum(padded, axis=0) / len(tracks)

    # Normalize to avoid clipping
    mix = mix / np.max(np.abs(mix))

    sd.play(mix, SAMPLE_RATE)
    sd.wait()


intro_melody = [
    ("G5", 4), ("F#5", 2), ("B5", 2), ("E5", 4),
    ("D5", 2), ("G5", 2), ("C5", 4), ("B4", 2), ("E5", 2),
    ("A4", 4), ("D5", 3), ("F#5", 0.5), ("G5", 0.5), ("D5", 2), ("REST", 0.5),
]


bass = [
    ("REST", 32), ("G4", 4), ("F#4", 2), ("B4", 2), ("E4", 4),
    ("D4", 2), ("G4", 2), ("C4", 4), ("B3", 2), ("E4", 2),
    ("A3", 4), ("D4", 3) 
]


play_song([intro_melody, bass], wave="square")
# --- Demo melody ---
""" if __name__ == "__main__":
    play_note("C4", 0.3, wave="square")
    play_note("E4", 0.3, wave="square")
    play_note("G4", 0.3, wave="square")
    play_note("C5", 0.5, wave="square")
 """
