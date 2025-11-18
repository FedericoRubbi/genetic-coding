from pydub import AudioSegment
from pydub.playback import play
import librosa
import numpy as np
import os

# UTILS FUNCTIONS
def ensure_wav(path):
    """
    Ensures the audio file at the given path is available in .wav format for analysis 
    (converts from mp3 or other formats if needed)
    """
    if path.endswith('.wav'): 
        return path

    wav_path = os.path.splitext(path)[0] + '.wav'
    if not os.path.exists(wav_path):
        audio = AudioSegment.from_file(path)
        audio.export(wav_path, format='wav')

    return wav_path

# FEATURE SIMILARITY FUNCTIONS
def cosine_similarity(a, b, eps=1e-10):
    """
    Computes the cosine similarity between two vectors
    (returns 0 if either vector is near-silent)
    """
    min_len = min(len(a), len(b))
    a, b = a[:min_len], b[:min_len]
    
    norm_a, norm_b = np.linalg.norm(a), np.linalg.norm(b)
    if norm_a < eps or norm_b < eps:
        return 0.0
    
    return np.dot(a, b) / (norm_a * norm_b)


def cosine_matrix_similarity(M1, M2, eps=1e-10):
    """
    Frame-wise cosine similarity for time-varying features (MFCC, chroma).
    Averages across frames to get overall similarity.
    """
    min_cols = min(M1.shape[1], M2.shape[1])
    M1, M2 = M1[:, :min_cols], M2[:, :min_cols]
    sims = [
        cosine_similarity(M1[:, i], M2[:, i], eps)
        for i in range(min_cols)
        if not np.isnan(M1[:, i]).any() and not np.isnan(M2[:, i]).any()
    ]

    return np.mean(sims) if sims else 0.0

def fft_similarity(sig1, sig2):
    """
    Compares two waveforms in frequency domain (timbre, energy distribution).
    Returns cosine similarity of their FFT magnitudes.
    """
    min_len = min(len(sig1), len(sig2))
    sig1, sig2 = sig1[:min_len], sig2[:min_len]
    fft1, fft2 = np.fft.fft(sig1), np.fft.fft(sig2)
    mag1, mag2 = np.abs(fft1), np.abs(fft2)
    sim = cosine_similarity(mag1, mag2)

    return np.clip(sim, 0, 1)


def feature_similarity(audio1, audio2, sr=22050): # sr is the sampling rate
    """
    Extracts and compares multiple features of two audio files.
    Returns dictionary of similarity values between 0 and 1.
    """
    audio1, audio2 = ensure_wav(audio1), ensure_wav(audio2)
    y1, sr1 = librosa.load(audio1, sr=sr)
    y2, sr2 = librosa.load(audio2, sr=sr)
    
    min_len = min(len(y1), len(y2))
    y1, y2 = y1[:min_len], y2[:min_len]

    features = {}

    # Timbre (MFCC): to match timbre
    mfcc1, mfcc2 = librosa.feature.mfcc(y=y1, sr=sr1, n_mfcc=13), librosa.feature.mfcc(y=y2, sr=sr2, n_mfcc=13)
    features["mfcc"] = cosine_matrix_similarity(mfcc1, mfcc2)

    # Harmony (Chroma): to match harmonic content
    S1, S2 = np.abs(librosa.stft(y1))**2, np.abs(librosa.stft(y2))**2
    chroma1, chroma2 = librosa.feature.chroma_stft(S=S1, sr=sr1), librosa.feature.chroma_stft(S=S2, sr=sr2)
    features["chroma"] = cosine_matrix_similarity(chroma1, chroma2)

    # Rhythm: to match rhythmic patterns
    onset_env1, onset_env2 = librosa.onset.onset_strength(y=y1, sr=sr1), librosa.onset.onset_strength(y=y2, sr=sr2)
    features["rhythm"] = cosine_similarity(onset_env1, onset_env2)

    # Spectral Distribution (FFT): to match overall spectral shape
    features["fft"] = fft_similarity(y1, y2)

    # Dynamics (RMS Energy Curve): to match dynamics
    rms1, rms2 = librosa.feature.rms(y=y1), librosa.feature.rms(y=y2)
    features["rms"] = cosine_matrix_similarity(rms1, rms2)

    # Tempo: to match BPM
    tempo1, tempo2 = librosa.beat.tempo(y=y1, sr=sr1)[0], librosa.beat.tempo(y=y2, sr=sr2)[0]
    features["tempo"] = 1 - abs(tempo1 - tempo2) / max(tempo1, tempo2)
    features["tempo"] = np.clip(features["tempo"], 0, 1)

    # Melody/Pitch Contour: to match pitch progression
    try:
        pitch1 = librosa.yin(y1, fmin=80, fmax=1000)
        pitch2 = librosa.yin(y2, fmin=80, fmax=1000)
        features["melody"] = cosine_similarity(pitch1, pitch2)
    except Exception:
        features["melody"] = 0.0 # Fallback if pitch extraction fails

    return features


