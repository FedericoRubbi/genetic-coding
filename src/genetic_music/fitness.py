"""
Fitness evaluation for evolved audio.

Provides multiple fitness functions based on audio embeddings,
perceptual features, and heuristics.
"""

import numpy as np
from pathlib import Path
from typing import Optional, Union
import warnings

# Audio processing imports
try:
    import librosa
    import soundfile as sf
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    warnings.warn("librosa not available, audio loading will fail")

# ML imports for embeddings
try:
    import torch
    from transformers import ClapModel, ClapProcessor
    CLAP_AVAILABLE = True
except ImportError:
    CLAP_AVAILABLE = False
    warnings.warn("CLAP not available, embedding-based fitness will fail")


def load_audio(path: Union[str, Path], sr: int = 22050) -> np.ndarray:
    """
    Load audio file.
    
    Args:
        path: Path to audio file
        sr: Target sample rate
    
    Returns:
        Audio signal as numpy array
    """
    if not LIBROSA_AVAILABLE:
        raise RuntimeError("librosa is required for audio loading")
    
    y, _ = librosa.load(path, sr=sr, mono=True)
    return y


def compute_spectral_features(audio: np.ndarray, sr: int = 22050) -> dict:
    """
    Compute spectral features of audio.
    
    Args:
        audio: Audio signal
        sr: Sample rate
    
    Returns:
        Dictionary of features
    """
    if not LIBROSA_AVAILABLE:
        raise RuntimeError("librosa is required for feature extraction")
    
    # Spectral centroid (brightness)
    centroid = np.mean(librosa.feature.spectral_centroid(y=audio, sr=sr))
    
    # Spectral flatness (noisiness)
    flatness = np.mean(librosa.feature.spectral_flatness(y=audio))
    
    # RMS energy
    rms = np.mean(librosa.feature.rms(y=audio))
    
    # Zero crossing rate
    zcr = np.mean(librosa.feature.zero_crossing_rate(audio))
    
    # Tempo and beat strength
    tempo, beats = librosa.beat.beat_track(y=audio, sr=sr)
    
    return {
        'spectral_centroid': float(centroid),
        'spectral_flatness': float(flatness),
        'rms_energy': float(rms),
        'zero_crossing_rate': float(zcr),
        'tempo': float(tempo),
        'num_beats': len(beats)
    }


def compute_embedding(audio: np.ndarray, sr: int = 48000, model_name: str = "clap") -> np.ndarray:
    """
    Compute perceptual embedding of audio.
    
    Args:
        audio: Audio signal
        sr: Sample rate (CLAP expects 48kHz)
        model_name: Model to use ('clap', 'vggish', etc.)
    
    Returns:
        Embedding vector
    """
    if not CLAP_AVAILABLE:
        raise RuntimeError("CLAP model not available")
    
    # Load CLAP model (cache for efficiency)
    if not hasattr(compute_embedding, '_model'):
        compute_embedding._model = ClapModel.from_pretrained("laion/clap-htsat-unfused")
        compute_embedding._processor = ClapProcessor.from_pretrained("laion/clap-htsat-unfused")
    
    model = compute_embedding._model
    processor = compute_embedding._processor
    
    # Resample if needed
    if sr != 48000 and LIBROSA_AVAILABLE:
        audio = librosa.resample(audio, orig_sr=sr, target_sr=48000)
    
    # Process and get embedding
    inputs = processor(audios=audio, return_tensors="pt", sampling_rate=48000)
    
    with torch.no_grad():
        audio_embed = model.get_audio_features(**inputs)
    
    return audio_embed.numpy().flatten()


def embedding_similarity(audio1: np.ndarray, audio2: np.ndarray) -> float:
    """
    Compute cosine similarity between audio embeddings.
    
    Args:
        audio1: First audio signal
        audio2: Second audio signal
    
    Returns:
        Similarity score [0, 1]
    """
    emb1 = compute_embedding(audio1)
    emb2 = compute_embedding(audio2)
    
    # Cosine similarity
    similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
    
    # Map from [-1, 1] to [0, 1]
    return (similarity + 1) / 2


def heuristic_fitness(audio: np.ndarray, sr: int = 22050) -> float:
    """
    Compute heuristic-based fitness.
    
    Rewards:
    - Moderate spectral content (not too bright, not too dull)
    - Good dynamic range
    - Rhythmic structure
    - Reasonable energy levels
    
    Args:
        audio: Audio signal
        sr: Sample rate
    
    Returns:
        Fitness score [0, 1]
    """
    features = compute_spectral_features(audio, sr)
    
    # Normalize features and compute sub-scores
    centroid_score = 1.0 - abs(features['spectral_centroid'] - 2000) / 4000
    centroid_score = max(0, min(1, centroid_score))
    
    flatness_score = 1.0 - features['spectral_flatness']  # Prefer tonal
    
    energy_score = features['rms_energy']
    energy_score = max(0, min(1, energy_score * 10))  # Scale to [0, 1]
    
    rhythm_score = min(1.0, features['num_beats'] / 8)  # Prefer some beats
    
    # Weighted combination
    fitness = (
        0.3 * centroid_score +
        0.2 * flatness_score +
        0.3 * energy_score +
        0.2 * rhythm_score
    )
    
    return fitness


def compute_fitness(
    audio_path: Union[str, Path],
    reference_audio: Optional[np.ndarray] = None,
    method: str = 'heuristic'
) -> float:
    """
    Compute fitness for an audio file.
    
    Args:
        audio_path: Path to audio file
        reference_audio: Reference audio for similarity (optional)
        method: Fitness method ('heuristic', 'embedding', 'combined')
    
    Returns:
        Fitness score [0, 1]
    """
    audio = load_audio(audio_path)
    
    if method == 'heuristic':
        return heuristic_fitness(audio)
    
    elif method == 'embedding':
        if reference_audio is None:
            raise ValueError("reference_audio required for embedding method")
        return embedding_similarity(audio, reference_audio)
    
    elif method == 'combined':
        heuristic = heuristic_fitness(audio)
        if reference_audio is not None:
            similarity = embedding_similarity(audio, reference_audio)
            return 0.6 * heuristic + 0.4 * similarity
        return heuristic
    
    else:
        raise ValueError(f"Unknown method: {method}")

