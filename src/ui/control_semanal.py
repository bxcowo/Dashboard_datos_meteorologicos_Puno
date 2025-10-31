from dash import html, dcc, callback, Input, Output, State, no_update
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.graph_objects as go
from datetime import datetime
from data.file_managment import get_registro_mensual, convert_month
from cache import data_cache
import pandas as pd

COLORS = {
    'station1': {
        'tmax': '#fa5252', 'tmin': '#339af0', 'pp': '#51cf66',
        'tmax_normal': '#9333ea', 'tmin_normal': '#c084fc', 'pp_normal': '#eab308'
    },
    'station2': {
        'tmax': '#f03e3e', 'tmin': '#1c7ed6', 'pp': '#37b24d',
        'tmax_normal': '#7c3aed', 'tmin_normal': '#a78bfa', 'pp_normal': '#facc15'
    }
}


def get_month_range(start_date, end_date):
    """
    Genera lista de tuplas (año, mes) entre dos fechas
    """

    months = []
    current = start_date.replace(day=1)
    while current <= end_date:
        months.append((current.year, current.month))
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    return months


def get_monthly_data_cached(year, month):
    """
    Obtiene datos mensuales con cache por mes
    """

    cache_key = f"MENSUAL_{year}_{month:02d}"

    if cache_key not in data_cache:
        df_mes = get_registro_mensual(year, month)
        days_in_month = len(df_mes)
        fechas_mes = pd.date_range(start=f"{year}-{month:02d}-01", periods=days_in_month, freq='D')
        data_cache[cache_key] = (df_mes, fechas_mes.tolist())

    return data_cache[cache_key]


def extract_station_data(df, estacion):
    """
    Extrae TMAX, TMIN, PP de una estación desde DataFrame con MultiIndex
    """

    result = {'TMAX': None, 'TMIN': None, 'PP': None}

    for col in df.columns:
        if isinstance(col, tuple) and len(col) == 2:
            estacion_col, variable_col = col
            if estacion_col == estacion:
                var_str = str(variable_col).upper().strip()
                if 'MAX' in var_str and result['TMAX'] is None:
                    result['TMAX'] = pd.to_numeric(df[col], errors='coerce').tolist()
                elif 'MIN' in var_str and result['TMIN'] is None:
                    result['TMIN'] = pd.to_numeric(df[col], errors='coerce').tolist()
                elif ('PP' in var_str or 'PREC' in var_str) and result['PP'] is None:
                    result['PP'] = pd.to_numeric(df[col], errors='coerce').tolist()

    if None in result.values():
        return None
    return result


def get_normal_values(estacion, fechas):
    """
    Obtiene valores normales para una estación en rango de fechas
    """

    df_tmax = data_cache.get('NORMAL_TMAX')
    df_tmin = data_cache.get('NORMAL_TMIN')
    df_pp = data_cache.get('NORMAL_PP')

    result = {'TMAX': [], 'TMIN': [], 'PP': []}

    for fecha in fechas:
        fecha_ts = pd.Timestamp(fecha) if not isinstance(fecha, pd.Timestamp) else fecha
        mes_nombre = convert_month(fecha_ts.month)

        for var_name, df_normal in [('TMAX', df_tmax), ('TMIN', df_tmin), ('PP', df_pp)]:
            try:
                if df_normal is not None and estacion in df_normal.index:
                    val = df_normal.loc[estacion, mes_nombre]
                    result[var_name].append(val if pd.notna(val) else None)
                else:
                    result[var_name].append(None)
            except:
                result[var_name].append(None)

    return result


def add_graph_traces(fig, fechas, data_real, data_normal, estacion, color_key, var_names):
    """
    Agrega trazas de datos reales y normales al gráfico
    """

    colors = COLORS[color_key]
    is_station2 = (color_key == 'station2')

    for var in var_names:
        fig.add_trace(go.Scatter(
            x=fechas, y=data_real[var], mode='lines+markers',
            name=f'{estacion} - {var}',
            line=dict(color=colors[var.lower()], width=2, dash='dot' if is_station2 else 'solid'),
            marker=dict(size=4 if var != 'PP' else 6, symbol='square' if is_station2 else 'circle')
        ))

        fig.add_trace(go.Scatter(
            x=fechas, y=data_normal[var], mode='lines',
            name=f'{estacion} - {var} Normal (1991-2020)',
            line=dict(color=colors[f'{var.lower()}_normal'], width=3, dash='dashdot' if is_station2 else 'dash'),
            line_shape='hv'
        ))


