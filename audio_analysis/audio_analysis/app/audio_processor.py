import glob
import os

import numpy as np
from scipy.io import wavfile
from hydromoth_processor import is_hydromoth_file


def load_wav_normalized(path):
    """Cargar un archivo WAV y devolver frecuencia y señal float32 normalizada.

    Args:
        path (str): Path to the WAV file.

    Returns:
        tuple[int, np.ndarray]: Sampling rate and signal as float32 in [-1.0, 1.0].
    """
    sample_rate, data = wavfile.read(path)
    data_float = data.astype(np.float32)

    if data.dtype == np.int16:
        signal = data_float / 32768.0
    elif data.dtype == np.int32:
        signal = data_float / 2147483648.0
    elif data.dtype == np.uint8:
        signal = (data_float - 128.0) / 128.0
    elif data.dtype == np.float32 or data.dtype == np.float64:
        signal = data_float
    else:
        raise ValueError(f"Unsupported WAV data type: {data.dtype}")

    if signal.ndim == 2:
        signal = signal.mean(axis=1)

    return sample_rate, signal


def load_wav_folder(folder_path, pattern="*.wav"):
    """Load all WAV files in a folder.

    Args:
        folder_path (str): Directory containing WAV files.
        pattern (str): Glob pattern for WAV files.

    Returns:
        list[tuple[str, int, np.ndarray]]: List of (path, sample_rate, signal).
    """
    folder_path = os.fspath(folder_path)
    wav_paths = sorted(glob.glob(os.path.join(folder_path, pattern)))
    results = []

    for wav_path in wav_paths:
        sr, signal = load_wav_normalized(wav_path)
        results.append((wav_path, sr, signal))

    return results


def detect_device_type(folder_path):
    """
    Automatically detect the audio device type based on WAV file characteristics.
    
    Args:
        folder_path (str): Directory containing WAV files
    
    Returns:
        str: Device type ('hydromoth', 'generic', or 'unknown')
    """
    folder_path = os.fspath(folder_path)
    wav_paths = sorted(glob.glob(os.path.join(folder_path, "*.wav")))
    
    if not wav_paths:
        return "unknown"
    
    # Check first WAV file
    first_wav = wav_paths[0]
    
    # Try to detect HydroMoth
    if is_hydromoth_file(first_wav):
        return "hydromoth"
    
    return "generic"

