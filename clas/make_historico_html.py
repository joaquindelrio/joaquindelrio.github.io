import os
import argparse
import pandas as pd
from datetime import datetime, timedelta, timezone

import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio

def load_transmission_history(xlsx_path):
    df = pd.read_excel(xlsx_path)

    cols = ['imei', '_servidor_recibido', 'pila', 'latitude', 'longitude']
    cols_present = [c for c in cols if c in df.columns]
    df = df[cols_present].copy()

    df["_servidor_recibido"] = pd.to_datetime(df["_servidor_recibido"], errors="coerce", utc=True).dt.tz_localize(None)
    df["imei"] = df["imei"].astype(str).str.replace(".0", "", regex=False)
    return df

def build_figures(df, hours=None):
    df = df.dropna(subset=["imei", "_servidor_recibido"]).copy()
    df = df.sort_values(by=["imei", "_servidor_recibido"])

    now = datetime.now(timezone.utc).replace(tzinfo=None)

    if hours is not None:
        threshold = now - timedelta(hours=hours)
        df = df[df["_servidor_recibido"] >= threshold]

    # Intervalos
    df["Interval (min)"] = df.groupby("imei")["_servidor_recibido"].diff().dt.total_seconds() / 60
    df["Tipo"] = "normal"

    # fila "hasta ahora"
    filas_extra = []
    for device_id, grupo in df.groupby("imei"):
        ultimo_ts = grupo["_servidor_recibido"].max()
        intervalo = (now - ultimo_ts).total_seconds() / 60
        nueva = {
            "imei": device_id,
            "_servidor_recibido": now,
            "Interval (min)": intervalo,
            "Tipo": "hasta ahora",
            "pila": None,
            "latitude": None,
            "longitude": None,
        }
        filas_extra.append(nueva)

    if filas_extra:
        df = pd.concat([df, pd.DataFrame(filas_extra)], ignore_index=True)

    # Orden por último intervalo
    ultimos_intervalos = (
        df.groupby("imei")["_servidor_recibido"]
        .idxmax()
        .apply(lambda idx: df.loc[idx, "Interval (min)"])
    )
    imei_ordenados = ultimos_intervalos.sort_values(ascending=False).index.tolist()

    # FIG 1: Intervalos
    fig_interval = go.Figure()
    for dev_id in imei_ordenados:
        dev_df = df[df["imei"] == dev_id]
        fig_interval.add_trace(go.Scatter(
            x=dev_df["_servidor_recibido"],
            y=dev_df["Interval (min)"],
            mode="lines+markers",
            name=f"Dispositivo {dev_id}",
        ))
    fig_interval.update_layout(
        title="Intervalo entre transmisiones consecutivas",
        xaxis_title="Fecha y hora",
        yaxis_title="Intervalo (min)",
        height=420,
        showlegend=True,
    )

    # FIG 2: Pila
    fig_pila = go.Figure()
    for dev_id in imei_ordenados:
        dev_df = df[(df["imei"] == dev_id) & (df.get("pila").notna() if "pila" in df.columns else False)]
        if dev_df.empty:
            continue
        fig_pila.add_trace(go.Scatter(
            x=dev_df["_servidor_recibido"],
            y=dev_df["pila"],
            mode="lines+markers",
            name=f"Pila {dev_id}",
        ))
    fig_pila.update_layout(
        title="Evolución de la pila",
        xaxis_title="Fecha y hora",
        yaxis_title="Pila (mV)",
        height=420,
        showlegend=True,
    )

    # FIG 3: Mapa
    fig_map = go.Figure()
    if "latitude" in df.columns and "longitude" in df.columns:
        df_map = df.copy()
        df_map = df_map[(df_map["latitude"].notna()) & (df_map["longitude"].notna())]
        df_map = df_map[(df_map["latitude"] != 99) & (df_map["longitude"] != 99)]

        if not df_map.empty:
            colors = px.colors.qualitative.Safe
            color_map = {dev_id: colors[i % len(colors)] for i, dev_id in enumerate(imei_ordenados)}

            for dev_id in imei_ordenados:
                dev_df = df_map[df_map["imei"] == dev_id]
                if dev_df.empty:
                    continue
                fig_map.add_trace(go.Scattermap(
                    lat=dev_df["latitude"],
                    lon=dev_df["longitude"],
                    mode="markers+lines",
                    name=f"Dispositivo {dev_id}",
                    marker=dict(size=9, color=color_map[dev_id]),
                    text=[
                        f"IMEI: {row['imei']}<br>{row['_servidor_recibido']}<br>Pila: {row.get('pila')}"
                        for _, row in dev_df.iterrows()
                    ],
                ))

            fig_map.update_layout(
                map=dict(
                    style="open-street-map",
                    center={"lat": df_map["latitude"].mean(), "lon": df_map["longitude"].mean()},
                    zoom=6,
                ),
                map_style="open-street-map",
                title="Posición de los dispositivos",
                height=900,
                showlegend=True,
            )
        else:
            fig_map.update_layout(
                title="Posición de los dispositivos (sin datos válidos)",
                height=900,
                map=dict(style="open-street-map", zoom=2, center={"lat": 0, "lon": 0}),
            )

    return fig_interval, fig_pila, fig_map

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--hours", type=int, default=None, help="Filtra ultimas N horas (ej 24). Por defecto: todo.")
    args = ap.parse_args()

    df = load_transmission_history(args.xlsx)
    fig1, fig2, fig3 = build_figures(df, hours=args.hours)

    # HTML completo con 3 gráficos
    html_parts = []
    html_parts.append("<!doctype html><html><head><meta charset='utf-8'>")
    html_parts.append("<meta name='viewport' content='width=device-width, initial-scale=1'>")
    html_parts.append("<title>Histórico Telit</title></head><body style='font-family:Arial;margin:16px'>")
    html_parts.append(f"<h2>Histórico Telit</h2><div style='color:#555;margin-bottom:12px'>Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>")

    html_parts.append(pio.to_html(fig1, full_html=False, include_plotlyjs="cdn"))
    html_parts.append(pio.to_html(fig2, full_html=False, include_plotlyjs=False))
    html_parts.append(pio.to_html(fig3, full_html=False, include_plotlyjs=False))

    html_parts.append("</body></html>")

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))

if __name__ == "__main__":
    main()