def create_station_selector(id, label, badge_text, badge_color, stations, value, clearable):
    """
    Crea un selector de estación con badge
    """

    return dmc.GridCol(
        span={"base": 12, "sm": 6, "md": 4},
        children=dmc.Stack(gap="xs", children=[
            dmc.Group(gap="xs", children=[
                dmc.Text(label, size="sm", fw=500),
                dmc.Badge(badge_text, size="xs", color=badge_color, variant="light")
            ]),
            dmc.Select(
                id=id,
                data=[{"value": s, "label": s} for s in stations],
                value=value,
                placeholder="Selecciona para comparar..." if clearable else None,
                searchable=True,
                clearable=clearable
            )
        ])
    )


def create_graph_paper(title, graph_id, height='500px'):
    """Crea un Paper con gráfico"""
    return dmc.Paper(p="md", shadow="sm", radius="md", withBorder=True, children=[
        dmc.Stack(gap="md", children=[
            dmc.Group(justify="space-between", children=[
                dmc.Title(title, order=4)
            ]),
            dcc.Loading(type="default", children=[
                dcc.Graph(
                    id=graph_id,
                    config={'displayModeBar': True, 'displaylogo': False, 'scrollZoom': True},
                    style={'height': height}
                )
            ])
        ])
    ])


def control_semanal_layout():
    """
    Crea el layout para el análisis semanal
    """

    stations_list = data_cache["LISTA_ESTACIONES"]

    return dmc.Container(fluid=True, style={"padding": "20px"}, children=[
        dmc.Stack(gap="md", children=[
            dmc.Paper(p="md", shadow="sm", radius="md", children=[
                dmc.Group(justify="space-between", children=[
                    dmc.Stack(gap="xs", children=[
                        dmc.Title("Análisis Mensual", order=2, c="blue"),
                        dmc.Text("Comparación de Datos Mensuales vs Valores Normales", size="sm", c="dimmed")
                    ])
                ])
            ]),

            dmc.Paper(p="md", shadow="sm", radius="md", withBorder=True, children=[
                dmc.Stack(gap="md", children=[
                    dmc.Grid(align="center", justify="center", gutter="md", children=[
                        dmc.GridCol(span={"base": 12, "sm": 6, "md": 4}, children=[
                            dmc.Stack(gap="xs", justify="center", align="center", children=[
                                dmc.Text("Rango de Fechas", size="sm", fw=500),
                                dmc.DatesProvider(
                                    settings={"locale": "es", "firstDayOfWeek": 1},
                                    children=dmc.DatePicker(
                                        id="date-range-semanal",
                                        type="range",
                                        value=[],
                                        minDate=datetime(2020, 1, 1).date(),
                                        size="lg"
                                    )
                                )
                            ])
                        ]),
                        create_station_selector('estacion-selector-1-semanal', "Estación Principal", "Obligatorio", "red", stations_list, stations_list[0] if stations_list else None, False),
                        create_station_selector('estacion-selector-2-semanal', "Estación Comparación", "Opcional", "blue", stations_list, None, True)
                    ]),
                    dmc.Group(justify="flex-end", children=[
                        dmc.Button("Cargar Datos", id='cargar-datos-btn-semanal',
                                  leftSection=DashIconify(icon="mdi:refresh", width=20), size="md", variant="filled")
                    ]),
                    html.Div(id='loading-status-semanal')
                ])
            ]),

            create_graph_paper("Temperaturas (Máxima y Mínima)", "temperatura-graph-semanal", '500px'),
            create_graph_paper("Precipitación", "precipitacion-graph-semanal", '400px'),
        ])
    ])


