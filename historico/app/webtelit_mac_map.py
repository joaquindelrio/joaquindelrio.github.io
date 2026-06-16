import os
import pandas as pd
from datetime import datetime, timedelta, timezone
import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px


# === CARGAR HISTORIAL DE TRANSMISIONES DESDE EXCEL ===
def load_transmission_history():
    file_path = os.path.join(os.path.dirname(__file__), 'json_data.xlsx')
    df = pd.read_excel(file_path)

    columnas_necesarias = ['imei', '_servidor_recibido', 'pila', 'latitude', 'longitude']
    columnas_presentes = [c for c in columnas_necesarias if c in df.columns]
    df = df[columnas_presentes]

    df["_servidor_recibido"] = pd.to_datetime(df["_servidor_recibido"], utc=True).dt.tz_localize(None)
    df["imei"] = df["imei"].astype(str).str.replace(".0", "", regex=False)

    return df


# === DASHBOARD ===
def run_dashboard():
    df = load_transmission_history()
    df = df.sort_values(by=["imei", "_servidor_recibido"])
    df["Interval (min)"] = df.groupby("imei")["_servidor_recibido"].diff().dt.total_seconds() / 60
    df["Tipo"] = "normal"

    filas_extra = []
    for device_id, grupo in df.groupby("imei"):
        ultimo_ts = grupo["_servidor_recibido"].max()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        intervalo = (now - ultimo_ts).total_seconds() / 60
        nueva_fila = {
            "imei": device_id,
            "_servidor_recibido": now,
            "Interval (min)": intervalo,
            "Tipo": "hasta ahora",
            "pila": None
        }
        for col in df.columns:
            if col not in nueva_fila:
                nueva_fila[col] = None
        filas_extra.append(nueva_fila)

    df = pd.concat([df, pd.DataFrame(filas_extra)], ignore_index=True)

    app = dash.Dash(__name__)

    device_options = [{"label": "Todos", "value": "all"}] + [
        {"label": str(dev), "value": dev} for dev in sorted(df["imei"].dropna().unique())
    ]

    time_options = {
        "Últimas 3 horas": timedelta(hours=3),
        "Últimas 6 horas": timedelta(hours=6),
        "Últimas 24 horas": timedelta(hours=24),
        "Últimas 48 horas": timedelta(hours=48),
        "Todo": None
    }

    app.layout = html.Div([
        html.H1("Transmisiones Telit"),
        html.Div(f"Total de dispositivos: {df['imei'].nunique()}", style={'marginBottom': '10px'}),
        html.Div([
            html.Label("Selecciona un dispositivo:"),
            dcc.Dropdown(id="device-dropdown", options=device_options, value="all")
        ], style={'width': '48%', 'display': 'inline-block'}),
        html.Div([
            html.Label("Rango de tiempo:"),
            dcc.Dropdown(id="time-range-dropdown",
                         options=[{"label": k, "value": k} for k in time_options],
                         value="Todo")
        ], style={'width': '48%', 'display': 'inline-block'}),
        html.Div([
            html.Label("Intervalo mínimo para mostrar (min):"),
            dcc.Input(id='interval-threshold', type='number', value=0, step=1)
        ], style={'width': '48%', 'display': 'inline-block', 'marginTop': '10px'}),
        dcc.Graph(id="interval-graph"),
        dcc.Graph(id="pila-graph"),
        dcc.Graph(id="map-graph")
    ])

    # === CALLBACK PRINCIPAL ===
    @app.callback(
        [Output("interval-graph", "figure"),
         Output("pila-graph", "figure"),
         Output("map-graph", "figure")],
        [Input("device-dropdown", "value"),
         Input("time-range-dropdown", "value"),
         Input("interval-threshold", "value")]
    )
    def update_graphs(selected_device, selected_range, interval_threshold):
        try:
            filtered = df.copy()

            if time_options[selected_range]:
                threshold = datetime.now(timezone.utc).replace(tzinfo=None) - time_options[selected_range]
                filtered = filtered[filtered["_servidor_recibido"] >= threshold]

            if selected_device != "all":
                filtered = filtered[filtered["imei"] == selected_device]

            # === INTERVALOS ===
            fig_interval = go.Figure()
            ultimos_intervalos = (
                filtered.groupby("imei")["_servidor_recibido"]
                .idxmax()
                .apply(lambda idx: filtered.loc[idx, "Interval (min)"])
            )
            imei_ordenados = ultimos_intervalos.sort_values(ascending=False).index.tolist()

            for dev_id in imei_ordenados:
                dev_df = filtered[filtered["imei"] == dev_id]
                ultimo_valor = dev_df["Interval (min)"].dropna().iloc[-1] if not dev_df["Interval (min)"].dropna().empty else 0
                mostrar = (ultimo_valor <= interval_threshold)
                fig_interval.add_trace(go.Scatter(
                    x=dev_df["_servidor_recibido"],
                    y=dev_df["Interval (min)"],
                    mode='lines+markers',
                    name=f"Dispositivo {dev_id}",
                    visible=True if mostrar else 'legendonly'
                ))

            fig_interval.update_layout(
                title="Intervalo entre transmisiones consecutivas",
                xaxis_title="Fecha y hora",
                yaxis_title="Intervalo (minutos)",
                showlegend=True,
                height=400
            )

            # === PILA ===
            ultimos_pilas = {}
            for dev_id in filtered["imei"].dropna().unique():
                dev_df = filtered[(filtered["imei"] == dev_id) & (filtered["pila"].notna())]
                if not dev_df.empty:
                    ultimos_pilas[dev_id] = dev_df.sort_values("_servidor_recibido").iloc[-1]["pila"]

            imei_ordenados_pila = sorted(ultimos_pilas, key=ultimos_pilas.get, reverse=True)

            fig_pila = go.Figure()
            for dev_id in imei_ordenados_pila:
                dev_df = filtered[(filtered["imei"] == dev_id) & (filtered["pila"].notna())]
                ultimo_valor_intervalo = filtered[filtered["imei"] == dev_id]["Interval (min)"].dropna()
                mostrar = (not ultimo_valor_intervalo.empty and ultimo_valor_intervalo.iloc[-1] <= interval_threshold)
                fig_pila.add_trace(go.Scatter(
                    x=dev_df["_servidor_recibido"],
                    y=dev_df["pila"],
                    mode='lines+markers',
                    name=f"Pila {dev_id}",
                    visible=True if mostrar else 'legendonly'
                ))

            fig_pila.update_layout(
                title="Evolución de la pila",
                xaxis_title="Fecha y hora",
                yaxis_title="Nivel de pila (mV)",
                showlegend=True,
                height=400
            )

            # === MAPA ===
            df_map = filtered.copy()
            df_map = df_map[(df_map["latitude"] != 99) & (df_map["longitude"] != 99)]

            fig_map = go.Figure()

            if not df_map.empty:
                colors = px.colors.qualitative.Safe
                color_map = {dev_id: colors[i % len(colors)] for i, dev_id in enumerate(imei_ordenados)}

                for dev_id in imei_ordenados:
                    dev_df = df_map[df_map["imei"] == dev_id]
                    if not dev_df.empty:
                        fig_map.add_trace(go.Scattermap(

                            lat=dev_df["latitude"],
                            lon=dev_df["longitude"],
                            mode='markers+lines',
                            name=f"Dispositivo {dev_id}",
                            marker=dict(size=9, color=color_map[dev_id]),
                            text=[f"IMEI: {row['imei']}<br>{row['_servidor_recibido']}<br>Pila: {row['pila']}"
                                  for _, row in dev_df.iterrows()]
                        ))

                fig_map.update_layout(
                    map=dict(
                        style="open-street-map",
                        center={"lat": df_map["latitude"].mean(),
                                "lon": df_map["longitude"].mean()},
                        zoom=6,
                    ),
                    map_style="open-street-map",
                    title="Posición de los dispositivos",
                    height=1200,
                    showlegend=True
                )
            else:
                fig_map.update_layout(
                    title="Posición de los dispositivos (sin datos válidos)",
                    height=1200,
                    map=dict(style="open-street-map", zoom=2, center={"lat": 0, "lon": 0})
                )

            return fig_interval, fig_pila, fig_map

        except Exception as e:
            print("Error en update_graphs:", e)
            empty_fig = go.Figure()
            empty_fig.update_layout(title="Error al generar gráfico")
            return empty_fig, empty_fig, empty_fig


    # === CALLBACK DE SINCRONIZACIÓN MAPA/INTERVALO ===
    @app.callback(
        Output("map-graph", "figure", allow_duplicate=True),
        [Input("interval-graph", "relayoutData"),
         Input("interval-graph", "restyleData")],
        [State("interval-graph", "figure"),
         State("map-graph", "figure")],
        prevent_initial_call=True
    )
    def sync_map_with_interval(relayoutData, restyleData, fig_interval, fig_map):
        print("SYNC CALLBACK ACTIVADO", relayoutData, restyleData)

        ctx = dash.callback_context
        if not ctx.triggered or not fig_interval or "data" not in fig_interval:
            raise dash.exceptions.PreventUpdate

        # === Determinar rango de tiempo mostrado ===
        x_range = None
        if relayoutData and "xaxis.range[0]" in relayoutData:
            x_range = (
                pd.to_datetime(relayoutData["xaxis.range[0]"]),
                pd.to_datetime(relayoutData["xaxis.range[1]"])
            )
        else:
            try:
                layout_xaxis = fig_interval.get("layout", {}).get("xaxis", {})
                if "range" in layout_xaxis and len(layout_xaxis["range"]) == 2:
                    x_range = (
                        pd.to_datetime(layout_xaxis["range"][0]),
                        pd.to_datetime(layout_xaxis["range"][1])
                    )
            except Exception:
                x_range = None

        # === Determinar qué IMEIs están visibles ===
        visible_series = []
        for i, trace in enumerate(fig_interval["data"]):
            visible = trace.get("visible", True)
            if restyleData and len(restyleData) >= 2 and "visible" in restyleData[0]:
                if i in restyleData[1]:
                    visible = restyleData[0]["visible"][0]
            if visible not in ["legendonly", False]:
                imei = str(trace["name"]).replace("Dispositivo ", "").strip()
                if imei.endswith(".0"):
                    imei = imei[:-2]
                visible_series.append(imei)

        # === Filtrado del DataFrame ===
        df_visible = pd.DataFrame()
        for imei in visible_series:
            df_dev = df[df["imei"] == imei].copy()

            if x_range:
                df_dev_range = df_dev[
                    (df_dev["_servidor_recibido"] >= x_range[0]) &
                    (df_dev["_servidor_recibido"] <= x_range[1])
                ]
            else:
                df_dev_range = df_dev

            if df_dev_range.empty and x_range:
                df_dev_before = df_dev[df_dev["_servidor_recibido"] < x_range[0]]
                if not df_dev_before.empty:
                    df_dev_range = df_dev_before.tail(1)

            df_dev_range = df_dev_range.dropna(subset=["latitude", "longitude"], how="any")
            df_visible = pd.concat([df_visible, df_dev_range], ignore_index=True)

        # === Filtrado final: eliminar coordenadas inválidas (99.0 o NaN) ===
        
        print(f"Rango temporal aplicado: {x_range[0]} → {x_range[1]}")
        print(f"Filas para el mapa: {len(df_visible)}")
        print(df_visible[["imei", "_servidor_recibido", "latitude", "longitude"]].tail(20))
        

        df_visible = df_visible[
            (df_visible["latitude"].notna()) &
            (df_visible["longitude"].notna()) &
            (df_visible["latitude"] != 99.0) &
            (df_visible["longitude"] != 99.0)
        ]
        
        print(f"Filas válidas para el mapa: {len(df_visible)}")
        print(df_visible[["imei", "_servidor_recibido", "latitude", "longitude"]].tail(20))


        # === Dibujar mapa sincronizado ===
        fig_map_new = go.Figure()
        for imei in visible_series:
            dev_df = df_visible[df_visible["imei"] == imei]
            if not dev_df.empty:
                fig_map_new.add_trace(go.Scattermap(
                    lat=dev_df["latitude"],
                    lon=dev_df["longitude"],
                    mode='markers+lines',
                    name=str(imei),
                    marker=dict(size=9),
                    text=[f"IMEI: {row['imei']}<br>{row['_servidor_recibido']}" for _, row in dev_df.iterrows()],
                ))

        if not df_visible.empty:
            fig_map_new.update_layout(
                map=dict(
                    style="open-street-map",
                    center={"lat": df_visible["latitude"].mean(),
                            "lon": df_visible["longitude"].mean()},
                    zoom=6,
                ),
                map_style="open-street-map",
                dragmode="zoom",
                uirevision="constant",
                title="Posición sincronizada con la gráfica de transmisiones"
            )
        else:
            fig_map_new.update_layout(
                title="Posición (sin datos válidos en este rango temporal)",
                height=800,
                map=dict(style="open-street-map", zoom=2, center={"lat": 0, "lon": 0}),
                dragmode="zoom",
                uirevision="constant"
            )

        print(f"Pintando {len(df_visible)} puntos de {len(df_visible['imei'].unique())} dispositivos visibles.")

        return fig_map_new


    # === EJECUCIÓN DEL DASHBOARD ===
    app.run(debug=True, host="127.0.0.1", port=8050)


if __name__ == "__main__":
    run_dashboard()
