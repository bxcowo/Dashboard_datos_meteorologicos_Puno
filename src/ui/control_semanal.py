"""
Dashboard de Control Semanal - Datos Meteorológicos Puno
Layout y callbacks para análisis semanal con comparación multi-estación
"""
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.graph_objects as go
from datetime import datetime, timedelta
from data.file_managment import get_registro_diario
from cache import data_cache
import calendar

# Colores para las estaciones y variables
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

def create_date_picker(id, label, default_date):
    """Crea un selector de fecha con label"""
    return dmc.GridCol(
        span={"base": 12, "sm": 6, "md": 3},
        children=dmc.Stack(gap="xs", children=[
            dmc.Text(label, size="sm", fw=500),
            dcc.DatePickerSingle(
                id=id, date=default_date, display_format='DD/MM/YYYY', style={'width': '100%'}
            )
        ])
    )

def create_station_selector(id, label, badge_text, badge_color, stations, value, clearable):
    """Crea un selector de estación con badge"""
    return dmc.GridCol(
        span={"base": 12, "sm": 6, "md": 3},
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

def create_graph_paper(title, badge_text, badge_color, graph_id, height='500px'):
    """Crea un Paper con gráfico"""
    return dmc.Paper(p="md", shadow="sm", radius="md", withBorder=True, children=[
        dmc.Stack(gap="md", children=[
            dmc.Group(justify="space-between", children=[
                dmc.Title(title, order=4),
                dmc.Badge(badge_text, color=badge_color, variant="light")
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

def create_stat_card(title, values, unit, color, is_total=False):
    """Crea una tarjeta de estadística"""
    main_value = sum(values) if is_total else sum(values) / len(values)
    sub_text = (f"Max: {max(values):.1f}{unit} | Promedio: {sum(values)/len(values):.1f}{unit}"
                if is_total else f"Max: {max(values):.1f}{unit} | Min: {min(values):.1f}{unit}")

    return dmc.GridCol(span={"base": 12, "sm": 6, "md": 4}, children=[
        dmc.Paper(p="md", withBorder=True, radius="md", children=[
            dmc.Stack(gap="xs", children=[
                dmc.Text(title, size="sm", c="dimmed"),
                dmc.Text(f"{main_value:.1f}{unit}", size="xl", fw=700, c=color),
                dmc.Text(sub_text, size="xs", c="dimmed")
            ])
        ])
    ])

def control_semanal_layout():
    """Crea el layout para el análisis semanal"""
    # Obtener lista de estaciones desde el cache
    normales_tmax = data_cache.get("NORMAL_TMAX")
    stations_list = normales_tmax.index.tolist() if normales_tmax is not None else []

    return dmc.Container(fluid=True, style={"padding": "20px"}, children=[
        dmc.Stack(gap="md", children=[
            # Header
            dmc.Paper(p="md", shadow="sm", radius="md", children=[
                dmc.Group(justify="space-between", children=[
                    dmc.Stack(gap="xs", children=[
                        dmc.Title("Análisis Semanal", order=2, c="blue.7"),
                        dmc.Text("Comparación de Datos Diarios vs Valores Normales (1991-2020)", size="sm", c="dimmed")
                    ]),
                    dmc.ActionIcon(DashIconify(icon="mdi:calendar-range", width=28), size="xl", variant="light", color="blue")
                ])
            ]),

            # Panel de control
            dmc.Paper(p="md", shadow="sm", radius="md", withBorder=True, children=[
                dmc.Stack(gap="md", children=[
                    dmc.Group(justify="space-between", children=[
                        dmc.Title("Configuración de Consulta", order=4),
                        dmc.Badge("Datos Diarios + Normales", color="green", variant="light")
                    ]),
                    dmc.Grid(gutter="md", children=[
                        create_date_picker('fecha-inicio-semanal', "Fecha Inicio", datetime(2025, 10, 1).date()),
                        create_date_picker('fecha-fin-semanal', "Fecha Fin", datetime(2025, 10, 9).date()),
                        create_station_selector('estacion-selector-1-semanal', "Estación Principal", "Obligatorio", "red",
                                               stations_list, stations_list[0] if stations_list else None, False),
                        create_station_selector('estacion-selector-2-semanal', "Estación Comparación", "Opcional", "blue",
                                               stations_list, None, True)
                    ]),
                    dmc.Group(justify="flex-end", children=[
                        dmc.Button("Cargar Datos", id='cargar-datos-btn-semanal',
                                  leftSection=DashIconify(icon="mdi:refresh", width=20), size="md", variant="filled")
                    ]),
                    html.Div(id='loading-status-semanal')
                ])
            ]),

            # Gráficos
            create_graph_paper("🌡️ Temperaturas (Máxima y Mínima)", "Datos Diarios + Normales",
                              "orange", "temperatura-graph-semanal", '500px'),
            create_graph_paper("💧 Precipitación", "Datos Diarios + Normales",
                              "teal", "precipitacion-graph-semanal", '400px'),

            # Estadísticas
            dmc.Paper(p="md", shadow="sm", radius="md", withBorder=True, children=[
                dmc.Stack(gap="md", children=[
                    dmc.Title("📊 Estadísticas del Período", order=4),
                    html.Div(id='estadisticas-container-semanal')
                ])
            ])
        ])
    ])


@callback(
    [Output('temperatura-graph-semanal', 'figure'), Output('precipitacion-graph-semanal', 'figure'),
     Output('estadisticas-container-semanal', 'children'), Output('loading-status-semanal', 'children')],
    [Input('cargar-datos-btn-semanal', 'n_clicks')],
    [State('fecha-inicio-semanal', 'date'), State('fecha-fin-semanal', 'date'),
     State('estacion-selector-1-semanal', 'value'), State('estacion-selector-2-semanal', 'value')]
)
def update_graphs_semanal(n_clicks, fecha_inicio, fecha_fin, estacion1, estacion2):
    # Obtener normales desde el cache
    normales_dict = {
        'TMAX': data_cache.get("NORMAL_TMAX").to_dict('index') if data_cache.get("NORMAL_TMAX") is not None else {},
        'TMIN': data_cache.get("NORMAL_TMIN").to_dict('index') if data_cache.get("NORMAL_TMIN") is not None else {},
        'PP': data_cache.get("NORMAL_PP").to_dict('index') if data_cache.get("NORMAL_PP") is not None else {}
    }

    # Validación inicial
    if not n_clicks or not fecha_inicio or not fecha_fin or not estacion1:
        empty_fig = lambda title: go.Figure(layout=dict(
            title="Selecciona un rango de fechas y presiona 'Cargar Datos'",
            template='plotly_white'
        ))
        return empty_fig(""), empty_fig(""), dmc.Text("No hay datos cargados", c="dimmed"), None

    try:
        start_date = datetime.fromisoformat(fecha_inicio)
        end_date = datetime.fromisoformat(fecha_fin)

        # Validaciones
        if start_date > end_date:
            return no_update, no_update, no_update, dmc.Alert(
                "La fecha de inicio debe ser anterior a la fecha fin", color="red",
                icon=DashIconify(icon="mdi:alert")
            )
        if estacion2 and estacion1 == estacion2:
            return no_update, no_update, no_update, dmc.Alert(
                "Las estaciones deben ser diferentes para comparar", color="yellow",
                icon=DashIconify(icon="mdi:alert")
            )

        # Generar lista de fechas
        date_list = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]

        # Función para cargar datos de una estación
        def load_station_data(estacion):
            fechas, tmax_values, tmin_values, pp_values = [], [], [], []
            for date in date_list:
                try:
                    df_dia = get_registro_diario(date.year, date.month, date.day)
                    if estacion in df_dia.index.get_level_values('ESTACION'):
                        row = df_dia.xs(estacion, level='ESTACION').iloc[0]
                        fechas.append(date)
                        tmax_values.append(row['TMAX'])
                        tmin_values.append(row['TMIN'])
                        pp_values.append(row['PP'])
                except:
                    continue
            return fechas, tmax_values, tmin_values, pp_values

        # Cargar datos estación 1
        fechas1, tmax1, tmin1, pp1 = load_station_data(estacion1)
        if not fechas1:
            return no_update, no_update, no_update, dmc.Alert(
                f"No se encontraron datos para la estación {estacion1} en el rango seleccionado",
                color="yellow", icon=DashIconify(icon="mdi:alert")
            )

        # Preparar normales estación 1
        normales_est1 = {
            var: list(normales_dict[var][estacion1].values()) if estacion1 in normales_dict[var] else None
            for var in ['TMAX', 'TMIN', 'PP']
        }

        # Función para agregar trazas diarias
        def add_daily_traces(fig, fechas, tmax, tmin, pp, estacion, station_key, is_temp_graph):
            traces_config = [
                ('TMAX', tmax, 'tmax', '°C') if is_temp_graph else ('PP', pp, 'pp', 'mm'),
                ('TMIN', tmin, 'tmin', '°C') if is_temp_graph else None
            ]
            for config in filter(None, traces_config):
                var_name, values, color_key, unit = config
                fig.add_trace(go.Scatter(
                    x=fechas, y=values, mode='lines+markers',
                    name=f'{estacion} - {var_name} (Diaria)',
                    line=dict(color=COLORS[station_key][color_key], width=1.5,
                             dash='dot' if station_key == 'station2' else None),
                    marker=dict(size=3, symbol='square' if station_key == 'station2' else 'circle'),
                    hovertemplate=f'<b>{estacion} - {var_name} Diaria</b><br>Fecha: %{{x|%d/%m/%Y}}<br>Valor: %{{y:.1f}}{unit}<extra></extra>'
                ))

        # Función para agregar líneas normales por mes
        def add_normal_lines(fig, estacion, station_key, var_configs):
            months_in_range = sorted(set(d.month for d in date_list))
            for month_idx, month in enumerate(months_in_range):
                year = start_date.year if start_date.month <= month <= end_date.month else end_date.year
                first_day = max(datetime(year, month, 1), start_date)
                last_day = min(datetime(year, month, calendar.monthrange(year, month)[1]), end_date)

                for var_name, color_key, unit, normal_values in var_configs:
                    if normal_values is None:
                        continue
                    value = normal_values[month - 1]
                    fig.add_trace(go.Scatter(
                        x=[first_day, last_day], y=[value, value], mode='lines',
                        name=f'{estacion} - {var_name} Normal (1991-2020)',
                        line=dict(color=COLORS[station_key][color_key], width=4),
                        hovertemplate=f'<b>{estacion} - {var_name} Normal</b><br>Mes: {calendar.month_name[month]}<br>Valor: {value:.1f}{unit}<extra></extra>',
                        legendgroup=f'{var_name.lower()}_normal_{station_key[-1]}',
                        showlegend=(month_idx == 0)
                    ))

        # GRÁFICO DE TEMPERATURAS
        fig_temp = go.Figure()
        add_daily_traces(fig_temp, fechas1, tmax1, tmin1, pp1, estacion1, 'station1', True)
        add_normal_lines(fig_temp, estacion1, 'station1', [
            ('TMAX', 'tmax_normal', '°C', normales_est1['TMAX']),
            ('TMIN', 'tmin_normal', '°C', normales_est1['TMIN'])
        ])

        # Estación 2 si existe
        fechas2, tmax2, tmin2, pp2 = None, None, None, None
        if estacion2:
            fechas2, tmax2, tmin2, pp2 = load_station_data(estacion2)
            if fechas2:
                add_daily_traces(fig_temp, fechas2, tmax2, tmin2, pp2, estacion2, 'station2', True)
                normales_est2 = {
                    var: list(normales_dict[var][estacion2].values()) if estacion2 in normales_dict[var] else None
                    for var in ['TMAX', 'TMIN']
                }
                add_normal_lines(fig_temp, estacion2, 'station2', [
                    ('TMAX', 'tmax_normal', '°C', normales_est2['TMAX']),
                    ('TMIN', 'tmin_normal', '°C', normales_est2['TMIN'])
                ])

        fig_temp.update_layout(
            xaxis=dict(title="Fecha", rangeslider=dict(visible=True), type='date',
                      dtick=86400000, tickformat='%d/%m/%Y'),
            yaxis=dict(title="Temperatura (°C)"),
            hovermode='x unified', template='plotly_white', height=500,
            legend=dict(orientation="v", yanchor="top", y=0.99, xanchor="left", x=1.01),
            dragmode='pan'
        )

        # GRÁFICO DE PRECIPITACIÓN
        fig_pp = go.Figure()
        add_daily_traces(fig_pp, fechas1, tmax1, tmin1, pp1, estacion1, 'station1', False)
        add_normal_lines(fig_pp, estacion1, 'station1', [
            ('PP', 'pp_normal', 'mm', normales_est1['PP'])
        ])

        if estacion2 and fechas2:
            add_daily_traces(fig_pp, fechas2, tmax2, tmin2, pp2, estacion2, 'station2', False)
            normales_est2_pp = list(normales_dict['PP'][estacion2].values()) if estacion2 in normales_dict['PP'] else None
            add_normal_lines(fig_pp, estacion2, 'station2', [
                ('PP', 'pp_normal', 'mm', normales_est2_pp)
            ])

        fig_pp.update_layout(
            xaxis=dict(title="Fecha", rangeslider=dict(visible=True), type='date',
                      dtick=86400000, tickformat='%d/%m/%Y'),
            yaxis=dict(title="Precipitación (mm)"),
            hovermode='x unified', template='plotly_white', height=400,
            legend=dict(orientation="v", yanchor="top", y=0.99, xanchor="left", x=1.01),
            dragmode='pan'
        )

        # ESTADÍSTICAS
        stats_children = [
            dmc.Stack(gap="xs", children=[
                dmc.Title(f"📍 {estacion1}", order=5, c="blue.7"),
                dmc.Grid(gutter="md", children=[
                    create_stat_card("TMAX Promedio", tmax1, "°C", "red.6"),
                    create_stat_card("TMIN Promedio", tmin1, "°C", "blue.6"),
                    create_stat_card("PP Total", pp1, "mm", "green.6", is_total=True)
                ])
            ])
        ]

        if estacion2 and fechas2:
            stats_children.append(
                dmc.Stack(gap="xs", children=[
                    dmc.Title(f"📍 {estacion2}", order=5, c="violet.7"),
                    dmc.Grid(gutter="md", children=[
                        create_stat_card("TMAX Promedio", tmax2, "°C", "red.6"),
                        create_stat_card("TMIN Promedio", tmin2, "°C", "blue.6"),
                        create_stat_card("PP Total", pp2, "mm", "green.6", is_total=True)
                    ])
                ])
            )

        status_msg = f"✅ Datos cargados: {len(fechas1)} días"
        if estacion2 and fechas2:
            status_msg += f" | Comparando 2 estaciones"

        return fig_temp, fig_pp, dmc.Stack(gap="lg", children=stats_children), \
               dmc.Alert(status_msg, color="green", icon=DashIconify(icon="mdi:check-circle"))

    except Exception as e:
        return no_update, no_update, no_update, dmc.Alert(
            f"Error al cargar datos: {str(e)}", color="red", icon=DashIconify(icon="mdi:alert")
        )
