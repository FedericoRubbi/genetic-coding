"""Fitness evaluation for genetic music generation.

This module provides utilities for evaluating pattern fitness based on
audio feature similarity to a target audio file.
"""

from __future__ import annotations

import os
from typing import Dict, Optional

import librosa
import numpy as np
from pydub import AudioSegment

from genetic_music.backend.backend import Backend
from genetic_music.codegen.tidal_codegen import to_tidal
from genetic_music.genome.genome import Genome

# ---------------------------------------------------------------------------
# Audio format utilities
# ---------------------------------------------------------------------------


def ensure_wav(path: str | os.PathLike) -> str:
    """Ensure the audio file at the given path is available in .wav format.

    If the file is not already a .wav, converts from mp3 or other formats
    as needed.

    Parameters
    ----------
    path:
        Path to the audio file.

    Returns
    -------
    str
        Path to the .wav version of the file.
    """

    if not isinstance(path, str):
        path = str(path)
    if path.endswith(".wav"):
        return path

    wav_path = os.path.splitext(path)[0] + ".wav"
    if not os.path.exists(wav_path):
        audio = AudioSegment.from_file(path)
        audio.export(wav_path, format="wav")

    return wav_path

# ---------------------------------------------------------------------------
# Feature similarity functions
# ---------------------------------------------------------------------------


def cosine_similarity(
    a: np.ndarray, b: np.ndarray, eps: float = 1e-10
) -> float:
    """Compute the cosine similarity between two vectors.

    Returns 0 if either vector is near-silent.

    Parameters
    ----------
    a, b:
        Input vectors.
    eps:
        Minimum norm threshold for non-zero comparison.

    Returns
    -------
    float
        Cosine similarity in [0, 1].
    """

    min_len = min(len(a), len(b))
    a, b = a[:min_len], b[:min_len]

    norm_a, norm_b = np.linalg.norm(a), np.linalg.norm(b)
    if norm_a < eps or norm_b < eps:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))


def cosine_matrix_similarity(
    M1: np.ndarray, M2: np.ndarray, eps: float = 1e-10
) -> float:
    """Frame-wise cosine similarity for time-varying features (MFCC, chroma).

    Averages across frames to get overall similarity.

    Parameters
    ----------
    M1, M2:
        Feature matrices (features x time).
    eps:
        Minimum norm threshold for non-zero comparison.

    Returns
    -------
    float
        Average cosine similarity across frames.
    """

    min_cols = min(M1.shape[1], M2.shape[1])
    M1, M2 = M1[:, :min_cols], M2[:, :min_cols]
    sims = [
        cosine_similarity(M1[:, i], M2[:, i], eps)
        for i in range(min_cols)
        if not np.isnan(M1[:, i]).any() and not np.isnan(M2[:, i]).any()
    ]

    return float(np.mean(sims)) if sims else 0.0

def fft_similarity(sig1: np.ndarray, sig2: np.ndarray) -> float:
    """Compare two waveforms in frequency domain (timbre, energy distribution).

    Returns cosine similarity of their FFT magnitudes.

    Parameters
    ----------
    sig1, sig2:
        Audio waveforms.

    Returns
    -------
    float
        Similarity in [0, 1].
    """

    min_len = min(len(sig1), len(sig2))
    sig1, sig2 = sig1[:min_len], sig2[:min_len]
    fft1, fft2 = np.fft.fft(sig1), np.fft.fft(sig2)
    mag1, mag2 = np.abs(fft1), np.abs(fft2)
    sim = cosine_similarity(mag1, mag2)

    return float(np.clip(sim, 0, 1))


