import numpy as np
from scipy.signal import hilbert


PHASE_FACTOR = 0.70710678


def prevent_clipping(data: np.ndarray) -> np.ndarray:
    """
    Scale all channels equally if the decoded audio exceeds 1.0.

    Parameters:
        data: Multichannel float32 audio array.

    Returns:
        Scaled float32 audio array.
    """

    peak_value = np.max(np.abs(data))

    if peak_value > 1.0:
        scale = 0.98 / peak_value
        data *= scale

    return data.astype(np.float32)


def decode_sq(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """
    Basic CBS SQ matrix decoder.

    Input:
        Left and Right stereo SQ encoded channels.

    Output:
        4 channels:
        FL, FR, RL, RR

    This is a simplified fixed matrix decoder.
    It does not include Tate/Fosgate logic steering.
    """

    # Generate quadrature phase signals
    L90 = np.imag(hilbert(left))
    R90 = np.imag(hilbert(right))

    decoded = np.zeros(
        (len(left), 4),
        dtype=np.float32
    )

    # Front channels
    decoded[:, 0] = left + (PHASE_FACTOR * R90)
    decoded[:, 1] = right - (PHASE_FACTOR * L90)

    # Rear channels
    decoded[:, 2] = left - (PHASE_FACTOR * R90)
    decoded[:, 3] = right + (PHASE_FACTOR * L90)

    return prevent_clipping(decoded)


def decode_qs(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """
    Basic Sansui QS matrix decoder.

    Input:
        Left and Right QS encoded channels.

    Output:
        4 channels:
        FL, FR, RL, RR

    This is a simplified fixed matrix QS decoder.
    """

    # Generate quadrature phase signals
    L90 = np.imag(hilbert(left))
    R90 = np.imag(hilbert(right))

    decoded = np.zeros(
        (len(left), 4),
        dtype=np.float32
    )

    # Front channels
    decoded[:, 0] = left
    decoded[:, 1] = right

    # Rear channels extracted from phase information
    decoded[:, 2] = left - R90
    decoded[:, 3] = right + L90

    return prevent_clipping(decoded)


def decode_ev4(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """
    Basic Electro-Voice Stereo-4 / Dynaquad decoder.

    Input:
        Left and Right EV-4 encoded channels.

    Output:
        4 channels:
        FL, FR, RL, RR

    This is a simplified fixed matrix decoder.
    """

    decoded = np.zeros(
        (len(left), 4),
        dtype=np.float32
    )

    # Front channels
    decoded[:, 0] = left
    decoded[:, 1] = right

    # Rear channels from difference information
    decoded[:, 2] = (left - right) * PHASE_FACTOR
    decoded[:, 3] = (right - left) * PHASE_FACTOR

    return prevent_clipping(decoded)


def sq_decoder(stereo_data: np.ndarray) -> np.ndarray:
    """
    Decode SQ stereo input.

    Input:
        Shape:
        (samples, 2)

    Output:
        Shape:
        (samples, 4)
    """

    left = stereo_data[:, 0]
    right = stereo_data[:, 1]

    return decode_sq(left, right)


def qs_decoder(stereo_data: np.ndarray) -> np.ndarray:
    """
    Decode QS stereo input.

    Input:
        Shape:
        (samples, 2)

    Output:
        Shape:
        (samples, 4)
    """

    left = stereo_data[:, 0]
    right = stereo_data[:, 1]

    return decode_qs(left, right)


def ev4_decoder(stereo_data: np.ndarray) -> np.ndarray:
    """
    Decode EV-4 Stereo-4 input.

    Input:
        Shape:
        (samples, 2)

    Output:
        Shape:
        (samples, 4)
    """

    left = stereo_data[:, 0]
    right = stereo_data[:, 1]

    return decode_ev4(left, right)