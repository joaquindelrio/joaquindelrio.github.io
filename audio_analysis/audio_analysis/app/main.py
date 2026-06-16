import argparse
import csv
import logging
import os

from audio_processor import load_wav_folder, detect_device_type
from report_generator import analyze_folder_and_generate_report
from spl import (
    save_spl_time_series_csv,
    spl,
    spl_band_time_series,
    spl_time_series,
    eu_noise_indicators,
    evaluate_eu_compliance,
)
from spectrogram import wav_to_spectrogram_png
from hydromoth_processor import process_hydromoth_folder

logger = logging.getLogger(__name__)




def configure_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    for noisy in [
        "matplotlib",
        "matplotlib.font_manager",
        "matplotlib.backends",
        "matplotlib.pyplot",
    ]:
        logging.getLogger(noisy).setLevel(logging.WARNING)


def compute_eu_metrics(signal, sample_rate, p_ref, window_seconds):
    """Compute EU Marine Strategy Framework Directive D11 indicators and compliance."""
    try:
        eu_indicators = eu_noise_indicators(
            signal,
            sample_rate,
            p_ref=p_ref,
            window_seconds=window_seconds,
        )
        eu_compliance = evaluate_eu_compliance(eu_indicators)

        logger.info(
            "  EU D11 indicators - Type: %s, Broad: %.1f dB, Low: %.1f dB",
            eu_indicators["noise_type"],
            eu_indicators["spl_broad_band"],
            eu_indicators["spl_low_freq"],
        )

        return eu_indicators, eu_compliance

    except Exception as exc:
        logger.warning("Error calculando EU indicators: %s", exc)
        return None, None
def save_combined_spl_csv(rows, csv_path):
    output_dir = os.path.dirname(csv_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["wav", "time_s", "spl_db"])
        writer.writerows(rows)
    os.chmod(csv_path, 0o777)


