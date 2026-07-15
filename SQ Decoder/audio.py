import soundfile as sf
import numpy as np


def load_wav(filepath: str) -> tuple[np.ndarray, int]:
    """
    Load a stereo 48kHz PCM WAV file.

    Returns:
        data:
            Float32 numpy array shaped (samples, 2)

        samplerate:
            Sample rate
    """

    data, samplerate = sf.read(
        filepath,
        dtype="float32"
    )

    if (
        len(data.shape) != 2
        or data.shape[1] != 2
        or samplerate != 48000
    ):
        raise ValueError(
            "Unsupported format: Must be stereo 48kHz PCM WAV."
        )

    return data, samplerate


def to_float32(data: np.ndarray) -> np.ndarray:
    """
    Convert integer PCM audio to float32.

    Note:
    soundfile already returns float32 when requested,
    so this is only needed for raw integer data.
    """

    return data.astype(np.float32) / 32768.0


def normalize(data: np.ndarray) -> np.ndarray:
    """
    Normalize audio data to prevent clipping.

    All channels are scaled together.
    """

    peak = np.max(np.abs(data))

    if peak > 1.0:
        data = data * (0.98 / peak)

    return data.astype(np.float32)


def export_flac(
    filepath: str,
    data: np.ndarray,
    samplerate: int
) -> None:
    """
    Export multichannel FLAC.

    Expected input:

    Channel 0:
        Front Left

    Channel 1:
        Front Right

    Channel 2:
        Center (silent)

    Channel 3:
        LFE (silent)

    Channel 4:
        Surround Left

    Channel 5:
        Surround Right
    """

    print("----------------------------")
    print("Preparing FLAC export")
    print("Array shape:", data.shape)
    print("Sample rate:", samplerate)
    print("Channel count:", data.shape[1])

    for channel in range(data.shape[1]):
        print(
            f"Channel {channel} peak:",
            np.max(np.abs(data[:, channel]))
        )

    print("----------------------------")

    if data.ndim != 2:
        raise ValueError(
            "Audio data must be a 2D numpy array."
        )

    if data.shape[1] != 6:
        raise ValueError(
            f"Expected 6 channels for 5.1 FLAC, got {data.shape[1]}"
        )

    sf.write(
        filepath,
        data,
        samplerate,
        format="FLAC",
        subtype="PCM_16"
    )

    print("FLAC export complete")