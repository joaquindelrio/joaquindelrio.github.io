import csv
import io
import logging
import os

import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from audio_processor import load_wav_folder, load_wav_normalized
from spl import (
    save_spl_time_series_csv,
    spl,
    spl_band_time_series,
    spl_third_octave_bands,
    spl_time_series,
    eu_noise_indicators,
    evaluate_eu_compliance,
)
from spectrogram import wav_to_spectrogram_png


def plot_spl_time_series(times, levels, output_path, title="SPL Time Series"):
    """Plot SPL time series and save it as a PNG file."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 4), constrained_layout=True)
    ax.plot(times, levels, marker="o", linestyle="-", color="#0056b3")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("SPL (dB)")
    ax.set_title(title)
    ax.grid(True, alpha=0.4)
    fig.savefig(output_path, dpi=150)
    try:
        os.chmod(output_path, 0o777)
    except OSError:
        pass
    plt.close(fig)
    return output_path

def plot_combined_spl_timeseries(rows, output_path, title="Combined SPL Time Series"):
    import datetime
    import matplotlib.dates as mdates

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    if not rows:
        return None

    data_by_wav = {}

    for wav, time_s, spl_db in rows:
        data_by_wav.setdefault(wav, []).append((float(time_s), float(spl_db)))

    cumulative_times = []
    cumulative_levels = []

    # ✅ construir datos sin concatenación artificial
    for wav, samples in sorted(data_by_wav.items()):
        samples.sort(key=lambda item: item[0])
        if not samples:
            continue

        times = np.array([item[0] for item in samples], dtype=np.float64)
        levels = np.array([item[1] for item in samples], dtype=np.float64)

        cumulative_times.extend(times.tolist())
        cumulative_levels.extend(levels.tolist())

    if not cumulative_times:
        return None

    # ✅ ordenar por tiempo real
    combined = list(zip(cumulative_times, cumulative_levels))
    combined.sort(key=lambda x: x[0])
    cumulative_times, cumulative_levels = zip(*combined)

    # ✅ detectar gaps y meter NaN (muy importante)
    clean_times = []
    clean_levels = []

    for i in range(len(cumulative_times)):
        if i > 0:
            gap = cumulative_times[i] - cumulative_times[i - 1]
            if gap > 15:  # ajusta según window_seconds
                clean_times.append(datetime.datetime.fromtimestamp(cumulative_times[i]))
                clean_levels.append(float("nan"))

        clean_times.append(datetime.datetime.fromtimestamp(cumulative_times[i]))
        clean_levels.append(cumulative_levels[i])

    dates = clean_times
    levels = clean_levels

    fig, ax = plt.subplots(figsize=(10, 4), constrained_layout=True)

    ax.plot(dates, levels, marker="o", linestyle="-", linewidth=1, color="#0056b3")

    # ✅ formato eje X
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    fig.autofmt_xdate()

    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("SPL (dB)")
    ax.set_title(title)
    ax.grid(True, alpha=0.4)

    fig.savefig(output_path, dpi=150)

    try:
        os.chmod(output_path, 0o777)
    except OSError:
        pass

    plt.close(fig)
    return output_path

def plot_combined_spl_timeseriesold(rows, output_path, title="Combined SPL Time Series"):
    import datetime
    import matplotlib.dates as mdates

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    if not rows:
        return None

    data_by_wav = {}


    # insertar NaN si hay gaps grandes (>2x ventana por ejemplo)
    clean_times = []
    clean_levels = []

    for i in range(len(cumulative_times)):
        if i > 0:
            gap = cumulative_times[i] - cumulative_times[i - 1]
            if gap > 15:  # segundos (ajusta según ventana)
                clean_times.append(datetime.datetime.fromtimestamp(cumulative_times[i]))
                clean_levels.append(np.nan)

        clean_times.append(datetime.datetime.fromtimestamp(cumulative_times[i]))
        clean_levels.append(cumulative_levels[i])

    dates = clean_times
    cumulative_levels = clean_levels
    for wav, time_s, spl_db in rows:
        data_by_wav.setdefault(wav, []).append((float(time_s), float(spl_db)))

    cumulative_times = []
    cumulative_levels = []

    # 🔹 ya NO concatenamos
    for wav, samples in sorted(data_by_wav.items()):
        samples.sort(key=lambda item: item[0])
        if not samples:
            continue

        times = np.array([item[0] for item in samples], dtype=np.float64)
        levels = np.array([item[1] for item in samples], dtype=np.float64)

        cumulative_times.extend(times.tolist())
        cumulative_levels.extend(levels.tolist())

    if not cumulative_times:
        return None

    # ✅ ordenar todo por tiempo real
    combined = list(zip(cumulative_times, cumulative_levels))
    combined.sort(key=lambda x: x[0])
    cumulative_times, cumulative_levels = zip(*combined)

    # ✅ convertir a datetime
    dates = [datetime.datetime.fromtimestamp(t, tz=datetime.timezone.utc) for t in cumulative_times]

    fig, ax = plt.subplots(figsize=(10, 4), constrained_layout=True)

    ax.plot(dates, cumulative_levels, marker="o", linestyle="-", linewidth=1, color="#0056b3")

    # ✅ formato bonito del eje X
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    fig.autofmt_xdate()

    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel("SPL (dB)")
    ax.set_title(title)
    ax.grid(True, alpha=0.4)

    fig.savefig(output_path, dpi=150)

    try:
        os.chmod(output_path, 0o777)
    except OSError:
        pass

    plt.close(fig)
    return output_path
def plot_combined_spl_timeseriesold(rows, output_path, title="Combined SPL Time Series"):
    """Plot combined SPL time series from multiple WAV files as a concatenated series."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    if not rows:
        return None

    data_by_wav = {}
    for wav, time_s, spl_db in rows:
        data_by_wav.setdefault(wav, []).append((float(time_s), float(spl_db)))

    cumulative_times = []
    cumulative_levels = []
    current_offset = 0.0
    sorted_wavs = sorted(data_by_wav.items())

    for wav, samples in sorted_wavs:
        samples.sort(key=lambda item: item[0])
        if not samples:
            continue
        times = np.array([item[0] for item in samples], dtype=np.float64)
        levels = np.array([item[1] for item in samples], dtype=np.float64)
       
        cumulative_times.extend(times.tolist())
        #cumulative_times.extend((times + current_offset).tolist())
        cumulative_levels.extend(levels.tolist())
        #current_offset += times[-1] if times.size else 0.0

    if not cumulative_times:
        return None

    fig, ax = plt.subplots(figsize=(10, 4), constrained_layout=True)
    #ax.plot(cumulative_times, cumulative_levels, marker="o", linestyle="-", linewidth=1, color="#0056b3")
    
    import datetime

    dates = [datetime.datetime.fromtimestamp(t, tz=datetime.timezone.utc) for t in cumulative_times]

    ax.plot(dates, cumulative_levels, marker="o", linestyle="-", linewidth=1, color="#0056b3")
    fig.autofmt_xdate()

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("SPL (dB)")
    ax.set_title(title)
    ax.grid(True, alpha=0.4)
    fig.savefig(output_path, dpi=150)
    try:
        os.chmod(output_path, 0o777)
    except OSError:
        pass
    plt.close(fig)
    return output_path


