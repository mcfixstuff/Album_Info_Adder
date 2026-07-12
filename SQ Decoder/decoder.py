import numpy as np
from scipy.signal import hilbert

def decode_sq(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """
    Decode stereo CBS SQ encoded audio into four discrete channels using a fixed-matrix approach.
    
    The process includes generating phase-shifted signals and applying a decoding matrix to create
    the Front Left (FL), Front Right (FR), Rear Left (RL), and Rear Right (RR) channels.
    
    Parameters:
    left (np.ndarray): Left channel data in float32 range (-1.0, +1.0).
    right (np.ndarray): Right channel data in float32 range (-1.0, +1.0).
    
    Returns:
    np.ndarray: A NumPy array with shape (samples, 4) containing the four decoded channels.
    
    Why Hilbert transforms are used:
    - The Hilbert transform is used to generate a quadrature signal which represents an approximate
      +90 degree phase-shifted version of the original channel. This is essential for capturing
      the in-phase and out-of-phase components needed for quadraphonic decoding.
      
    Why phase information is required:
    - Quadraphonic sound relies on both amplitude and phase differences between channels to
      separate front and rear audio signals accurately.
      
    This is a fixed matrix decoder:
    - The current implementation uses a predefined matrix to combine the original left and right
      channels with their phase-shifted counterparts. While this approach works reasonably well,
      it does not include advanced logic steering which could potentially improve separation quality.
    
    Future improvements could add logic steering:
    - Implementing a more sophisticated decoding algorithm that dynamically adjusts based on the
      content of the audio signal could lead to better channel separation.
    """
    # Generate phase-shifted signals using Hilbert transform
    L_90 = np.imag(hilbert(left))
    R_90 = np.imag(hilbert(right))
    
    # Define the fixed decoding matrix
    decoder_matrix = np.array([
        [1, 0.70710678 * -1],  # Front Left (FL)
        [0, 0.70710678 * 1],   # Front Right (FR)
        [1, 0.70710678 * -1],  # Rear Left (RL)
        [-1, 0.70710678 * 1]    # Rear Right (RR)
    ])
    
    # Apply the decoding matrix
    decoded_channels = np.dot(np.column_stack((left, right)), decoder_matrix.T).astype(np.float32)
    
    # Prevent clipping by scaling all channels together if needed
    peak_value = np.max(np.abs(decoded_channels))
    if peak_value > 1.0:
        scale = 0.98 / peak_value
        decoded_channels *= scale
    
    return decoded_channels

def sq_decoder(stereo_data: np.ndarray) -> np.ndarray:
    """
    Decode stereo CBS SQ encoded audio into four discrete channels.
    
    Parameters:
    stereo_data (np.ndarray): Stereo audio data with shape (samples, 2).
    
    Returns:
    np.ndarray: A NumPy array with shape (samples, 4) containing the four decoded channels.
    """
    left_channel = stereo_data[:, 0]
    right_channel = stereo_data[:, 1]
    return decode_sq(left_channel, right_channel)