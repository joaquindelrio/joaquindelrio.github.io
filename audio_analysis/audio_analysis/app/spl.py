import os
import numpy as np
from scipy.signal import butter, sosfiltfilt


def spl(signal, p_ref=20e-6, axis=None):
    """Calcular el nivel de presión sonora (SPL) de una señal.

    Args:
        signal (array-like): Señal de presión acústica.
        p_ref (float): Presión de referencia en pascales. Por defecto 20 micropascales.
        axis (int | None): Eje a lo largo del cual calcular el RMS. Por defecto None.

    Returns:
        numpy.ndarray | float: Nivel SPL en dB re 20 µPa.
    """
    signal = np.asarray(signal, dtype=np.float64)

    if signal.size == 0:
        raise ValueError("Signal is empty")

    p_rms = np.sqrt(np.mean(signal ** 2, axis=axis))

    with np.errstate(divide="ignore"):
        spl_value = 20.0 * np.log10(p_rms / p_ref)

    return spl_value


def third_octave_band_limits(center_freq):
    """Return lower and upper third-octave band limits for a center frequency."""
    factor = 2 ** (1.0 / 6.0)
    return center_freq / factor, center_freq * factor


def bandpass_sos(center_freq, fs, order=4):
    """Design a third-octave bandpass filter as second-order sections."""
    low, high = third_octave_band_limits(center_freq)
    nyquist = fs / 2.0
    if low <= 0 or high >= nyquist:
        raise ValueError(
            f"Center frequency {center_freq} Hz is not valid for sampling rate {fs} Hz"
        )
    return butter(order, [low, high], fs=fs, btype="bandpass", output="sos")


def spl_band(signal, sample_rate, center_freq, p_ref=20e-6, order=4):
    """Calculate SPL for one third-octave band centered at center_freq."""
    signal = np.asarray(signal, dtype=np.float64)
    if signal.ndim == 2:
        signal = signal.mean(axis=1)
    sos = bandpass_sos(center_freq, sample_rate, order=order)
    filtered = sosfiltfilt(sos, signal)
    return spl(filtered, p_ref=p_ref)


def spl_third_octave_bands(signal, sample_rate, center_freqs, p_ref=20e-6, order=4):
    """Calculate SPL levels for multiple third-octave bands."""
    center_freqs = np.asarray(center_freqs, dtype=np.float64)
    levels = np.empty_like(center_freqs)
    for idx, fc in enumerate(center_freqs):
        levels[idx] = spl_band(signal, sample_rate, fc, p_ref=p_ref, order=order)
    return center_freqs, levels


def spl_time_series(
    signal,
    sample_rate,
    window_seconds=10.0,
    hop_seconds=None,
    p_ref=20e-6,
):
    """Calculate SPL time series in fixed windows.

    Args:
        signal (array-like): Time-domain signal.
        sample_rate (int): Sample rate in Hz.
        window_seconds (float): Window length in seconds.
        hop_seconds (float | None): Hop length in seconds. If None, uses window length.
        p_ref (float): Reference pressure in pascals.

    Returns:
        tuple[numpy.ndarray, numpy.ndarray]: Window center times and SPL values in dB.
    """
    signal = np.asarray(signal, dtype=np.float64)
    if signal.ndim == 2:
        signal = signal.mean(axis=1)

    if hop_seconds is None:
        hop_seconds = window_seconds

    n_window = int(round(window_seconds * sample_rate))
    n_hop = int(round(hop_seconds * sample_rate))

    if n_window < 1:
        raise ValueError("window_seconds must be positive")
    if n_hop < 1:
        raise ValueError("hop_seconds must be positive")

    n_samples = signal.shape[0]
    if n_samples < n_window:
        return np.array([], dtype=np.float64), np.array([], dtype=np.float64)

    starts = np.arange(0, n_samples - n_window + 1, n_hop)
    times = np.empty(starts.shape, dtype=np.float64)
    levels = np.empty(starts.shape, dtype=np.float64)

    for idx, start in enumerate(starts):
        window = signal[start : start + n_window]
        levels[idx] = spl(window, p_ref=p_ref)
        times[idx] = (start + n_window / 2) / sample_rate

    return times, levels


