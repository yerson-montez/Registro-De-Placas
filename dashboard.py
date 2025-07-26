import dash
from dash import html, dcc, Output, Input
import pandas as pd
import plotly.express as px
import subprocess
import os

# ========== CONFIG ========== #
CSV_FILE = os.path.join(os.getcwd(), "registro.csv")

# ========== APP INIT ========== #
app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    title="Dashboard de Placas",
    external_stylesheets=[
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css"
    ]
)
server = app.server

# ========== LAYOUT ========== #
app.layout = html.Div([
    html.Div([
        html.H1("🚘 Dashboard de Registros de Placas", className="text-center my-4"),

        html.Div([
            html.Button("▶ Iniciar reconocimiento", id='btn-iniciar', n_clicks=0, className='btn btn-success'),
            html.Span(id='estado-script', className="ms-3 text-muted fs-5")
        ], className="d-flex justify-content-center mb-4"),

        dcc.Interval(id='intervalo', interval=5000, n_intervals=0),

        html.Div([
            dcc.Graph(id='grafico-barras', config={"displayModeBar": False}, className="mb-5"),
            dcc.Graph(id='grafico-pie', config={"displayModeBar": False}, className="mb-5"),
            dcc.Graph(id='grafico-linea', config={"displayModeBar": False}, className="mb-5")
        ], className="container"),

        html.H2("📋 Últimos Registros", className="text-center my-4"),
        html.Div(id='tabla-registros', className="container mb-5", style={"maxHeight": "400px", "overflowY": "auto"})
    ], className="shadow p-4 bg-white rounded container my-5")
], style={"backgroundColor": "#f4f6f9", "minHeight": "100vh"})

# ========== FUNCIONES AUXILIARES ========== #
def leer_datos():
    if not os.path.exists(CSV_FILE):
        return pd.DataFrame(columns=["ID", "Placa", "Evento", "FechaHora", "Propietario"])
    df = pd.read_csv(CSV_FILE, encoding='utf-8-sig')
    df.columns = ["ID", "Placa", "Evento", "FechaHora", "Propietario"]
    df["FechaHora"] = pd.to_datetime(df["FechaHora"])
    return df

# ========== CALLBACKS ========== #
@app.callback(
    Output('estado-script', 'children'),
    Input('btn-iniciar', 'n_clicks'),
    prevent_initial_call=True
)
def iniciar_script(n):
    try:
        subprocess.Popen(["python", "prueba1.py"], shell=True)
        return "✅ Script ejecutado"
    except Exception as e:
        return f"❌ Error: {e}"

@app.callback(
    Output('grafico-barras', 'figure'),
    Output('grafico-pie', 'figure'),
    Output('grafico-linea', 'figure'),
    Output('tabla-registros', 'children'),
    Input('intervalo', 'n_intervals')
)
def actualizar_graficos(n):
    df = leer_datos()
    if df.empty:
        return dash.no_update, dash.no_update, dash.no_update, html.P("No hay registros.")

    # Gráfico de barras por evento
    fig_barras = px.bar(
        df.groupby("Evento").size().reset_index(name='Cantidad'),
        x='Evento', y='Cantidad', color='Evento',
        barmode='group', title="Cantidad de eventos por tipo"
    )

    # Gráfico circular por propietario
    fig_pie = px.pie(df, names='Propietario', title="Distribución por propietario")

    # Gráfico de línea por fecha
    df['Fecha'] = df['FechaHora'].dt.date
    fig_linea = px.line(
        df.groupby("Fecha").size().reset_index(name='Registros'),
        x="Fecha", y="Registros", title="Registros por día"
    )

    # Tabla HTML
    tabla = html.Table([
        html.Thead(html.Tr([html.Th(col) for col in df.columns])),
        html.Tbody([
            html.Tr([html.Td(df.iloc[i][col]) for col in df.columns])
            for i in range(len(df) - 1, max(-1, len(df) - 11), -1)
        ])
    ], className="table table-striped table-bordered table-hover")

    return fig_barras, fig_pie, fig_linea, tabla

if __name__ == "__main__":
    app.run(debug=True)