def process_wav_folder(
    folder_path,
    p_ref=20e-6,
    nperseg=1024,
    noverlap=None,
    cmap="viridis",
    window_seconds=20.0,
    hop_seconds=None,
    band_frequencies=(63, 125, 2000),
    csv_folder=None,
    include_spectrograms=True,
):
    """Load all WAV files in a folder, compute SPL, generate spectrogram PNGs, and save SPL time series."""
    if csv_folder is None:
        parent_dir = os.path.dirname(folder_path)
        csv_folder = os.path.join(parent_dir, "resultados")
    os.makedirs(csv_folder, exist_ok=True)

    global_csv = os.path.join(csv_folder, "all_spl_timeseries_global.csv")
    band_csvs = {
        63: os.path.join(csv_folder, "all_spl_timeseries_63Hz.csv"),
        125: os.path.join(csv_folder, "all_spl_timeseries_125Hz.csv"),
        2000: os.path.join(csv_folder, "all_spl_timeseries_2000Hz.csv"),
    }
    global_rows = []
    band_rows = {freq: [] for freq in band_csvs}

    wav_entries = list(load_wav_folder(folder_path))
    total_wavs = len(wav_entries)
    logger.info("Procesando carpeta: %s", folder_path)
    logger.info("Archivos WAV encontrados: %d", total_wavs)

    results = []

    for idx, (wav_path, sample_rate, signal) in enumerate(wav_entries, start=1):
        logger.info("[%d/%d] Procesando: %s", idx, total_wavs, os.path.basename(wav_path))
        spl_db = spl(signal, p_ref=p_ref)
        logger.debug("  sample rate: %d Hz, muestras: %d", sample_rate, signal.shape[0])
        
        # Calculate EU Marine Strategy Framework Directive D11 indicators
        #eu_indicators = eu_noise_indicators(signal, sample_rate, p_ref=p_ref, window_seconds=window_seconds)
        #eu_compliance = evaluate_eu_compliance(eu_indicators)
        eu_indicators, eu_compliance = compute_eu_metrics(signal,sample_rate,p_ref, window_seconds,)
        
        logger.info("  EU D11 indicators calculated - Type: %s, Broad: %.1f dB, Low: %.1f dB", 
                   eu_indicators["noise_type"], eu_indicators["spl_broad_band"], eu_indicators["spl_low_freq"])
        
        output_png = None
        if include_spectrograms:
            output_png = wav_to_spectrogram_png(
                wav_path,
                output_path=None,
                nperseg=nperseg,
                noverlap=noverlap,
                cmap=cmap,
            )
            logger.info("  espectrograma guardado: %s", output_png)
        #eu_indicators = None
        #eu_compliance = None


        times, levels = spl_time_series(
            signal,
            sample_rate,
            window_seconds=window_seconds,
            hop_seconds=hop_seconds,
            p_ref=p_ref,
        )
        csv_path = None
        if times.size:
            base_name = os.path.splitext(os.path.basename(wav_path))[0]
            csv_path = os.path.join(csv_folder, f"{base_name}_spl_timeseries_global.csv")
            save_spl_time_series_csv(times, levels, csv_path)
            logger.info("  SPL global CSV guardado: %s", csv_path)

            for time_value, level_value in zip(times, levels):
                global_rows.append((os.path.basename(wav_path), f"{time_value:.6f}", f"{level_value:.6f}"))
        else:
            logger.info("  SPL global CSV no disponible: audio demasiado corto")

        for freq in band_frequencies:
            times_band, levels_band = spl_band_time_series(
                signal,
                sample_rate,
                freq,
                window_seconds=window_seconds,
                hop_seconds=hop_seconds,
                p_ref=p_ref,
            )
            if times_band.size:
                band_csv_path = os.path.join(csv_folder, f"{base_name}_spl_timeseries_{int(freq)}Hz.csv")
                save_spl_time_series_csv(times_band, levels_band, band_csv_path)
                logger.info("  SPL banda %s Hz CSV guardado: %s", freq, band_csv_path)
                for time_value, level_value in zip(times_band, levels_band):
                    band_rows[int(freq)].append(
                        (os.path.basename(wav_path), f"{time_value:.6f}", f"{level_value:.6f}")
                    )
            else:
                logger.info(
                    "  SPL banda %s Hz CSV no disponible: audio demasiado corto para ventana de %ds",
                    freq,
                    int(window_seconds),
                )

        results.append((wav_path, sample_rate, float(spl_db), output_png, csv_path, eu_indicators, eu_compliance))
    save_combined_spl_csv(global_rows, global_csv)
    logger.info("CSV agregado global generado: %s", global_csv)
    for freq, csv_path in band_csvs.items():
        save_combined_spl_csv(band_rows[freq], csv_path)
        logger.info("CSV agregado banda %s Hz generado: %s", freq, csv_path)

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Procesar todos los WAV de una carpeta: SPL + espectrograma PNG."
    )
    parser.add_argument("folder", help="Carpeta que contiene archivos WAV")
    parser.add_argument("--ref", type=float, default=20e-6, help="Presión de referencia en Pa")
    parser.add_argument("--nperseg", type=int, default=1024, help="Tamaño de ventana para el espectrograma")
    parser.add_argument("--noverlap", type=int, default=None, help="Solapamiento entre ventanas")
    parser.add_argument("--cmap", default="viridis", help="Colormap para el espectrograma")
    parser.add_argument("--window", type=float, default=20.0, help="Window length in seconds for SPL time series")
    parser.add_argument("--hop", type=float, default=None, help="Hop length in seconds for SPL time series")
    parser.add_argument("--csv-folder", default=None, help="Folder to save SPL time series CSV files")
    parser.add_argument("--band-freqs", default="63,125,2000", help="Comma-separated band center frequencies for SPL time series CSV files")
    parser.add_argument("--no-pdf", action="store_true", help="No generar PDF de informe")
    parser.add_argument("--include-spectrograms", action="store_true", default=True, help="Incluir espectrogramas en el informe PDF")
    parser.add_argument("--no-spectrograms", action="store_false", dest="include_spectrograms", help="No incluir espectrogramas en el informe PDF")
    parser.add_argument("--device-type", default="auto", choices=["auto", "generic", "hydromoth"], help="Audio device type (auto=detect automatically)")
    parser.add_argument("--verbose", action="store_true", help="Show progress messages during processing")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging for detailed tracing")
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    configure_logging(level=log_level)

    band_freqs = (63, 125, 2000)
    if args.band_freqs:
        band_freqs = tuple(float(x.strip()) for x in args.band_freqs.split(",") if x.strip())

    # Detect device type
    device_type = args.device_type
    if device_type == "auto":
        device_type = detect_device_type(args.folder)
        logger.info("Dispositivo detectado: %s", device_type)
    else:
        logger.info("Dispositivo especificado: %s", device_type)

    # Process based on device type
    hydromoth_results = None
    if device_type == "hydromoth":
        logger.info("Procesando como archivos HydroMoth...")
        hydromoth_results = process_hydromoth_folder(
            args.folder,
            window_seconds=args.window,
        )
        results = []
        csv_folder = args.csv_folder or os.path.join(os.path.dirname(args.folder), "resultados")
        os.makedirs(csv_folder, exist_ok=True)
        
        # Convert HydroMoth results to compatible format with generic processor
        for result in hydromoth_results:
            
            
            # ✅ Calcular EU indicators (AQUÍ es donde debe ir)
            signal = result.get("signal")
            sample_rate = result.get("sample_rate")

            if signal is not None and sample_rate is not None:
                eu_indicators, eu_compliance = compute_eu_metrics(
                    signal,
                    sample_rate,
                    args.ref,
                    args.window,
                )
            else:
                eu_indicators, eu_compliance = None, None

            result["eu_indicators"] = eu_indicators
            result["eu_compliance"] = eu_compliance

            
            if args.include_spectrograms:
                try:
                    output_png = wav_to_spectrogram_png(
                        result["wav_path"],
                        output_path=None,
                        nperseg=args.nperseg,
                        noverlap=args.noverlap,
                        cmap=args.cmap,
                    )
                    result["spectrogram_png"] = output_png
                    logger.info("  espectrograma guardado para HydroMoth: %s", output_png)
                except Exception as exc:
                    logger.warning("No se pudo generar espectrograma HydroMoth para %s: %s", result["wav_path"], exc)
                    result["spectrogram_png"] = None
            else:
                result["spectrogram_png"] = None
            results.append({
                "type": "hydromoth",
                "data": result,
            })
    else:
        logger.info("Procesando como archivos genéricos...")
        results = process_wav_folder(
            args.folder,
            p_ref=args.ref,
            nperseg=args.nperseg,
            noverlap=args.noverlap,
            cmap=args.cmap,
            window_seconds=args.window,
            hop_seconds=args.hop,
            band_frequencies=band_freqs,
            csv_folder=args.csv_folder,
            include_spectrograms=args.include_spectrograms,
        )

    
    if not results:
        print(f"No se encontraron archivos WAV en {args.folder}")
    else:
        print("Procesamiento completado:\n")

        if device_type == "hydromoth":
            for item in results:
                result = item["data"]
                print(f"{result.get('wav_path', 'N/A')}")
                print(f"  sample rate: {result.get('sample_rate', 'N/A')}")
                print(f"  SPL: {result.get('spl_overall_db', 0.0):.2f} dB")
                if result.get("spectrogram_png"):
                    print(f"  espectrograma: {result.get('spectrogram_png')}")
                else:
                    print("  espectrograma: no disponible para HydroMoth")
                print("  serie temporal CSV: no disponible para HydroMoth")
                print()
        else:
            for wav_path, sample_rate, spl_db, output_png, csv_path, eu_indicators, eu_compliance in results:
                print(f"{wav_path}")
                print(f"  sample rate: {sample_rate}")
                print(f"  SPL: {spl_db:.2f} dB")
                print(f"  espectrograma: {output_png}")
                if csv_path:
                    print(f"  serie temporal CSV: {csv_path}")
                else:
                    print("  serie temporal CSV: no disponible (audio demasiado corto)")
                print()

        if not args.no_pdf:
            pdf_folder = args.csv_folder or os.path.join(os.path.dirname(args.folder), "resultados")
            pdf_path = os.path.join(pdf_folder, "audio_analysis_report.pdf")
            logger.info("Generando PDF de informe: %s", pdf_path)
            analyze_folder_and_generate_report(
                args.folder,
                pdf_path=pdf_path,
                centers=None,
                band_frequencies=band_freqs,
                window_seconds=args.window,
                hop_seconds=args.hop,
                band_window_seconds=args.window,
                nperseg=args.nperseg,
                noverlap=args.noverlap,
                cmap=args.cmap,
                p_ref=args.ref,
                include_spectrograms=args.include_spectrograms,
                device_type=device_type,
                hydromoth_results=hydromoth_results if device_type == "hydromoth" else None,
            )
            print(f"PDF report generated at: {pdf_path}")