def feature_similarity(
    audio1: str | os.PathLike, audio2: str | os.PathLike, sr: int = 22050
) -> Dict[str, float]:
    """Extract and compare multiple features of two audio files.

    Parameters
    ----------
    audio1, audio2:
        Paths to audio files to compare.
    sr:
        Target sampling rate for loading audio.

    Returns
    -------
    Dict[str, float]
        Dictionary of similarity values between 0 and 1 for each feature:
        - mfcc: Timbre similarity
        - chroma: Harmony similarity
        - rhythm: Rhythmic pattern similarity
        - fft: Spectral distribution similarity
        - rms: Dynamics similarity
        - tempo: BPM matching
        - melody: Pitch contour similarity
    """

    audio1, audio2 = ensure_wav(audio1), ensure_wav(audio2)
    y1, sr1 = librosa.load(audio1, sr=sr)
    y2, sr2 = librosa.load(audio2, sr=sr)

    min_len = min(len(y1), len(y2))
    y1, y2 = y1[:min_len], y2[:min_len]

    features: Dict[str, float] = {}

    # Timbre (MFCC): to match timbre
    mfcc1 = librosa.feature.mfcc(y=y1, sr=sr1, n_mfcc=13)
    mfcc2 = librosa.feature.mfcc(y=y2, sr=sr2, n_mfcc=13)
    features["mfcc"] = cosine_matrix_similarity(mfcc1, mfcc2)

    # Harmony (Chroma): to match harmonic content
    S1, S2 = np.abs(librosa.stft(y1)) ** 2, np.abs(librosa.stft(y2)) ** 2
    chroma1 = librosa.feature.chroma_stft(S=S1, sr=sr1)
    chroma2 = librosa.feature.chroma_stft(S=S2, sr=sr2)
    features["chroma"] = cosine_matrix_similarity(chroma1, chroma2)

    # Rhythm: to match rhythmic patterns
    onset_env1 = librosa.onset.onset_strength(y=y1, sr=sr1)
    onset_env2 = librosa.onset.onset_strength(y=y2, sr=sr2)
    features["rhythm"] = cosine_similarity(onset_env1, onset_env2)

    # Spectral Distribution (FFT): to match overall spectral shape
    features["fft"] = fft_similarity(y1, y2)

    # Dynamics (RMS Energy Curve): to match dynamics
    rms1, rms2 = librosa.feature.rms(y=y1), librosa.feature.rms(y=y2)
    features["rms"] = cosine_matrix_similarity(rms1, rms2)

    # Tempo: to match BPM
    tempo1 = librosa.beat.tempo(y=y1, sr=sr1)[0]
    tempo2 = librosa.beat.tempo(y=y2, sr=sr2)[0]
    features["tempo"] = float(
        np.clip(1 - abs(tempo1 - tempo2) / max(tempo1, tempo2), 0, 1)
    )

    # Melody/Pitch Contour: to match pitch progression
    try:
        pitch1 = librosa.yin(y1, fmin=80, fmax=1000)
        pitch2 = librosa.yin(y2, fmin=80, fmax=1000)
        features["melody"] = cosine_similarity(pitch1, pitch2)
    except Exception:
        features["melody"] = 0.0  # Fallback if pitch extraction fails

    return features


# ---------------------------------------------------------------------------
# Fitness aggregation
# ---------------------------------------------------------------------------

DEFAULT_WEIGHTS: Dict[str, float] = {
    "mfcc": 0.25,    # timbre
    "chroma": 0.25,  # harmony
    "rhythm": 0.15,  # groove
    "fft": 0.10,     # general spectrum
    "rms": 0.10,     # dynamics
    "tempo": 0.10,   # beat alignment
    "melody": 0.05,  # pitch contour
}


def compute_fitness(
    candidate_file: str | os.PathLike,
    target_file: str | os.PathLike,
    weights: Optional[Dict[str, float]] = None,
) -> tuple[float, Dict[str, float]]:
    """Compute weighted fitness based on all active features.

    Parameters
    ----------
    candidate_file:
        Path to the candidate audio file.
    target_file:
        Path to the target audio file.
    weights:
        Feature weights for aggregation. If ``None``, uses
        :data:`DEFAULT_WEIGHTS`.

    Returns
    -------
    fitness_score:
        Weighted aggregate similarity in [0, 1].
    feature_dict:
        Dictionary of individual feature similarities.
    """

    if weights is None:
        weights = DEFAULT_WEIGHTS

    sims = feature_similarity(candidate_file, target_file)
    fitness = sum(weights[k] * sims.get(k, 0) for k in weights.keys())

    return fitness, sims

# ---------------------------------------------------------------------------
# Multi-objective optimization helpers
# ---------------------------------------------------------------------------


