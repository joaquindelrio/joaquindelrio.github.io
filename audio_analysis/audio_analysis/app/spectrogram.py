import argparse
import os

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

from audio_processor import load_wav_normalized


def compute_spectrogram(signal_data, sample_rate, nperseg=1024, noverlap=None, window="hann"):
    """Compute a spectrogram using scipy.signal.spectrogram.

    Args:
        signal_data (np.ndarray): Time-domain signal.
        sample_rate (int): Sampling rate in Hz.
        nperseg (int): Length of each segment.
        noverlap (int | None): Number of points to overlap between segments.
        window (str): Window function name.

    Returns:
        tuple[np.ndarray, np.ndarray, np.ndarray]: Frequencies, times, and spectrogram magnitude in dB.
    """
    if noverlap is None:
        noverlap = nperseg // 2

    freqs, times, Sxx = signal.spectrogram(
        signal_data,
        fs=sample_rate,
        window=window,
        nperseg=nperseg,
        noverlap=noverlap,
        mode="magnitude",
    )

    Sxx = np.maximum(Sxx, 1e-20)
    Sxx_db = 20.0 * np.log10(Sxx)
    return freqs, times, Sxx_db


def save_spectrogram_png(output_path, freqs, times, Sxx_db, cmap="viridis"):
    """Save a spectrogram as a PNG image."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 3), constrained_layout=True)
    img = ax.pcolormesh(times, freqs, Sxx_db, shading="auto", cmap=cmap)
    ax.set_ylabel("Frequency [Hz]")
    ax.set_xlabel("Time [s]")
    ax.set_title("Spectrogram")
    fig.colorbar(img, ax=ax, label="Magnitude [dB]")
    ax.set_ylim(0, freqs.max())
    fig.savefig(output_path, dpi=100)
    try:
        os.chmod(output_path, 0o777)
    except OSError:
        pass
    plt.close(fig)


def default_resultados_png_path(wav_path, resultados_name="resultados", suffix="_spectrogram.png"):
    """Build a default output path in the experiment resultados folder."""
    base_name = os.path.splitext(os.path.basename(wav_path))[0]
    audio_dir = os.path.dirname(wav_path)
    parent_dir = os.path.dirname(audio_dir)
    resultados_dir = os.path.join(parent_dir, resultados_name)
    os.makedirs(resultados_dir, exist_ok=True)
    return os.path.join(resultados_dir, f"{base_name}{suffix}")


def wav_to_spectrogram_png(wav_path, output_path=None, nperseg=512, noverlap=None, cmap="viridis"):
    """Load a WAV file, compute its spectrogram, and save as PNG."""
    sample_rate, signal_data = load_wav_normalized(wav_path)
    freqs, times, Sxx_db = compute_spectrogram(signal_data, sample_rate, nperseg=nperseg, noverlap=noverlap)

    if output_path is None:
        output_path = default_resultados_png_path(wav_path)

    save_spectrogram_png(output_path, freqs, times, Sxx_db, cmap=cmap)
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a PNG spectrogram from a WAV file.")
    parser.add_argument("wav_path", help="Path to the WAV file")
    parser.add_argument("--out", default=None, help="Output PNG file path")
    parser.add_argument("--nperseg", type=int, default=1024, help="Number of samples per segment")
    parser.add_argument("--noverlap", type=int, default=None, help="Number of overlapping samples")
    parser.add_argument("--cmap", default="viridis", help="Matplotlib colormap")
    args = parser.parse_args()

    output_path = wav_to_spectrogram_png(
        args.wav_path,
        output_path=args.out,
        nperseg=args.nperseg,
        noverlap=args.noverlap,
        cmap=args.cmap,
    )
    print(f"Spectrogram saved to: {output_path}")