@callback(
    [Output('temperatura-graph-semanal', 'figure'), Output('precipitacion-graph-semanal', 'figure'),
     Output('loading-status-semanal', 'children')],
    [Input('cargar-datos-btn-semanal', 'n_clicks')],
    [State('date-range-semanal', 'value'), State('estacion-selector-1-semanal', 'value'), State('estacion-selector-2-semanal', 'value')]
)
def update_graphs_semanal(n_clicks, date_range, estacion1, estacion2):
    if not n_clicks or not date_range or not estacion1 or not isinstance(date_range, list) or len(date_range) != 2:
        empty_fig = go.Figure(layout=dict(
            title="Selecciona un rango de fechas y presiona 'Cargar Datos'",
            template='plotly_white'
        ))
        return empty_fig, empty_fig, None

    start_date = datetime.fromisoformat(date_range[0]) if isinstance(date_range[0], str) else datetime.combine(date_range[0], datetime.min.time())
    end_date = datetime.fromisoformat(date_range[1]) if isinstance(date_range[1], str) else datetime.combine(date_range[1], datetime.min.time())

    if start_date > end_date:
        return no_update, no_update, dmc.Alert(
            "La fecha de inicio debe ser anterior a la fecha fin", color="red",
            icon=DashIconify(icon="mdi:alert")
        )
    if estacion2 and estacion1 == estacion2:
        return no_update, no_update, dmc.Alert(
            "Las estaciones deben ser diferentes para comparar", color="yellow",
            icon=DashIconify(icon="mdi:alert")
        )

    months_to_load = get_month_range(start_date, end_date)
    all_data = []
    all_fechas = []

    for year, month in months_to_load:
        df_mes, fechas_mes = get_monthly_data_cached(year, month)
        all_data.append(df_mes)
        all_fechas.extend(fechas_mes)

    df_combined = pd.concat(all_data, ignore_index=True)

    fechas_series = pd.Series(all_fechas, name='fecha')
    mask = (fechas_series >= start_date) & (fechas_series <= end_date)
    df_filtrado = df_combined[mask].reset_index(drop=True)
    fechas_filtradas = fechas_series[mask].reset_index(drop=True).tolist()

    if len(df_filtrado) == 0:
        return no_update, no_update, dmc.Alert(
            "No se encontraron datos en el rango seleccionado", color="yellow",
            icon=DashIconify(icon="mdi:alert")
        )

    data1 = extract_station_data(df_filtrado, estacion1)
    if not data1:
        return no_update, no_update, dmc.Alert(
            f"No se encontraron datos para la estación {estacion1}", color="yellow",
            icon=DashIconify(icon="mdi:alert")
        )

    normal1 = get_normal_values(estacion1, fechas_filtradas)

    fig_temp = go.Figure()
    fig_pp = go.Figure()

    add_graph_traces(fig_temp, fechas_filtradas, data1, normal1, estacion1, 'station1', ['TMAX', 'TMIN'])
    add_graph_traces(fig_pp, fechas_filtradas, data1, normal1, estacion1, 'station1', ['PP'])

    if estacion2:
        data2 = extract_station_data(df_filtrado, estacion2)
        if data2:
            normal2 = get_normal_values(estacion2, fechas_filtradas)
            add_graph_traces(fig_temp, fechas_filtradas, data2, normal2, estacion2, 'station2', ['TMAX', 'TMIN'])
            add_graph_traces(fig_pp, fechas_filtradas, data2, normal2, estacion2, 'station2', ['PP'])

    fig_temp.update_layout(
        xaxis=dict(title="Fecha", tickformat='%d/%m/%Y'),
        yaxis=dict(title="Temperatura (°C)"),
        hovermode='x unified', template='plotly_white', height=500,
        legend=dict(orientation="v", yanchor="top", y=0.99, xanchor="left", x=1.01)
    )

    fig_pp.update_layout(
        xaxis=dict(title="Fecha", tickformat='%d/%m/%Y'),
        yaxis=dict(title="Precipitación (mm)"),
        hovermode='x unified', template='plotly_white', height=400,
        legend=dict(orientation="v", yanchor="top", y=0.99, xanchor="left", x=1.01)
    )

    num_meses = len(months_to_load)
    if num_meses == 1:
        status_msg = f" Datos cargados: {len(fechas_filtradas)} días del {months_to_load[0][1]}/{months_to_load[0][0]}"
    else:
        status_msg = f" Datos cargados: {len(fechas_filtradas)} días de {num_meses} meses"
    if estacion2 and data2:
        status_msg += f" | Comparando 2 estaciones"

    return fig_temp, fig_pp, dmc.Alert(status_msg, color="green", icon=DashIconify(icon="mdi:check-circle"))