# FITNESS AGGREGATION (here fixed weights, A PRIORI, but we could adapt them/use pareto front instead)
DEFAULT_WEIGHTS = {
    "mfcc": 0.25,    # timbre
    "chroma": 0.25,  # harmony
    "rhythm": 0.15,  # groove
    "fft": 0.10,     # general spectrum
    "rms": 0.10,     # dynamics
    "tempo": 0.10,   # beat alignment
    "melody": 0.05   # pitch contour
}

def compute_fitness(candidate_file, target_file, weights=None):
    """
    Compute weighted fitness based on all active features.
    Returns (fitness_score, feature_dict).
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    sims = feature_similarity(candidate_file, target_file)
    fitness = sum(weights[k] * sims.get(k, 0) for k in weights.keys())

    return fitness, sims

# MULTI-OBJECTIVE OPTIMIZATION HELPERS (A POSTERIORI)
def dominates(a, b):
    """
    Returns True if candidate a dominates candidate b
    (a is >= b for all objectives, and > for at least one)
    """
    better_or_equal = all(a[k] >= b[k] for k in a)
    strictly_better = any(a[k] > b[k] for k in a)

    return better_or_equal and strictly_better

def pareto_front(candidates):
    """
    Given a list of candidates (dictonary of objectives), returns non-dominated set.
    """
    front = []
    for i, a in enumerate(candidates):
        dominated = False
        for j, b in enumerate(candidates):
            if i != j and dominates(b, a):
                dominated = True
                break
        if not dominated:
            front.append(a)
    return front

# MAIN EXECUTION
if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.realpath(__file__))
    target = os.path.join(base_dir, "data/target_audio/target.mp3")
    candidate_dir = os.path.join(base_dir, "data/candidate_audio")

    candidates = [os.path.join(candidate_dir, f) for f in os.listdir(candidate_dir) if f.endswith(('.mp3', '.wav'))]
    target_wav = ensure_wav(target)

    print(f"Target: {os.path.basename(target_wav)}")
    results = []

    for c in candidates:
        fitness, components = compute_fitness(c, target_wav)
        results.append((os.path.basename(c), fitness))
        print(f"\nCandidate: {os.path.basename(c)}")
        print(f"  Total fitness: {fitness:.3f}")
        for k, v in components.items():
            print(f"    {k}: {v:.3f}")

    print("\nSorted candidates (from best to worst):")
    for name, score in sorted(results, key=lambda x: x[1], reverse=True):
        print(f"{name}: {score:.3f}")
    
    # Play the best candidate and the target for auditory comparison
    best_candidate = max(results, key=lambda x: x[1])[0]
    print(f"\nPlaying best candidate: {best_candidate}")
    play(AudioSegment.from_file(os.path.join(candidate_dir, best_candidate)))
    print("Playing target audio:")
    play(AudioSegment.from_file(target))