def build_hydromoth_combined_results(
    folder_path,
    hydromoth_results,
    include_spectrograms=True,
    band_frequencies=(63, 125, 2000),
    p_ref=1.0,
):
    resultados_dir = os.path.join(os.path.dirname(folder_path), "resultados")
    os.makedirs(resultados_dir, exist_ok=True)

    all_spl_csv = os.path.join(resultados_dir, "all_spl_timeseries_global.csv")
    band_csvs = {
        int(freq): os.path.join(resultados_dir, f"all_spl_timeseries_{int(freq)}Hz.csv")
        for freq in band_frequencies
    }

    global_rows = []
    band_rows = {freq: [] for freq in band_csvs}
    spectrograms = []
    wav_files_info = []
    all_eu_indicators = []

    band_name_map = {
        63: "63Hz",
        125: "125Hz",
        2000: "2kHz",
    }

    for result in hydromoth_results:
        wav_name = result.get("wav_file") or os.path.basename(result.get("wav_path", ""))
        sample_rate = result.get("sample_rate")
        duration = result.get("duration_seconds")
        wav_path = result.get("wav_path")
        size_mb = None
        if wav_path and os.path.isfile(wav_path):
            try:
                size_mb = os.path.getsize(wav_path) / (1024 * 1024)
            except OSError:
                size_mb = None

        wav_files_info.append(
            {
                "name": wav_name,
                "size_mb": size_mb,
                "duration_s": float(duration) if duration is not None else None,
                "sample_rate": sample_rate,
            }
        )

        time_series = result.get("time_series", {})
        times = np.asarray(time_series.get("times", []), dtype=np.float64)
        overall_levels = np.asarray(time_series.get("overall_levels", []), dtype=np.float64)

        for time_s, level in zip(times.tolist(), overall_levels.tolist()):
            global_rows.append((wav_name, f"{time_s:.6f}", f"{level:.6f}"))

        for freq, csv_rows in band_rows.items():
            band_key = band_name_map.get(int(freq), f"{int(freq)}Hz")
            band_levels = np.asarray(time_series.get("band_levels", {}).get(band_key, []), dtype=np.float64)
            for time_s, level in zip(times.tolist(), band_levels.tolist()):
                if np.isnan(level):
                    continue
                csv_rows.append((wav_name, f"{time_s:.6f}", f"{level:.6f}"))

        if include_spectrograms and result.get("spectrogram_png"):
            spectrograms.append(result["spectrogram_png"])

        # Calculate EU indicators from pressure signal
        pressure_signal = result.get("signal")
        if pressure_signal is not None and sample_rate is not None:
            try:
                indicators = eu_noise_indicators(pressure_signal, sample_rate, p_ref=p_ref, window_seconds=10.0)
                all_eu_indicators.append(indicators)
            except Exception as e:
                logger.warning("Error calculating EU indicators for %s: %s", wav_name, e)

    save_combined_spl_csv(global_rows, all_spl_csv)
    for freq, csv_path in band_csvs.items():
        save_combined_spl_csv(band_rows[freq], csv_path)

    all_spl_plot = os.path.join(resultados_dir, "all_spl_timeseries_global.png")
    band_plots = {}
    all_spl_plot = plot_combined_spl_timeseries(
        global_rows,
        all_spl_plot,
        title="SPL global combinado",
    )
    for freq, csv_path in band_csvs.items():
        plot_path = os.path.join(resultados_dir, f"all_spl_timeseries_{freq}Hz.png")
        band_plots[freq] = plot_combined_spl_timeseries(
            band_rows[freq],
            plot_path,
            title=f"SPL combinado banda {freq} Hz",
        )

    # Aggregate EU indicators for HydroMoth
    combined_eu_indicators = None
    eu_compliance = None
    if all_eu_indicators:
        combined_eu_indicators = {
            "spl_broad_band": max(ind["spl_broad_band"] for ind in all_eu_indicators),
            "spl_low_freq": max(ind["spl_low_freq"] for ind in all_eu_indicators),
            "peak_pressure_db": max(ind["peak_pressure_db"] for ind in all_eu_indicators),
            "noise_type": "mixed" if any(ind["is_impulsive"] for ind in all_eu_indicators) else "continuous",
            "sel_mean": np.mean([ind["sel_mean"] for ind in all_eu_indicators]),
            "is_impulsive": any(ind["is_impulsive"] for ind in all_eu_indicators),
        }
        eu_compliance = evaluate_eu_compliance(combined_eu_indicators)

    return {
        "num_wavs": len(hydromoth_results),
        "all_spl_csv": all_spl_csv,
        "band_csvs": band_csvs,
        "all_spl_plot": all_spl_plot,
        "band_plots": band_plots,
        "spectrograms": list(dict.fromkeys(spectrograms)),
        "combined_counts": {
            "global": len(global_rows),
            **{freq: len(rows) for freq, rows in band_rows.items()},
        },
        "generation_time": None,
        "wav_files_info": wav_files_info,
        "include_spectrograms": include_spectrograms,
        "eu_compliance": eu_compliance,
        "eu_indicators": combined_eu_indicators,
    }


