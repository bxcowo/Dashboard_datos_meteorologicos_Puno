"""
Dashboard de Control Semanal - Datos Meteorológicos Puno
Layout y callbacks para análisis semanal con comparación multi-estación
"""
from dash import html, dcc, callback, Input, Output, State, no_update
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.graph_objects as go
from datetime import datetime
from data.file_managment import get_registro_mensual
from cache import data_cache
import pandas as pd
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

def create_station_selector(id, label, badge_text, badge_color, stations, value, clearable):
    """Crea un selector de estación con badge"""
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
                        dmc.Title("Análisis Mensual", order=2, c="blue.7"),
                        dmc.Text("Comparación de Datos Mensuales vs Valores Normales (1991-2020)", size="sm", c="dimmed")
                    ]),
                    dmc.ActionIcon(DashIconify(icon="mdi:calendar-month", width=28), size="xl", variant="light", color="blue")
                ])
            ]),

            # Panel de control
            dmc.Paper(p="md", shadow="sm", radius="md", withBorder=True, children=[
                dmc.Stack(gap="md", children=[
                    dmc.Group(justify="space-between", children=[
                        dmc.Title("Configuración de Consulta", order=4),
                        dmc.Badge("Datos Mensuales + Normales", color="green", variant="light")
                    ]),
                    dmc.Grid(gutter="md", children=[
                        # Date range picker
                        dmc.GridCol(span={"base": 12, "sm": 6, "md": 4}, children=[
                            dmc.Stack(gap="xs", children=[
                                dmc.Text("Rango de Fechas", size="sm", fw=500),
                                dmc.DatesProvider(
                                    settings={"locale": "es", "firstDayOfWeek": 1},
                                    children=dmc.DatePicker(
                                        id="date-range-semanal",
                                        type="range",
                                        value=[datetime(2025, 10, 1).date(), datetime(2025, 10, 31).date()],
                                        minDate=datetime(2020, 1, 1).date()
                                    )
                                )
                            ])
                        ]),
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
            create_graph_paper("🌡️ Temperaturas (Máxima y Mínima)", "Datos Mensuales + Normales",
                              "orange", "temperatura-graph-semanal", '500px'),
            create_graph_paper("💧 Precipitación", "Datos Mensuales + Normales",
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
    [State('date-range-semanal', 'value'),
     State('estacion-selector-1-semanal', 'value'), State('estacion-selector-2-semanal', 'value')]
)
def update_graphs_semanal(n_clicks, date_range, estacion1, estacion2):
    # Obtener normales desde el cache
    normales_dict = {
        'TMAX': data_cache.get("NORMAL_TMAX").to_dict('index') if data_cache.get("NORMAL_TMAX") is not None else {},
        'TMIN': data_cache.get("NORMAL_TMIN").to_dict('index') if data_cache.get("NORMAL_TMIN") is not None else {},
        'PP': data_cache.get("NORMAL_PP").to_dict('index') if data_cache.get("NORMAL_PP") is not None else {}
    }

    # Validación inicial
    if not n_clicks or not date_range or not estacion1 or not isinstance(date_range, list) or len(date_range) != 2:
        empty_fig = go.Figure(layout=dict(
            title="Selecciona un rango de fechas y presiona 'Cargar Datos'",
            template='plotly_white'
        ))
        return empty_fig, empty_fig, dmc.Text("No hay datos cargados", c="dimmed"), None

    try:
        # Manejar diferentes formatos de fecha
        if isinstance(date_range[0], str):
            start_date = datetime.fromisoformat(date_range[0])
        else:
            start_date = datetime.combine(date_range[0], datetime.min.time())

        if isinstance(date_range[1], str):
            end_date = datetime.fromisoformat(date_range[1])
        else:
            end_date = datetime.combine(date_range[1], datetime.min.time())

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

        # Calcular los meses necesarios en el rango
        months_to_load = []
        current = start_date.replace(day=1)
        while current <= end_date:
            months_to_load.append((current.year, current.month))
            # Ir al siguiente mes
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        # Cargar datos de todos los meses necesarios
        all_data = []
        all_fechas = []

        for year, month in months_to_load:
            try:
                df_mes = get_registro_mensual(year, month)
                # Generar fechas para cada día del mes
                days_in_month = len(df_mes)
                fechas_mes = pd.date_range(start=f"{year}-{month:02d}-01", periods=days_in_month, freq='D')

                all_data.append(df_mes)
                all_fechas.extend(fechas_mes.tolist())
            except Exception as e:
                return no_update, no_update, no_update, dmc.Alert(
                    f"Error al cargar datos del mes {month}/{year}: {str(e)}", color="red",
                    icon=DashIconify(icon="mdi:alert")
                )

        # Combinar todos los dataframes manteniendo el MultiIndex en columnas
        df_combined = pd.concat(all_data, ignore_index=True)

        # Agregar las fechas como una serie separada (no como parte del MultiIndex)
        fechas_series = pd.Series(all_fechas, name='fecha')

        # Filtrar por el rango de fechas exacto
        mask = (fechas_series >= start_date) & (fechas_series <= end_date)
        df_filtrado = df_combined[mask].copy()
        fechas_filtradas = fechas_series[mask].reset_index(drop=True)

        if len(df_filtrado) == 0:
            return no_update, no_update, no_update, dmc.Alert(
                "No se encontraron datos en el rango seleccionado", color="yellow",
                icon=DashIconify(icon="mdi:alert")
            )

        df_filtrado = df_filtrado.reset_index(drop=True)

        # Función para normalizar nombres de estaciones (igual que en file_managment.py)
        def normalize_station_name(name):
            """Normaliza el nombre de estación: quita acentos, mayúsculas, trim"""
            normalized = str(name).upper().strip()
            # Quitar acentos
            normalized = normalized.translate(str.maketrans('ÁÉÍÓÚ', 'AEIOU'))
            # Caso especial
            if "TAHUACO - YUNGUYO" in normalized:
                normalized = "TAHUACO YUNGUYO"
            return normalized

        # Función para extraer datos de una estación
        def extract_station_data(df, estacion):
            try:
                # El DataFrame tiene MultiIndex en columnas: (estacion, variable)
                # Normalizar nombre de estación para búsqueda
                estacion_norm = normalize_station_name(estacion)

                # Buscar en el MultiIndex
                tmax_data = None
                tmin_data = None
                pp_data = None

                # Imprimir columnas disponibles para debug
                print(f"Buscando estación: {estacion_norm}")
                print(f"Columnas MultiIndex disponibles: {[col for col in df.columns if isinstance(col, tuple)][:5]}...")

                for col in df.columns:
                    if isinstance(col, tuple) and len(col) == 2:
                        estacion_col, variable_col = col
                        estacion_col_norm = normalize_station_name(estacion_col)

                        # Verificar si la estación coincide
                        if estacion_norm == estacion_col_norm or estacion_norm in estacion_col_norm:
                            var_str = str(variable_col).upper().strip()
                            # Buscar TMAX o MAX
                            if 'MAX' in var_str:
                                tmax_data = pd.to_numeric(df[col], errors='coerce')
                                print(f"  ✓ Encontrado TMAX en columna: {col}")
                            # Buscar TMIN o MIN
                            elif 'MIN' in var_str:
                                tmin_data = pd.to_numeric(df[col], errors='coerce')
                                print(f"  ✓ Encontrado TMIN en columna: {col}")
                            # Buscar PP o PREC
                            elif 'PP' in var_str or 'PREC' in var_str:
                                pp_data = pd.to_numeric(df[col], errors='coerce')
                                print(f"  ✓ Encontrado PP en columna: {col}")

                if tmax_data is None or tmin_data is None or pp_data is None:
                    print(f"  ✗ Datos incompletos para {estacion}: TMAX={tmax_data is not None}, TMIN={tmin_data is not None}, PP={pp_data is not None}")
                    return None, None, None

                # Convertir a listas, manteniendo NaN para alineación con fechas
                # Plotly maneja automáticamente los valores NaN
                tmax = tmax_data.tolist()
                tmin = tmin_data.tolist()
                pp = pp_data.tolist()

                return tmax, tmin, pp
            except Exception as e:
                print(f"Error extrayendo datos para {estacion}: {e}")
                import traceback
                traceback.print_exc()
                return None, None, None

        # Extraer datos estación 1
        tmax1, tmin1, pp1 = extract_station_data(df_filtrado, estacion1)

        if not tmax1 or not tmin1 or not pp1:
            return no_update, no_update, no_update, dmc.Alert(
                f"No se encontraron datos para la estación {estacion1} en el rango seleccionado", color="yellow",
                icon=DashIconify(icon="mdi:alert")
            )

        # Usar las fechas filtradas
        fechas = fechas_filtradas.tolist()

        # Obtener valores normales para las estaciones
        normales = data_cache.get('NORMALES', {})

        def get_normal_values(estacion, fechas_list):
            """Obtiene los valores normales para una estación en el rango de fechas"""
            tmax_normal = []
            tmin_normal = []
            pp_normal = []

            estacion_norm = normalize_station_name(estacion)

            for fecha in fechas_list:
                mes = fecha.strftime('%B').upper() if hasattr(fecha, 'strftime') else pd.Timestamp(fecha).strftime('%B').upper()
                # Convertir nombre de mes en inglés a español
                meses_esp = {
                    'JANUARY': 'ENERO', 'FEBRUARY': 'FEBRERO', 'MARCH': 'MARZO',
                    'APRIL': 'ABRIL', 'MAY': 'MAYO', 'JUNE': 'JUNIO',
                    'JULY': 'JULIO', 'AUGUST': 'AGOSTO', 'SEPTEMBER': 'SEPTIEMBRE',
                    'OCTOBER': 'OCTUBRE', 'NOVEMBER': 'NOVIEMBRE', 'DECEMBER': 'DICIEMBRE'
                }
                mes_esp = meses_esp.get(mes, mes)

                # Buscar en las normales
                try:
                    if 'TMAX' in normales:
                        val = None
                        for idx in normales['TMAX'].index:
                            if normalize_station_name(idx) == estacion_norm:
                                val = normales['TMAX'].loc[idx, mes_esp] if mes_esp in normales['TMAX'].columns else None
                                break
                        tmax_normal.append(val)
                    else:
                        tmax_normal.append(None)

                    if 'TMIN' in normales:
                        val = None
                        for idx in normales['TMIN'].index:
                            if normalize_station_name(idx) == estacion_norm:
                                val = normales['TMIN'].loc[idx, mes_esp] if mes_esp in normales['TMIN'].columns else None
                                break
                        tmin_normal.append(val)
                    else:
                        tmin_normal.append(None)

                    if 'PP' in normales:
                        val = None
                        for idx in normales['PP'].index:
                            if normalize_station_name(idx) == estacion_norm:
                                val = normales['PP'].loc[idx, mes_esp] if mes_esp in normales['PP'].columns else None
                                break
                        pp_normal.append(val)
                    else:
                        pp_normal.append(None)
                except:
                    tmax_normal.append(None)
                    tmin_normal.append(None)
                    pp_normal.append(None)

            return tmax_normal, tmin_normal, pp_normal

        # Obtener normales para estación 1
        tmax1_normal, tmin1_normal, pp1_normal = get_normal_values(estacion1, fechas)

        # GRÁFICO DE TEMPERATURAS
        fig_temp = go.Figure()

        # Estación 1 - TMAX y TMIN
        fig_temp.add_trace(go.Scatter(
            x=fechas, y=tmax1, mode='lines+markers',
            name=f'{estacion1} - TMAX', line=dict(color=COLORS['station1']['tmax'], width=2),
            marker=dict(size=4)
        ))
        fig_temp.add_trace(go.Scatter(
            x=fechas, y=tmin1, mode='lines+markers',
            name=f'{estacion1} - TMIN', line=dict(color=COLORS['station1']['tmin'], width=2),
            marker=dict(size=4)
        ))

        # Agregar normales para estación 1
        fig_temp.add_trace(go.Scatter(
            x=fechas, y=tmax1_normal, mode='lines',
            name=f'{estacion1} - TMAX Normal', line=dict(color=COLORS['station1']['tmax_normal'], width=2, dash='dash'),
            showlegend=True
        ))
        fig_temp.add_trace(go.Scatter(
            x=fechas, y=tmin1_normal, mode='lines',
            name=f'{estacion1} - TMIN Normal', line=dict(color=COLORS['station1']['tmin_normal'], width=2, dash='dash'),
            showlegend=True
        ))

        # Estación 2 si existe
        tmax2, tmin2, pp2 = None, None, None
        tmax2_normal, tmin2_normal, pp2_normal = None, None, None
        if estacion2:
            tmax2, tmin2, pp2 = extract_station_data(df_filtrado, estacion2)
            if tmax2 and tmin2:
                # Datos reales
                fig_temp.add_trace(go.Scatter(
                    x=fechas, y=tmax2, mode='lines+markers',
                    name=f'{estacion2} - TMAX', line=dict(color=COLORS['station2']['tmax'], width=2, dash='dot'),
                    marker=dict(size=4, symbol='square')
                ))
                fig_temp.add_trace(go.Scatter(
                    x=fechas, y=tmin2, mode='lines+markers',
                    name=f'{estacion2} - TMIN', line=dict(color=COLORS['station2']['tmin'], width=2, dash='dot'),
                    marker=dict(size=4, symbol='square')
                ))

                # Normales estación 2
                tmax2_normal, tmin2_normal, pp2_normal = get_normal_values(estacion2, fechas)
                fig_temp.add_trace(go.Scatter(
                    x=fechas, y=tmax2_normal, mode='lines',
                    name=f'{estacion2} - TMAX Normal', line=dict(color=COLORS['station2']['tmax_normal'], width=2, dash='dashdot'),
                    showlegend=True
                ))
                fig_temp.add_trace(go.Scatter(
                    x=fechas, y=tmin2_normal, mode='lines',
                    name=f'{estacion2} - TMIN Normal', line=dict(color=COLORS['station2']['tmin_normal'], width=2, dash='dashdot'),
                    showlegend=True
                ))

        fig_temp.update_layout(
            xaxis=dict(title="Fecha", tickformat='%d/%m/%Y'),
            yaxis=dict(title="Temperatura (°C)"),
            hovermode='x unified', template='plotly_white', height=500,
            legend=dict(orientation="v", yanchor="top", y=0.99, xanchor="left", x=1.01)
        )

        # GRÁFICO DE PRECIPITACIÓN
        fig_pp = go.Figure()

        # Estación 1 - PP con puntos
        fig_pp.add_trace(go.Scatter(
            x=fechas, y=pp1, mode='lines+markers',
            name=f'{estacion1} - PP',
            line=dict(color=COLORS['station1']['pp'], width=2),
            marker=dict(size=6)
        ))

        # Agregar normal PP para estación 1
        fig_pp.add_trace(go.Scatter(
            x=fechas, y=pp1_normal, mode='lines',
            name=f'{estacion1} - PP Normal',
            line=dict(color=COLORS['station1']['pp_normal'], width=2, dash='dash'),
            showlegend=True
        ))

        if estacion2 and pp2:
            # Estación 2 - PP con puntos
            fig_pp.add_trace(go.Scatter(
                x=fechas, y=pp2, mode='lines+markers',
                name=f'{estacion2} - PP',
                line=dict(color=COLORS['station2']['pp'], width=2, dash='dot'),
                marker=dict(size=6, symbol='square')
            ))

            # Agregar normal PP para estación 2
            if pp2_normal:
                fig_pp.add_trace(go.Scatter(
                    x=fechas, y=pp2_normal, mode='lines',
                    name=f'{estacion2} - PP Normal',
                    line=dict(color=COLORS['station2']['pp_normal'], width=2, dash='dashdot'),
                    showlegend=True
                ))

        fig_pp.update_layout(
            xaxis=dict(title="Fecha", tickformat='%d/%m/%Y'),
            yaxis=dict(title="Precipitación (mm)"),
            hovermode='x unified', template='plotly_white', height=400,
            legend=dict(orientation="v", yanchor="top", y=0.99, xanchor="left", x=1.01)
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

        if estacion2 and tmax2 and tmin2 and pp2:
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

        # Mensaje con info de meses cargados
        num_meses = len(months_to_load)
        if num_meses == 1:
            status_msg = f"✅ Datos cargados: {len(fechas)} días del {months_to_load[0][1]}/{months_to_load[0][0]}"
        else:
            status_msg = f"✅ Datos cargados: {len(fechas)} días de {num_meses} meses"
        if estacion2 and tmax2:
            status_msg += f" | Comparando 2 estaciones"

        return fig_temp, fig_pp, dmc.Stack(gap="lg", children=stats_children), \
               dmc.Alert(status_msg, color="green", icon=DashIconify(icon="mdi:check-circle"))

    except Exception as e:
        return no_update, no_update, no_update, dmc.Alert(
            f"Error al cargar datos: {str(e)}", color="red", icon=DashIconify(icon="mdi:alert")
        )