def dominates(a: Dict[str, float], b: Dict[str, float]) -> bool:
    """Check if candidate a dominates candidate b.

    A dominates B if A is >= B for all objectives and > B for at least one.

    Parameters
    ----------
    a, b:
        Dictionaries of objective values.

    Returns
    -------
    bool
        True if a dominates b.
    """

    better_or_equal = all(a[k] >= b[k] for k in a)
    strictly_better = any(a[k] > b[k] for k in a)

    return better_or_equal and strictly_better


def pareto_front(
    candidates: list[Dict[str, float]]
) -> list[Dict[str, float]]:
    """Compute the Pareto front from a list of candidates.

    Parameters
    ----------
    candidates:
        List of candidates, each represented as a dictionary of objectives.

    Returns
    -------
    list[Dict[str, float]]
        Non-dominated set (Pareto front).
    """

    front: list[Dict[str, float]] = []
    for i, a in enumerate(candidates):
        dominated = False
        for j, b in enumerate(candidates):
            if i != j and dominates(b, a):
                dominated = True
                break
        if not dominated:
            front.append(a)
    return front

# ---------------------------------------------------------------------------
# Genome fitness evaluation
# ---------------------------------------------------------------------------


def evaluate_genome_fitness(
    genome: Genome,
    backend: Backend,
    target_audio_path: str | os.PathLike,
    candidate_output_dir: str | os.PathLike,
    duration: float = 8.0,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """Evaluate the fitness of a genome by rendering its audio and comparing to a target.

    Parameters
    ----------
    genome:
        The genome to evaluate.
    backend:
        Backend instance for rendering Tidal code to audio.
    target_audio_path:
        Path to the target audio file.
    candidate_output_dir:
        Directory to save the rendered candidate audio.
    duration:
        Duration in seconds to render the candidate audio.
    weights:
        Feature weights for fitness aggregation. If ``None``, uses
        :data:`DEFAULT_WEIGHTS`.

    Returns
    -------
    float
        Fitness score in [0, 1].
    """

    # Convert pattern tree to Tidal code
    tidal_code = to_tidal(genome.pattern_tree)

    # Ensure output directory exists
    os.makedirs(candidate_output_dir, exist_ok=True)

    # Render candidate audio
    candidate_output_path = os.path.join(
        candidate_output_dir, "candidate.wav"
    )
    recorded_path = backend.play_tidal_code(
        rhs_pattern_expr=tidal_code,
        duration=duration,
        output_path=candidate_output_path,
        playback_after=False,
    )

    # Ensure target is in wav format
    target_wav = ensure_wav(target_audio_path)

    # Compute fitness
    fitness, _ = compute_fitness(recorded_path, target_wav, weights=weights)
    return fitness


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def get_fitness(genome: Genome) -> float:
    """Convenience function for fitness evaluation with default settings.

    This function uses hardcoded paths and a global backend instance,
    suitable for quick experiments. For production use, prefer
    :func:`evaluate_genome_fitness` with explicit configuration.

    Parameters
    ----------
    genome:
        The genome to evaluate.

    Returns
    -------
    float
        Fitness score in [0, 1].
    """

    # Load configuration
    from genetic_music.config import get_boot_tidal_path
    
    try:
        BOOT_TIDAL = get_boot_tidal_path()
        if not BOOT_TIDAL:
            raise ValueError(
                "BootTidal.hs path not configured. "
                "Please create a config.yaml file (see config.yaml.example) and set tidal.boot_file_path"
            )
    except FileNotFoundError as e:
        raise FileNotFoundError(str(e))
    
    backend = Backend(
        boot_tidal_path=BOOT_TIDAL,
        orbit=8,  # SuperDirt orbit to render on
        stream=12,  # dedicated Tidal stream (d12)
    )

    base_dir = os.path.dirname(os.path.realpath(__file__))
    target = os.path.join(base_dir, "../../../data/target/target.mp3")
    candidate_dir = os.path.join(
        base_dir, "../../../data/candidate/candidate_audio"
    )

    return evaluate_genome_fitness(
        genome=genome,
        backend=backend,
        target_audio_path=target,
        candidate_output_dir=candidate_dir,
        duration=8.0,
    )