def compute_spl_statistics(levels):
    """Compute statistics for SPL levels."""
    return {
        "mean": float(np.mean(levels)),
        "std": float(np.std(levels)),
        "min": float(np.min(levels)),
        "max": float(np.max(levels)),
        "count": int(len(levels)),
    }


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


def save_combined_spl_csv(rows, csv_path):
    output_dir = os.path.dirname(csv_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["wav", "time_s", "spl_db"])
        writer.writerows(rows)
    try:
        os.chmod(csv_path, 0o777)
    except OSError:
        pass


def generate_report_story(track_results, combined_results=None, title="Audio Analysis Report"):
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 12))

    # Add generation time and file info at the beginning
    if combined_results is not None:
        
            # --- Analysis configuration table ---
        config = combined_results.get("analysis_config")

        if config:
            story.append(Paragraph("Parámetros del análisis:", styles["Heading2"]))
            story.append(Spacer(1, 6))

            config_rows = [["Parámetro", "Valor"]]

            for key, value in config.items():
                if isinstance(value, (list, tuple)):
                    value_str = ", ".join(str(v) for v in value)
                elif value is None:
                    value_str = "None"
                else:
                    value_str = str(value)

                config_rows.append([key, value_str])

            config_table = Table(config_rows, colWidths=[180, 220])
            config_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ]))

            story.append(config_table)
            story.append(Spacer(1, 12))
                
            
        
        if combined_results.get("generation_time"):
            story.append(Paragraph(f"<b>Fecha y hora de generación:</b> {combined_results['generation_time']}", styles["Normal"]))
            story.append(Spacer(1, 6))

        story.append(Paragraph("Información de archivos analizados:", styles["Heading2"]))
        story.append(Spacer(1, 6))

        wav_files = combined_results.get("wav_files_info", [])
        if wav_files:
            file_info_rows = [["Archivo", "Duración (s)", "Tamaño (MB)", "Frecuencia (Hz)"]]
            for info in wav_files:
                duration_str = f"{info['duration_s']:.2f}" if info.get('duration_s') is not None else "N/A"
                size_str = f"{info['size_mb']:.2f}" if info.get('size_mb') is not None else "N/A"
                sample_rate_str = str(info['sample_rate']) if info.get('sample_rate') is not None else "N/A"
                file_info_rows.append([
                    info["name"],
                    duration_str,
                    size_str,
                    sample_rate_str,
                ])
            file_table = Table(file_info_rows)
            file_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(file_table)
            story.append(Spacer(1, 12))

        # Add HydroMoth metadata table if available
        if combined_results.get("device_type") == "hydromoth" and combined_results.get("hydromoth_results"):
            story.append(Paragraph("Metadatos del Dispositivo HydroMoth:", styles["Heading2"]))
            story.append(Spacer(1, 6))
            
            hydromoth_data = combined_results["hydromoth_results"]
            metadata_rows = [["Archivo", "Fecha/Hora UTC", "Batería (V)", "Temperatura (°C)", "Nº Serie", "Duración (s)"]]
            
            for result in hydromoth_data:
                if "metadata" in result:
                    metadata = result["metadata"]
                    filename = result.get("wav_file", "N/A")
                    timestamp = metadata.get("timestamp", "N/A")
                    battery = metadata.get("battery_v", "N/A")
                    temperature = metadata.get("temperature_c", "N/A")
                    serial = metadata.get("serial_number", "N/A")
                    duration = result.get("duration_seconds", "N/A")
                    
                    # Format values
                    timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S") if hasattr(timestamp, 'strftime') else str(timestamp)
                    battery_str = f"{battery:.2f}" if isinstance(battery, (int, float)) else str(battery)
                    temp_str = f"{temperature:.1f}" if isinstance(temperature, (int, float)) else str(temperature)
                    duration_str = f"{duration:.1f}" if isinstance(duration, (int, float)) else str(duration)
                    
                    metadata_rows.append([filename, timestamp_str, battery_str, temp_str, serial, duration_str])
            
            metadata_table = Table(metadata_rows)
            metadata_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.lightblue),
                ("GRID", (0, 0), (-1, -1), 1, colors.black),
            ]))
            story.append(metadata_table)
            story.append(Spacer(1, 12))

    if combined_results is not None:
        story.append(Paragraph("Análisis combinado de todos los WAV", styles["Heading1"]))
        story.append(Spacer(1, 12))

        story.append(Paragraph(f"Archivos totales analizados: {combined_results.get('num_wavs', 0)}", styles["Normal"]))
        story.append(Paragraph(
            f"Puntos SPL global combinados: {combined_results.get('combined_counts', {}).get('global', 0)}",
            styles["Normal"],
        ))
        story.append(Spacer(1, 12))

        if combined_results.get("all_spl_plot"):
            story.append(Paragraph("SPL global combinado:", styles["Heading2"]))
            story.append(Image(combined_results["all_spl_plot"], width=400, height=200))
            story.append(Spacer(1, 12))

        for freq, plot_path in combined_results.get("band_plots", {}).items():
            if plot_path:
                story.append(Paragraph(f"SPL combinado banda {freq} Hz:", styles["Heading2"]))
                story.append(Image(plot_path, width=400, height=200))
                story.append(Spacer(1, 12))
                story.append(Paragraph(
                    f"Puntos combinados banda {freq} Hz: {combined_results.get('combined_counts', {}).get(freq, 0)}",
                    styles["Normal"],
                ))
                story.append(Spacer(1, 6))

        if combined_results.get("all_spl_csv"):
            story.append(Paragraph("CSV agregado global:", styles["Heading3"]))
            story.append(Paragraph(combined_results["all_spl_csv"], styles["Normal"]))
            story.append(Spacer(1, 6))

        if combined_results.get("band_csvs"):
            story.append(Paragraph("CSV agregados por banda:", styles["Heading3"]))
            for freq, csv_path in combined_results["band_csvs"].items():
                story.append(Paragraph(f"{freq} Hz: {csv_path}", styles["Normal"]))
            story.append(Spacer(1, 12))

        # Add MSFD D11 compliance table
        if combined_results.get("eu_compliance"):
            story.append(PageBreak())
            story.append(Paragraph("Conformidad con Directiva Europea (MSFD D11)", styles["Heading1"]))
            story.append(Spacer(1, 12))
            
            eu_comp = combined_results["eu_compliance"]
            
            # Compliance table
            rows = [
                ["Indicador", "Valor (dB)", "Umbral (dB)", "Exceso (dB)", "Estado"],
                [
                    "Ruido Continuo 10Hz-48kHz",
                    f"{eu_comp['continuous_broad_db']:.2f}",
                    f"{eu_comp['continuous_broad_threshold']:.2f}",
                    f"{eu_comp['continuous_broad_excess']:.2f}",
                    "✓ Conforme" if eu_comp['continuous_broad_compliant'] else "✗ No conforme",
                ],
                [
                    "Ruido Continuo 10Hz-100Hz",
                    f"{eu_comp['continuous_low_db']:.2f}",
                    f"{eu_comp['continuous_low_threshold']:.2f}",
                    f"{eu_comp['continuous_low_excess']:.2f}",
                    "✓ Conforme" if eu_comp['continuous_low_compliant'] else "✗ No conforme",
                ],
                [
                    "Ruido Impulsivo (Presión Pico)",
                    f"{eu_comp['impulsive_db']:.2f}",
                    f"{eu_comp['impulsive_threshold']:.2f}",
                    f"{eu_comp['impulsive_excess']:.2f}",
                    "✓ Conforme" if eu_comp['impulsive_compliant'] else "✗ No conforme",
                ],
            ]
            
            table = Table(rows, colWidths=[150, 80, 80, 80, 100])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4788")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.beige, colors.lightgrey]),
                    ]
                )
            )
            story.append(table)
            story.append(Spacer(1, 12))
            
            # Overall status
            overall_status = "✓ CONFORME CON MSFD D11" if eu_comp['overall_compliant'] else "✗ NO CONFORME CON MSFD D11"
            status_color = colors.HexColor("#00AA00") if eu_comp['overall_compliant'] else colors.HexColor("#DD0000")
            status_para = Paragraph(
                f"<font color='{status_color.hexval()}' size=14><b>{overall_status}</b></font>",
                styles["Normal"]
            )
            story.append(status_para)
            story.append(Spacer(1, 12))
            
            # Noise type
            noise_type_text = "Impulsivo (corta duración, eventos)" if eu_comp['noise_type'] == 'impulsive' else "Continuo (tráfico, fuentes sostenidas)"
            story.append(Paragraph(f"Tipo de ruido detectado: <b>{noise_type_text}</b>", styles["Normal"]))
            story.append(Spacer(1, 12))

        # Add spectrograms section
        spectrograms = combined_results.get("spectrograms", [])
        if spectrograms:
            story.append(PageBreak())
            story.append(Paragraph("Espectrogramas individuales:", styles["Heading1"]))
            story.append(Spacer(1, 12))
            for spec_path in spectrograms:
                if os.path.isfile(spec_path):
                    wav_name = os.path.splitext(os.path.basename(spec_path))[0].replace("_spectrogram", "")
                    story.append(Paragraph(f"Espectrograma: {wav_name}", styles["Heading2"]))
                    story.append(Image(spec_path, width=450, height=250))
                    story.append(Spacer(1, 12))

        return story

    # Fallback: individual file summary when no combined results are provided
    for item in track_results:
        story.append(Paragraph(f"Archivo: {item['wav_path']}", styles["Heading2"]))
        story.append(Paragraph(f"Sample rate: {item['sample_rate']} Hz", styles["Normal"]))
        story.append(Spacer(1, 6))

        # Overall SPL statistics
        story.append(Paragraph("Estadísticas SPL Global:", styles["Heading3"]))
        overall_stats = item.get("overall_stats", {})
        rows = [
            ["Métrica", "Valor"],
            ["SPL Global (dB)", f"{overall_stats.get('mean', 0):.2f}"],
            ["Desv. Est. (dB)", f"{overall_stats.get('std', 0):.2f}"],
            ["Mínimo (dB)", f"{overall_stats.get('min', 0):.2f}"],
            ["Máximo (dB)", f"{overall_stats.get('max', 0):.2f}"],
        ]
        table = Table(rows, colWidths=[150, 150])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d3d3d3")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 12))

        # Third-octave bands
        if item.get("third_octave") is not None:
            story.append(Paragraph("SPL en bandas de tercio de octava:", styles["Heading3"]))
            rows = [["Centro (Hz)", "SPL (dB)"]]
            rows += [[f"{fc:.1f}", f"{level:.2f}"] for fc, level in item["third_octave"]]
            table = Table(rows, colWidths=[80, 80])
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d3d3d3")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ]
                )
            )
            story.append(table)
            story.append(Spacer(1, 12))

        # Spectrogram
        story.append(Paragraph("Espectrograma:", styles["Heading3"]))
        story.append(Image(item["spectrogram_png"], width=400, height=200))
        story.append(Spacer(1, 12))

        # SPL time series (20s)
        if item.get("times") is not None and item.get("spl_timeseries_png") is not None:
            story.append(Paragraph("Serie temporal de SPL (ventana 20s):", styles["Heading3"]))
            story.append(Image(item["spl_timeseries_png"], width=400, height=200))
            story.append(Spacer(1, 12))

        # Band-specific time series (10s windows)
        if item.get("band_timeseries", {}).get("63Hz"):
            story.append(Paragraph("Series temporales de SPL por banda (ventana 10s):", styles["Heading3"]))
            for freq, band_data in item.get("band_timeseries", {}).items():
                if band_data.get("png"):
                    story.append(Paragraph(f"Banda {freq}:", styles["Normal"]))
                    story.append(Image(band_data["png"], width=400, height=150))
                    if band_data.get("stats"):
                        stats = band_data["stats"]
                        stat_text = f"Media: {stats['mean']:.2f} dB | Std: {stats['std']:.2f} dB | Min: {stats['min']:.2f} dB | Max: {stats['max']:.2f} dB"
                        story.append(Paragraph(stat_text, styles["Normal"]))
                    story.append(Spacer(1, 6))

        story.append(PageBreak())

    return story