def save_spl_time_series_csv(times, levels, csv_path):
    """Save SPL time series to a CSV file."""
    output_dir = os.path.dirname(csv_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    data = np.column_stack((times, levels))
    header = "time_s,spl_db"
    np.savetxt(csv_path, data, delimiter=",", header=header, comments="", fmt="%.6f")
    try:
        os.chmod(csv_path, 0o777)
    except OSError:
        pass


def spl_band_time_series(
    signal,
    sample_rate,
    center_freq,
    window_seconds=10.0,
    hop_seconds=None,
    p_ref=20e-6,
):
    """Calculate SPL time series for a specific third-octave band."""
    signal = np.asarray(signal, dtype=np.float64)
    if signal.ndim == 2:
        signal = signal.mean(axis=1)

    if hop_seconds is None:
        hop_seconds = window_seconds

    n_window = int(round(window_seconds * sample_rate))
    n_hop = int(round(hop_seconds * sample_rate))

    if n_window < 1:
        raise ValueError("window_seconds must be positive")
    if n_hop < 1:
        raise ValueError("hop_seconds must be positive")

    if signal.shape[0] < n_window:
        return np.array([], dtype=np.float64), np.array([], dtype=np.float64)

    starts = np.arange(0, signal.shape[0] - n_window + 1, n_hop)
    times = np.empty(starts.shape, dtype=np.float64)
    levels = np.empty(starts.shape, dtype=np.float64)

    for idx, start in enumerate(starts):
        window = signal[start : start + n_window]
        levels[idx] = spl_band(window, sample_rate, center_freq, p_ref=p_ref)
        times[idx] = (start + n_window / 2) / sample_rate

    return times, levels


def sel_time_series(signal, sample_rate, window_seconds=10.0, p_ref=20e-6):
    """Calculate Sound Exposure Level (SEL) over time windows.
    
    SEL = 10 * log10(integral(p^2 / p_ref^2) / T0)
    where T0 = 1 second reference duration.
    
    Args:
        signal: Time-domain signal
        sample_rate: Sample rate in Hz
        window_seconds: Window length in seconds
        p_ref: Reference pressure (20e-6 Pa)
    
    Returns:
        tuple: (times, SEL_values_in_dB)
    """
    signal = np.asarray(signal, dtype=np.float64)
    if signal.ndim == 2:
        signal = signal.mean(axis=1)
    
    n_window = int(round(window_seconds * sample_rate))
    if signal.shape[0] < n_window:
        return np.array([], dtype=np.float64), np.array([], dtype=np.float64)
    
    n_samples = signal.shape[0]
    starts = np.arange(0, n_samples - n_window + 1, n_window)
    times = np.empty(starts.shape, dtype=np.float64)
    sel_values = np.empty(starts.shape, dtype=np.float64)
    
    T0 = 1.0  # Reference duration in seconds
    
    for idx, start in enumerate(starts):
        window = signal[start : start + n_window]
        # Energy in window
        energy = np.sum(window ** 2)
        # SEL = 10 * log10(energy / (T0 * sample_rate * p_ref^2)) 
        sel_db = 10.0 * np.log10(energy / (T0 * sample_rate * p_ref ** 2))
        sel_values[idx] = sel_db
        times[idx] = (start + n_window / 2) / sample_rate
    
    return times, sel_values


def detect_impulsive_noise(signal, sample_rate, percentile=95, margin_db=10):
    """Detect if signal contains impulsive noise.
    
    Impulsive noise typically has high peak-to-RMS ratio.
    Returns True if peaks exceed RMS by more than margin_db.
    
    Args:
        signal: Time-domain signal
        sample_rate: Sample rate in Hz
        percentile: Percentile threshold for peak detection
        margin_db: dB margin to classify as impulsive
    
    Returns:
        bool: True if impulsive noise detected
    """
    signal = np.asarray(signal, dtype=np.float64)
    if signal.ndim == 2:
        signal = signal.mean(axis=1)
    
    rms = np.sqrt(np.mean(signal ** 2))
    peak = np.percentile(np.abs(signal), percentile)
    
    if rms <= 0:
        return False
    
    peak_to_rms_db = 20.0 * np.log10(peak / rms)
    return peak_to_rms_db > margin_db


def eu_noise_indicators(signal, sample_rate, p_ref=20e-6, window_seconds=10.0):
    """Calculate EU Marine Strategy Framework Directive D11 noise indicators.
    
    Returns dict with:
    - continuous_spl_broad: SPL 10Hz-48kHz (continuous threshold 120 dB)
    - continuous_spl_low: SPL 10Hz-100Hz (continuous threshold 100 dB)
    - impulse_peak: Peak pressure (impulsive threshold 230 dB re 1µPa²/Hz)
    - noise_type: 'continuous', 'impulsive', or 'mixed'
    - sel: Sound Exposure Level
    """
    signal = np.asarray(signal, dtype=np.float64)
    if signal.ndim == 2:
        signal = signal.mean(axis=1)
    
    # Overall SPL (represents broad-band continuous noise)
    spl_broad = spl(signal, p_ref=p_ref)
    
    # Low frequency SPL (10-100 Hz) - requires filtering
    try:
        low_freq = bandpass_sos(56, sample_rate, order=4)  # Center of 10-100Hz band
        signal_low = sosfiltfilt(low_freq, signal)
        spl_low = spl(signal_low, p_ref=p_ref)
    except:
        spl_low = spl_broad  # Fallback
    
    # Peak pressure in dB re 1µPa
    peak_pressure = np.max(np.abs(signal))
    peak_db = 20.0 * np.log10(peak_pressure / p_ref)
    
    # Detect noise type
    is_impulsive = detect_impulsive_noise(signal, sample_rate)
    noise_type = 'impulsive' if is_impulsive else 'continuous'
    
    # SEL average
    times_sel, sel_vals = sel_time_series(signal, sample_rate, window_seconds, p_ref)
    sel_mean = np.mean(sel_vals) if sel_vals.size > 0 else 0.0
    
    return {
        "spl_broad_band": spl_broad,
        "spl_low_freq": spl_low,
        "peak_pressure_db": peak_db,
        "noise_type": noise_type,
        "sel_mean": sel_mean,
        "is_impulsive": is_impulsive,
    }


def evaluate_eu_compliance(indicators):
    """Evaluate compliance with MSFD D11 thresholds.
    
    Thresholds:
    - Continuous noise: 120 dB re 1µPa RMS (10Hz-48kHz)
    - Continuous noise low freq: 100 dB re 1µPa RMS (10Hz-100Hz)
    - Impulsive noise: 230 dB re 1µPa²/Hz @ 1m
    
    Returns dict with compliance status and details.
    """
    threshold_continuous_broad = 120.0
    threshold_continuous_low = 100.0
    threshold_impulsive = 230.0
    
    compliance = {
        "continuous_broad_compliant": indicators["spl_broad_band"] <= threshold_continuous_broad,
        "continuous_broad_db": indicators["spl_broad_band"],
        "continuous_broad_threshold": threshold_continuous_broad,
        "continuous_broad_excess": max(0, indicators["spl_broad_band"] - threshold_continuous_broad),
        
        "continuous_low_compliant": indicators["spl_low_freq"] <= threshold_continuous_low,
        "continuous_low_db": indicators["spl_low_freq"],
        "continuous_low_threshold": threshold_continuous_low,
        "continuous_low_excess": max(0, indicators["spl_low_freq"] - threshold_continuous_low),
        
        "impulsive_compliant": indicators["peak_pressure_db"] <= threshold_impulsive,
        "impulsive_db": indicators["peak_pressure_db"],
        "impulsive_threshold": threshold_impulsive,
        "impulsive_excess": max(0, indicators["peak_pressure_db"] - threshold_impulsive),
        
        "noise_type": indicators["noise_type"],
        "overall_compliant": (
            indicators["spl_broad_band"] <= threshold_continuous_broad and
            indicators["spl_low_freq"] <= threshold_continuous_low and
            indicators["peak_pressure_db"] <= threshold_impulsive
        ),
    }
    
    return compliance


if __name__ == "__main__":
    import argparse
    from audio_processor import load_wav_normalized

    parser = argparse.ArgumentParser(description="Calcular SPL de un archivo WAV.")
    parser.add_argument("wav_path", help="Ruta al archivo WAV")
    parser.add_argument("--ref", type=float, default=20e-6, help="Presión de referencia en Pa")
    parser.add_argument(
        "--centers",
        default=None,
        help="Frecuencias centrales de tercio de octava en Hz separadas por comas",
    )
    parser.add_argument(
        "--window",
        type=float,
        default=20.0,
        help="Longitud de ventana en segundos para la serie temporal SPL",
    )
    parser.add_argument(
        "--hop",
        type=float,
        default=None,
        help="Desplazamiento entre ventanas en segundos (por defecto igual a la ventana)",
    )
    parser.add_argument(
        "--csv",
        default=None,
        help="Ruta de salida CSV para guardar la serie temporal SPL",
    )
    args = parser.parse_args()

    sr, signal = load_wav_normalized(args.wav_path)
    overall = spl(signal, p_ref=args.ref)
    print(f"{args.wav_path}: {overall:.2f} dB SPL (ref={args.ref} Pa)")

    if args.centers:
        centers = [float(x.strip()) for x in args.centers.split(",") if x.strip()]
        freqs, levels = spl_third_octave_bands(signal, sr, centers, p_ref=args.ref)
        print("\nSPL por bandas de tercio de octava:")
        for fc, level in zip(freqs, levels):
            print(f"  {fc:.1f} Hz: {level:.2f} dB")

    times, window_levels = spl_time_series(
        signal,
        sr,
        window_seconds=args.window,
        hop_seconds=args.hop,
        p_ref=args.ref,
    )
    if times.size:
        print("\nSPL serie temporal:")
        for t, level in zip(times, window_levels):
            print(f"  {t:.1f} s: {level:.2f} dB")
        if args.csv:
            save_spl_time_series_csv(times, window_levels, args.csv)
            print(f"Serie temporal guardada en: {args.csv}")
    else:
        print("\nNo hay suficientes muestras para una ventana completa.")
