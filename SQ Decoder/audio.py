import soundfile as sf
import numpy as np

def load_wav(filepath: str) -> tuple[np.ndarray, int]:
    """Load a stereo 16-bit 48,000 Hz PCM WAV file."""
    data, samplerate = sf.read(filepath)
    if len(data.shape) != 2 or data.shape[1] != 2 or samplerate != 48000:
        raise ValueError("Unsupported format: Must be stereo, 48kHz, and 16-bit.")
    return data.astype(np.float32), samplerate

def to_float32(data: np.ndarray) -> np.ndarray:
    """Convert PCM int16 data to float32."""
    return data / (2**15)

def normalize(data: np.ndarray) -> np.ndarray:
    """Normalize audio data to prevent clipping."""
    max_amplitude = np.max(np.abs(data))
    if max_amplitude > 1.0:
        return data / max_amplitude
    return data

def export_flac(filepath: str, data: np.ndarray, samplerate: int) -> None:
    """Export a single multichannel FLAC file."""
    sf.write(filepath, data, samplerate)