def generate_pdf_report(pdf_path, track_results, combined_results=None, title="Audio Analysis Report"):
    """Generate a PDF report containing analysis results."""
    output_dir = os.path.dirname(pdf_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    story = generate_report_story(track_results, combined_results=combined_results, title=title)
    doc.build(story)
    try:
        os.chmod(pdf_path, 0o777)
    except OSError:
        pass
    return pdf_path
def analyze_folder_and_generate_report(
    folder_path,
    pdf_path=None,
    centers=None,
    band_frequencies=(63, 125, 2000),
    window_seconds=20.0,
    hop_seconds=None,
    band_window_seconds=10.0,
    nperseg=1024,
    noverlap=None,
    cmap="viridis",
    p_ref=20e-6,
    verbose=False,
    include_spectrograms=True,
    device_type="generic",
    hydromoth_results=None,
):
    folder_path = os.fspath(folder_path)

    if pdf_path is None:
        parent_dir = os.path.dirname(folder_path)
        resultados_dir = os.path.join(parent_dir, "resultados")
        os.makedirs(resultados_dir, exist_ok=True)
        pdf_path = os.path.join(resultados_dir, "audio_analysis_report.pdf")

    logger.info("Generando PDF desde datos agregados: %s", pdf_path)

    # =========================================================
    # ✅ CASO HYDROMOTH
    # =========================================================
    if device_type == "hydromoth":

        if hydromoth_results is None:
            from hydromoth_processor import process_hydromoth_folder

            hydromoth_results = process_hydromoth_folder(
                folder_path,
                window_seconds=window_seconds,
            )

        combined_results = build_hydromoth_combined_results(
            folder_path,
            hydromoth_results,
            include_spectrograms=include_spectrograms,
            band_frequencies=band_frequencies,
        )

        from datetime import datetime
        combined_results["generation_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        combined_results["device_type"] = device_type
        combined_results["hydromoth_results"] = hydromoth_results

        # ✅ CONFIGURACIÓN DEL ANÁLISIS (FIX IMPORTANTE)
        combined_results["analysis_config"] = {
            "device_type": device_type,
            "p_ref": p_ref,
            "window_seconds": window_seconds,
            "hop_seconds": hop_seconds,
            "band_window_seconds": band_window_seconds,
            "nperseg": nperseg,
            "noverlap": noverlap,
            "cmap": cmap,
            "band_frequencies": band_frequencies,
            "vpp": 3.0,
            "sensitivity_db": 5.0,
            "gain_db": 0,
            "time_reference": "UTC",
            "time_axis": "absolute (UTC)",
        }

        logger.info("Generando PDF de resultado HydroMoth...")
        generate_pdf_report(pdf_path, [], combined_results=combined_results)
        logger.info("PDF generado en: %s", pdf_path)
        return pdf_path

    # =========================================================
    # ✅ CASO GENÉRICO
    # =========================================================

    parent_dir = os.path.dirname(folder_path)
    resultados_dir = os.path.join(parent_dir, "resultados")

    all_spl_csv = os.path.join(resultados_dir, "all_spl_timeseries_global.csv")
    band_csvs = {
        int(freq): os.path.join(resultados_dir, f"all_spl_timeseries_{int(freq)}Hz.csv")
        for freq in band_frequencies
    }

    global_rows = []
    band_rows = {freq: [] for freq in band_csvs}


    if os.path.isfile(all_spl_csv):
        with open(all_spl_csv, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                global_rows.append((row['wav'], row['time_s'], row['spl_db']))

    for freq, csv_path in band_csvs.items():
        if os.path.isfile(csv_path):
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    band_rows[freq].append((row['wav'], row['time_s'], row['spl_db']))


    wav_entries = list(load_wav_folder(folder_path))
    total_wavs = len(wav_entries)


    # ✅ EU INDICATORS
    all_eu_indicators = []
    for wav_path, sr, signal in wav_entries:
        try:
            indicators = eu_noise_indicators(signal, sr, p_ref=p_ref, window_seconds=window_seconds)
            all_eu_indicators.append(indicators)
        except Exception as e:
            logger.warning("Error calculating EU indicators for %s: %s", wav_path, e)


    if all_eu_indicators:
        combined_eu_indicators = {
            "spl_broad_band": max(ind["spl_broad_band"] for ind in all_eu_indicators),
            "spl_low_freq": max(ind["spl_low_freq"] for ind in all_eu_indicators),
            "peak_pressure_db": max(ind["peak_pressure_db"] for ind in all_eu_indicators),
            "noise_type": "mixed" if any(ind["is_impulsive"] for ind in all_eu_indicators) else "continuous",
            "sel_mean": np.mean([ind["sel_mean"] for ind in all_eu_indicators]),
            "is_impulsive": any(ind["is_impulsive"] for ind in all_eu_indicators),
        }
        eu_compliance = evaluate_eu_compliance(combined_eu_indicators)
    else:
        eu_compliance = None


    # ✅ INFO ARCHIVOS
    wav_files_info = []
    for wav_path, sr, signal in wav_entries:
        wav_files_info.append({
            "name": os.path.basename(wav_path),
            "size_mb": os.path.getsize(wav_path) / (1024 * 1024),
            "duration_s": len(signal) / sr,
            "sample_rate": sr,
        })


    from datetime import datetime
    generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    combined_results = {
        "num_wavs": total_wavs,
        "all_spl_csv": all_spl_csv,
        "band_csvs": band_csvs,
        "all_spl_plot": None,
        "band_plots": {},
        "spectrograms": [],
        "combined_counts": {
            "global": len(global_rows),
            **{freq: len(rows) for freq, rows in band_rows.items()},
        },
        "eu_compliance": eu_compliance,
        "generation_time": generation_time,
        "wav_files_info": wav_files_info,
        "include_spectrograms": include_spectrograms,
        "device_type": device_type,
        "hydromoth_results": hydromoth_results,

        # ✅ CONFIGURACIÓN DEL ANÁLISIS
        "analysis_config": {
            "device_type": device_type,
            "p_ref": p_ref,
            "window_seconds": window_seconds,
            "hop_seconds": hop_seconds,
            "band_window_seconds": band_window_seconds,
            "nperseg": nperseg,
            "noverlap": noverlap,
            "cmap": cmap,
            "band_frequencies": band_frequencies,
            "time_axis": "relative (seconds)",
        },
    }


    # ✅ generar plots
    all_spl_plot = os.path.join(resultados_dir, "all_spl_timeseries_global.png")

    combined_results["all_spl_plot"] = plot_combined_spl_timeseries(
        global_rows,
        all_spl_plot,
        title="SPL global combinado",
    )

    for freq, rows in band_rows.items():
        plot_path = os.path.join(resultados_dir, f"all_spl_timeseries_{freq}Hz.png")
        combined_results["band_plots"][freq] = plot_combined_spl_timeseries(
            rows,
            plot_path,
            title=f"SPL combinado banda {freq} Hz",
        )


    logger.info("Generando PDF final...")
    generate_pdf_report(pdf_path, [], combined_results=combined_results)
    logger.info("PDF generado en: %s", pdf_path)

    return pdf_path

def analyze_folder_and_generate_report_old(
    folder_path,
    pdf_path=None,
    centers=None,
    band_frequencies=(63, 125, 2000),
    window_seconds=20.0,
    hop_seconds=None,
    band_window_seconds=10.0,
    nperseg=1024,
    noverlap=None,
    cmap="viridis",
    p_ref=20e-6,
    verbose=False,
    include_spectrograms=True,
    device_type="generic",
    hydromoth_results=None,
):
    """Generate PDF report using existing aggregated CSV data."""
    folder_path = os.fspath(folder_path)
    if pdf_path is None:
        parent_dir = os.path.dirname(folder_path)
        resultados_dir = os.path.join(parent_dir, "resultados")
        os.makedirs(resultados_dir, exist_ok=True)
        pdf_path = os.path.join(resultados_dir, "audio_analysis_report.pdf")

    logger.info("Generando PDF desde datos agregados: %s", pdf_path)
    
    if device_type == "hydromoth":
        if hydromoth_results is None:
            from hydromoth_processor import process_hydromoth_folder

            hydromoth_results = process_hydromoth_folder(
                folder_path,
                window_seconds=window_seconds,
            )

        combined_results = build_hydromoth_combined_results(
            folder_path,
            hydromoth_results,
            include_spectrograms=include_spectrograms,
            band_frequencies=band_frequencies,
        )

        from datetime import datetime
        combined_results["generation_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        combined_results["device_type"] = device_type
        combined_results["hydromoth_results"] = hydromoth_results
        #combined_results["eu_compliance"] = None

        logger.info("Generando PDF de resultado HydroMoth...")
        generate_pdf_report(pdf_path, [], combined_results=combined_results)
        logger.info("PDF generado en: %s", pdf_path)
        return pdf_path

    parent_dir = os.path.dirname(folder_path)
    resultados_dir = os.path.join(parent_dir, "resultados")
    all_spl_csv = os.path.join(resultados_dir, "all_spl_timeseries_global.csv")
    band_csvs = {
        int(freq): os.path.join(
            resultados_dir,
            f"all_spl_timeseries_{int(freq)}Hz.csv",
        )
        for freq in band_frequencies
    }

    global_rows = []
    band_rows = {freq: [] for freq in band_csvs}

    if os.path.isfile(all_spl_csv):
        with open(all_spl_csv, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                global_rows.append((row['wav'], row['time_s'], row['spl_db']))

    for freq, csv_path in band_csvs.items():
        if os.path.isfile(csv_path):
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    band_rows[freq].append((row['wav'], row['time_s'], row['spl_db']))

    wav_entries = list(load_wav_folder(folder_path))
    total_wavs = len(wav_entries)

    # Calculate combined EU indicators across all files
    all_eu_indicators = []
    for wav_path, sr, signal in wav_entries:
        try:
            indicators = eu_noise_indicators(signal, sr, p_ref=p_ref, window_seconds=window_seconds)
            all_eu_indicators.append(indicators)
        except Exception as e:
            logger.warning("Error calculating EU indicators for %s: %s", wav_path, e)

    # Aggregate EU indicators (use maximum values as conservative estimate)
    combined_eu_indicators = None
    if all_eu_indicators:
        combined_eu_indicators = {
            "spl_broad_band": max(ind["spl_broad_band"] for ind in all_eu_indicators),
            "spl_low_freq": max(ind["spl_low_freq"] for ind in all_eu_indicators),
            "peak_pressure_db": max(ind["peak_pressure_db"] for ind in all_eu_indicators),
            "noise_type": "mixed" if any(ind["is_impulsive"] for ind in all_eu_indicators) else "continuous",
            "sel_mean": np.mean([ind["sel_mean"] for ind in all_eu_indicators]),
            "is_impulsive": any(ind["is_impulsive"] for ind in all_eu_indicators),
        }
        eu_compliance = evaluate_eu_compliance(combined_eu_indicators)
    else:
        eu_compliance = None

    # Collect spectrograms from resultados folder
    spectrograms = []
    if os.path.isdir(resultados_dir):
        import glob
        spectrogram_files = sorted(glob.glob(os.path.join(resultados_dir, "*_spectrogram.png")))
        spectrograms = spectrogram_files

    # Collect WAV file information
    wav_files_info = []
    for wav_path, sr, signal in wav_entries:
        wav_name = os.path.basename(wav_path)
        file_size = os.path.getsize(wav_path) / (1024 * 1024)  # Size in MB
        duration = len(signal) / sr  # Duration in seconds
        wav_files_info.append({
            "name": wav_name,
            "size_mb": file_size,
            "duration_s": duration,
            "sample_rate": sr,
        })

    # Get current date and time
    from datetime import datetime
    generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    combined_results = {
        "num_wavs": total_wavs,
        "all_spl_csv": all_spl_csv,
        "band_csvs": band_csvs,
        "all_spl_plot": None,
        "band_plots": {},
        "spectrograms": spectrograms if include_spectrograms else [],
        "combined_counts": {
            "global": len(global_rows),
            **{freq: len(rows) for freq, rows in band_rows.items()},
        },
        "eu_compliance": eu_compliance,
        "generation_time": generation_time,
        "wav_files_info": wav_files_info,
        "include_spectrograms": include_spectrograms,
        "device_type": device_type,
        "hydromoth_results": hydromoth_results,
    }



    combined_results["analysis_config"] = {
        "device_type": device_type,
        "p_ref": p_ref,
        "window_seconds": window_seconds,
        "hop_seconds": hop_seconds,
        "band_window_seconds": band_window_seconds,
        "nperseg": nperseg,
        "noverlap": noverlap,
        "cmap": cmap,
        "band_frequencies": band_frequencies,
    }

    if device_type == "hydromoth":
        combined_results["analysis_config"].update({
            "vpp": 3.0,
            "sensitivity_db": 5.0,
            "gain_db": 0,
            "time_reference": "UTC",
        })

    all_spl_plot = os.path.join(resultados_dir, "all_spl_timeseries_global.png")
    combined_results["all_spl_plot"] = plot_combined_spl_timeseries(
        global_rows,
        all_spl_plot,
        title="SPL global combinado",
    )

    for freq, rows in band_rows.items():
        plot_path = os.path.join(resultados_dir, f"all_spl_timeseries_{freq}Hz.png")
        combined_results["band_plots"][freq] = plot_combined_spl_timeseries(
            rows,
            plot_path,
            title=f"SPL combinado banda {freq} Hz",
        )

    logger.info("Generando PDF de resultado...")
    generate_pdf_report(pdf_path, [], combined_results=combined_results)
    logger.info("PDF generado en: %s", pdf_path)
    return pdf_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a PDF report from WAV analysis.")
    parser.add_argument("folder", help="Folder containing WAV files")
    parser.add_argument(
        "--out",
        default=None,
        help="Output PDF report path",
    )
    parser.add_argument(
        "--centers",
        default=None,
        help="Comma-separated third-octave center frequencies in Hz",
    )
    parser.add_argument(
        "--band-freqs",
        default="63,125,2000",
        help="Comma-separated band center frequencies for 10s window analysis (default: 63,125,2000)",
    )
    parser.add_argument(
        "--window",
        type=float,
        default=20.0,
        help="Window duration in seconds for SPL time series",
    )
    parser.add_argument(
        "--band-window",
        type=float,
        default=10.0,
        help="Window duration in seconds for band-specific SPL time series",
    )
    parser.add_argument(
        "--hop",
        type=float,
        default=None,
        help="Hop duration in seconds for SPL time series",
    )
    parser.add_argument("--nperseg", type=int, default=1024, help="Samples per segment for spectrogram")
    parser.add_argument("--noverlap", type=int, default=None, help="Overlap for spectrogram")
    parser.add_argument("--cmap", default="viridis", help="Colormap for spectrogram")
    parser.add_argument("--ref", type=float, default=20e-6, help="Reference pressure in Pa")
    parser.add_argument("--verbose", action="store_true", help="Show progress messages during report generation")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging for detailed tracing")
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO
    configure_logging(level=log_level)

    centers = None
    if args.centers:
        centers = [float(x.strip()) for x in args.centers.split(",") if x.strip()]

    band_freqs = (63, 125, 2000)
    if args.band_freqs:
        band_freqs = tuple(float(x.strip()) for x in args.band_freqs.split(",") if x.strip())

    pdf_path = analyze_folder_and_generate_report(
        args.folder,
        pdf_path=args.out,
        centers=centers,
        band_frequencies=band_freqs,
        window_seconds=args.window,
        hop_seconds=args.hop,
        band_window_seconds=args.band_window,
        nperseg=args.nperseg,
        noverlap=args.noverlap,
        cmap=args.cmap,
        p_ref=args.ref,
        verbose=args.verbose or args.debug,
    )
    print(f"PDF report generated at: {pdf_path}")
