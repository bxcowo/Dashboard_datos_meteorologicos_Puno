"""
Dashboard de Control Semanal - Datos Meteorológicos Puno
Con datos normales, comparación multi-estación y gráficos interactivos
"""
from dash import Dash, html, dcc, callback, Input, Output, State, no_update
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys
import calendar

# Importar módulos de datos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.file_managment import get_registro_diario


# Colores para las estaciones y variables
COLORS = {
    'station1': {
        'tmax': '#fa5252',           # Rojo para TMAX diaria
        'tmin': '#339af0',           # Azul para TMIN diaria
        'pp': '#51cf66',             # Verde para PP diaria
        'tmax_normal': '#9333ea',    # Morado oscuro para TMAX Normal
        'tmin_normal': '#c084fc',    # Morado claro para TMIN Normal
        'pp_normal': '#eab308'       # Amarillo para PP Normal
    },
    'station2': {
        'tmax': '#f03e3e',           # Rojo oscuro para TMAX diaria est2
        'tmin': '#1c7ed6',           # Azul oscuro para TMIN diaria est2
        'pp': '#37b24d',             # Verde oscuro para PP diaria est2
        'tmax_normal': '#7c3aed',    # Morado oscuro para TMAX Normal est2
        'tmin_normal': '#a78bfa',    # Morado medio para TMIN Normal est2
        'pp_normal': '#facc15'       # Amarillo claro para PP Normal est2
    }
}


def create_app(normales_data=None, registro_mensual=None, access_token=None):
    """
    Crea la aplicación Dash con Dash Mantine Components v2

    Args:
        normales_data: Dict con DataFrames de valores normales (TMAX, TMIN, PP)
        registro_mensual: DataFrame con registro mensual
        access_token: Token de acceso para Microsoft Graph API
    """

    app = Dash(__name__, suppress_callback_exceptions=True)

    # Tema personalizado
    theme = {
        "fontFamily": "Inter, sans-serif",
        "primaryColor": "blue",
        "defaultRadius": "md",
    }

    # Lista de estaciones
    stations_list = normales_data['TMAX'].index.tolist() if normales_data else []

    # Layout principal
    app.layout = dmc.MantineProvider(
        theme=theme,
        children=[
            # Store para guardar datos
            dcc.Store(id='access-token-store', data=access_token),
            dcc.Store(id='normales-store', data={
                'TMAX': normales_data['TMAX'].to_dict('index') if normales_data else {},
                'TMIN': normales_data['TMIN'].to_dict('index') if normales_data else {},
                'PP': normales_data['PP'].to_dict('index') if normales_data else {}
            }),

            dmc.Container(
                fluid=True,
                style={"padding": "20px"},
                children=[
                    dmc.Stack(
                        gap="md",
                        children=[
                            # Header
                            dmc.Paper(
                                p="md",
                                shadow="sm",
                                radius="md",
                                children=[
                                    dmc.Group(
                                        justify="space-between",
                                        children=[
                                            dmc.Stack(
                                                gap="xs",
                                                children=[
                                                    dmc.Title(
                                                        "Dashboard Meteorológico - Puno",
                                                        order=2,
                                                        c="blue.7"
                                                    ),
                                                    dmc.Text(
                                                        "Comparación de Datos Diarios vs Valores Normales (1991-2020)",
                                                        size="sm",
                                                        c="dimmed"
                                                    ),
                                                ]
                                            ),
                                            dmc.ActionIcon(
                                                DashIconify(icon="mdi:weather-partly-cloudy", width=28),
                                                size="xl",
                                                variant="light",
                                                color="blue"
                                            ),
                                        ]
                                    )
                                ]
                            ),

                            # Panel de control
                            dmc.Paper(
                                p="md",
                                shadow="sm",
                                radius="md",
                                withBorder=True,
                                children=[
                                    dmc.Stack(
                                        gap="md",
                                        children=[
                                            dmc.Group(
                                                justify="space-between",
                                                children=[
                                                    dmc.Title("Configuración de Consulta", order=4),
                                                    dmc.Badge("Datos Diarios + Normales", color="green", variant="light")
                                                ]
                                            ),

                                            dmc.Grid(
                                                gutter="md",
                                                children=[
                                                    # Fecha inicio
                                                    dmc.GridCol(
                                                        span={"base": 12, "sm": 6, "md": 3},
                                                        children=[
                                                            dmc.Stack(
                                                                gap="xs",
                                                                children=[
                                                                    dmc.Text("Fecha Inicio", size="sm", fw=500),
                                                                    dcc.DatePickerSingle(
                                                                        id='fecha-inicio',
                                                                        date=datetime(2025, 10, 1).date(),
                                                                        display_format='DD/MM/YYYY',
                                                                        style={'width': '100%'}
                                                                    )
                                                                ]
                                                            )
                                                        ]
                                                    ),

                                                    # Fecha fin
                                                    dmc.GridCol(
                                                        span={"base": 12, "sm": 6, "md": 3},
                                                        children=[
                                                            dmc.Stack(
                                                                gap="xs",
                                                                children=[
                                                                    dmc.Text("Fecha Fin", size="sm", fw=500),
                                                                    dcc.DatePickerSingle(
                                                                        id='fecha-fin',
                                                                        date=datetime(2025, 10, 9).date(),
                                                                        display_format='DD/MM/YYYY',
                                                                        style={'width': '100%'}
                                                                    )
                                                                ]
                                                            )
                                                        ]
                                                    ),

                                                    # Selector de estación 1
                                                    dmc.GridCol(
                                                        span={"base": 12, "sm": 6, "md": 3},
                                                        children=[
                                                            dmc.Stack(
                                                                gap="xs",
                                                                children=[
                                                                    dmc.Group(
                                                                        gap="xs",
                                                                        children=[
                                                                            dmc.Text("Estación Principal", size="sm", fw=500),
                                                                            dmc.Badge("Obligatorio", size="xs", color="red", variant="light")
                                                                        ]
                                                                    ),
                                                                    dmc.Select(
                                                                        id='estacion-selector-1',
                                                                        data=[
                                                                            {"value": station, "label": station}
                                                                            for station in stations_list
                                                                        ],
                                                                        value=stations_list[0] if stations_list else None,
                                                                        searchable=True,
                                                                        clearable=False,
                                                                    )
                                                                ]
                                                            )
                                                        ]
                                                    ),

                                                    # Selector de estación 2
                                                    dmc.GridCol(
                                                        span={"base": 12, "sm": 6, "md": 3},
                                                        children=[
                                                            dmc.Stack(
                                                                gap="xs",
                                                                children=[
                                                                    dmc.Group(
                                                                        gap="xs",
                                                                        children=[
                                                                            dmc.Text("Estación Comparación", size="sm", fw=500),
                                                                            dmc.Badge("Opcional", size="xs", color="blue", variant="light")
                                                                        ]
                                                                    ),
                                                                    dmc.Select(
                                                                        id='estacion-selector-2',
                                                                        data=[
                                                                            {"value": station, "label": station}
                                                                            for station in stations_list
                                                                        ],
                                                                        value=None,
                                                                        placeholder="Selecciona para comparar...",
                                                                        searchable=True,
                                                                        clearable=True,
                                                                    )
                                                                ]
                                                            )
                                                        ]
                                                    ),
                                                ]
                                            ),

                                            # Botón cargar
                                            dmc.Group(
                                                justify="flex-end",
                                                children=[
                                                    dmc.Button(
                                                        "Cargar Datos",
                                                        id='cargar-datos-btn',
                                                        leftSection=DashIconify(icon="mdi:refresh", width=20),
                                                        size="md",
                                                        variant="filled"
                                                    )
                                                ]
                                            ),

                                            # Indicador de estado
                                            html.Div(id='loading-status')
                                        ]
                                    )
                                ]
                            ),

                            # Gráfico 1: Temperaturas
                            dmc.Paper(
                                p="md",
                                shadow="sm",
                                radius="md",
                                withBorder=True,
                                children=[
                                    dmc.Stack(
                                        gap="md",
                                        children=[
                                            dmc.Group(
                                                justify="space-between",
                                                children=[
                                                    dmc.Title("🌡️ Temperaturas (Máxima y Mínima)", order=4),
                                                    dmc.Badge("Datos Diarios + Normales", color="orange", variant="light")
                                                ]
                                            ),
                                            dcc.Loading(
                                                id="loading-temp-graph",
                                                type="default",
                                                children=[
                                                    dcc.Graph(
                                                        id="temperatura-graph",
                                                        config={
                                                            'displayModeBar': True,
                                                            'displaylogo': False,
                                                            'scrollZoom': True,
                                                        },
                                                        style={'height': '500px'}
                                                    )
                                                ]
                                            )
                                        ]
                                    )
                                ]
                            ),

                            # Gráfico 2: Precipitación
                            dmc.Paper(
                                p="md",
                                shadow="sm",
                                radius="md",
                                withBorder=True,
                                children=[
                                    dmc.Stack(
                                        gap="md",
                                        children=[
                                            dmc.Group(
                                                justify="space-between",
                                                children=[
                                                    dmc.Title("💧 Precipitación", order=4),
                                                    dmc.Badge("Datos Diarios + Normales", color="teal", variant="light")
                                                ]
                                            ),
                                            dcc.Loading(
                                                id="loading-pp-graph",
                                                type="default",
                                                children=[
                                                    dcc.Graph(
                                                        id="precipitacion-graph",
                                                        config={
                                                            'displayModeBar': True,
                                                            'displaylogo': False,
                                                            'scrollZoom': True,
                                                        },
                                                        style={'height': '400px'}
                                                    )
                                                ]
                                            )
                                        ]
                                    )
                                ]
                            ),

                            # Estadísticas
                            dmc.Paper(
                                p="md",
                                shadow="sm",
                                radius="md",
                                withBorder=True,
                                children=[
                                    dmc.Stack(
                                        gap="md",
                                        children=[
                                            dmc.Title("📊 Estadísticas del Período", order=4),
                                            html.Div(id='estadisticas-container')
                                        ]
                                    )
                                ]
                            ),

                            # Footer
                            dmc.Paper(
                                p="sm",
                                mt="xl",
                                children=[
                                    dmc.Group(
                                        justify="center",
                                        children=[
                                            dmc.Text(
                                                "Dashboard de Datos Meteorológicos - SENAMHI Puno",
                                                size="xs",
                                                c="dimmed"
                                            ),
                                        ]
                                    )
                                ]
                            )
                        ]
                    )
                ]
            )
        ]
    )

    # Callback principal
    @app.callback(
        [Output('temperatura-graph', 'figure'),
         Output('precipitacion-graph', 'figure'),
         Output('estadisticas-container', 'children'),
         Output('loading-status', 'children')],
        [Input('cargar-datos-btn', 'n_clicks')],
        [State('fecha-inicio', 'date'),
         State('fecha-fin', 'date'),
         State('estacion-selector-1', 'value'),
         State('estacion-selector-2', 'value'),
         State('access-token-store', 'data'),
         State('normales-store', 'data')]
    )
    def update_graphs(n_clicks, fecha_inicio, fecha_fin, estacion1, estacion2, token, normales_dict):
        if not n_clicks or not fecha_inicio or not fecha_fin or not estacion1:
            # Gráficos vacíos iniciales
            fig_temp = go.Figure()
            fig_temp.update_layout(
                title="Selecciona un rango de fechas y presiona 'Cargar Datos'",
                template='plotly_white',
                height=500
            )
            fig_pp = go.Figure()
            fig_pp.update_layout(
                title="Selecciona un rango de fechas y presiona 'Cargar Datos'",
                template='plotly_white',
                height=400
            )
            return fig_temp, fig_pp, dmc.Text("No hay datos cargados", c="dimmed"), None

        try:
            # Convertir fechas
            start_date = datetime.fromisoformat(fecha_inicio)
            end_date = datetime.fromisoformat(fecha_fin)

            # Validaciones
            if start_date > end_date:
                return no_update, no_update, no_update, dmc.Alert(
                    "La fecha de inicio debe ser anterior a la fecha fin",
                    color="red",
                    icon=DashIconify(icon="mdi:alert")
                )

            if estacion2 and estacion1 == estacion2:
                return no_update, no_update, no_update, dmc.Alert(
                    "Las estaciones deben ser diferentes para comparar",
                    color="yellow",
                    icon=DashIconify(icon="mdi:alert")
                )

            # Generar lista de fechas
            date_list = []
            current_date = start_date
            while current_date <= end_date:
                date_list.append(current_date)
                current_date += timedelta(days=1)

            # Función para cargar datos de una estación
            def load_station_data(estacion):
                fechas = []
                tmax_values = []
                tmin_values = []
                pp_values = []

                for date in date_list:
                    try:
                        df_dia = get_registro_diario(
                            "AndreaProyecto/REGISTRO DIARIO",
                            date.year,
                            date.month,
                            date.day,
                            token
                        )

                        if estacion in df_dia.index.get_level_values('ESTACION'):
                            row = df_dia.xs(estacion, level='ESTACION').iloc[0]
                            fechas.append(date)
                            tmax_values.append(row['TMAX'])
                            tmin_values.append(row['TMIN'])
                            pp_values.append(row['PP'])

                    except Exception:
                        continue

                return fechas, tmax_values, tmin_values, pp_values

            # Cargar datos estación 1
            fechas1, tmax1, tmin1, pp1 = load_station_data(estacion1)

            if not fechas1:
                return no_update, no_update, no_update, dmc.Alert(
                    f"No se encontraron datos para la estación {estacion1} en el rango seleccionado",
                    color="yellow",
                    icon=DashIconify(icon="mdi:alert")
                )

            # Preparar datos normales para estación 1
            # Con to_dict('index'), la estructura es: {'ARAPA': {'Enero': 16.0, 'Febrero': 16.0, ...}, ...}
            normales_tmax1 = list(normales_dict['TMAX'][estacion1].values()) if estacion1 in normales_dict['TMAX'] else None
            normales_tmin1 = list(normales_dict['TMIN'][estacion1].values()) if estacion1 in normales_dict['TMIN'] else None
            normales_pp1 = list(normales_dict['PP'][estacion1].values()) if estacion1 in normales_dict['PP'] else None

            # Crear fechas mensuales para normales
            meses = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC']

            # GRÁFICO 1: TEMPERATURAS
            fig_temp = go.Figure()

            # Estación 1 - TMAX diaria
            fig_temp.add_trace(go.Scatter(
                x=fechas1,
                y=tmax1,
                mode='lines+markers',
                name=f'{estacion1} - TMAX (Diaria)',
                line=dict(color=COLORS['station1']['tmax'], width=1.5),
                marker=dict(size=3),
                hovertemplate=f'<b>{estacion1} - TMAX Diaria</b><br>Fecha: %{{x|%d/%m/%Y}}<br>Valor: %{{y:.1f}}°C<extra></extra>',
            ))

            # Estación 1 - TMIN diaria
            fig_temp.add_trace(go.Scatter(
                x=fechas1,
                y=tmin1,
                mode='lines+markers',
                name=f'{estacion1} - TMIN (Diaria)',
                line=dict(color=COLORS['station1']['tmin'], width=1.5),
                marker=dict(size=3),
                hovertemplate=f'<b>{estacion1} - TMIN Diaria</b><br>Fecha: %{{x|%d/%m/%Y}}<br>Valor: %{{y:.1f}}°C<extra></extra>',
            ))

            # Estación 1 - Normales TMAX (líneas horizontales por mes)
            if normales_tmax1 is not None:
                # Determinar qué meses están en el rango seleccionado
                months_in_range = set()
                current = start_date
                while current <= end_date:
                    months_in_range.add(current.month)
                    current += timedelta(days=1)

                # Crear líneas horizontales para cada mes en el rango
                for month in sorted(months_in_range):
                    # Calcular el primer y último día del mes dentro del rango
                    import calendar
                    year = start_date.year if start_date.month <= month <= end_date.month else end_date.year

                    # Primer día del mes o start_date, lo que sea mayor
                    first_day_of_month = datetime(year, month, 1)
                    if first_day_of_month < start_date:
                        first_day_of_month = start_date

                    # Último día del mes o end_date, lo que sea menor
                    last_day_of_month = datetime(year, month, calendar.monthrange(year, month)[1])
                    if last_day_of_month > end_date:
                        last_day_of_month = end_date

                    # TMAX Normal - línea horizontal
                    tmax_normal_value = normales_tmax1[month - 1]
                    fig_temp.add_trace(go.Scatter(
                        x=[first_day_of_month, last_day_of_month],
                        y=[tmax_normal_value, tmax_normal_value],
                        mode='lines',
                        name=f'{estacion1} - TMAX Normal (1991-2020)',
                        line=dict(color=COLORS['station1']['tmax_normal'], width=4),
                        hovertemplate=f'<b>{estacion1} - TMAX Normal</b><br>Mes: {calendar.month_name[month]}<br>Valor: {tmax_normal_value:.1f}°C<extra></extra>',
                        legendgroup='tmax_normal_1',
                        showlegend=(month == sorted(months_in_range)[0])
                    ))

                    # TMIN Normal - línea horizontal
                    if normales_tmin1 is not None:
                        tmin_normal_value = normales_tmin1[month - 1]
                        fig_temp.add_trace(go.Scatter(
                            x=[first_day_of_month, last_day_of_month],
                            y=[tmin_normal_value, tmin_normal_value],
                            mode='lines',
                            name=f'{estacion1} - TMIN Normal (1991-2020)',
                            line=dict(color=COLORS['station1']['tmin_normal'], width=4),
                            hovertemplate=f'<b>{estacion1} - TMIN Normal</b><br>Mes: {calendar.month_name[month]}<br>Valor: {tmin_normal_value:.1f}°C<extra></extra>',
                            legendgroup='tmin_normal_1',
                            showlegend=(month == sorted(months_in_range)[0])
                        ))

            # Si hay estación 2
            fechas2, tmax2, tmin2, pp2 = None, None, None, None
            if estacion2:
                fechas2, tmax2, tmin2, pp2 = load_station_data(estacion2)

                if fechas2:
                    # Datos diarios estación 2
                    fig_temp.add_trace(go.Scatter(
                        x=fechas2,
                        y=tmax2,
                        mode='lines+markers',
                        name=f'{estacion2} - TMAX (Diaria)',
                        line=dict(color=COLORS['station2']['tmax'], width=1.5, dash='dot'),
                        marker=dict(size=3, symbol='square'),
                        hovertemplate=f'<b>{estacion2} - TMAX Diaria</b><br>Fecha: %{{x|%d/%m/%Y}}<br>Valor: %{{y:.1f}}°C<extra></extra>',
                    ))

                    fig_temp.add_trace(go.Scatter(
                        x=fechas2,
                        y=tmin2,
                        mode='lines+markers',
                        name=f'{estacion2} - TMIN (Diaria)',
                        line=dict(color=COLORS['station2']['tmin'], width=1.5, dash='dot'),
                        marker=dict(size=3, symbol='square'),
                        hovertemplate=f'<b>{estacion2} - TMIN Diaria</b><br>Fecha: %{{x|%d/%m/%Y}}<br>Valor: %{{y:.1f}}°C<extra></extra>',
                    ))

                    # Normales estación 2 - líneas horizontales por mes
                    normales_tmax2 = list(normales_dict['TMAX'][estacion2].values()) if estacion2 in normales_dict['TMAX'] else None
                    normales_tmin2 = list(normales_dict['TMIN'][estacion2].values()) if estacion2 in normales_dict['TMIN'] else None

                    if normales_tmax2 is not None:
                        # Usar los mismos meses que estación 1
                        months_in_range2 = set()
                        current = start_date
                        while current <= end_date:
                            months_in_range2.add(current.month)
                            current += timedelta(days=1)

                        for month in sorted(months_in_range2):
                            year = start_date.year if start_date.month <= month <= end_date.month else end_date.year

                            first_day_of_month = datetime(year, month, 1)
                            if first_day_of_month < start_date:
                                first_day_of_month = start_date

                            last_day_of_month = datetime(year, month, calendar.monthrange(year, month)[1])
                            if last_day_of_month > end_date:
                                last_day_of_month = end_date

                            # TMAX Normal estación 2
                            tmax_normal_value2 = normales_tmax2[month - 1]
                            fig_temp.add_trace(go.Scatter(
                                x=[first_day_of_month, last_day_of_month],
                                y=[tmax_normal_value2, tmax_normal_value2],
                                mode='lines',
                                name=f'{estacion2} - TMAX Normal (1991-2020)',
                                line=dict(color=COLORS['station2']['tmax_normal'], width=4),
                                hovertemplate=f'<b>{estacion2} - TMAX Normal</b><br>Mes: {calendar.month_name[month]}<br>Valor: {tmax_normal_value2:.1f}°C<extra></extra>',
                                legendgroup='tmax_normal_2',
                                showlegend=(month == sorted(months_in_range2)[0])
                            ))

                            # TMIN Normal estación 2
                            if normales_tmin2 is not None:
                                tmin_normal_value2 = normales_tmin2[month - 1]
                                fig_temp.add_trace(go.Scatter(
                                    x=[first_day_of_month, last_day_of_month],
                                    y=[tmin_normal_value2, tmin_normal_value2],
                                    mode='lines',
                                    name=f'{estacion2} - TMIN Normal (1991-2020)',
                                    line=dict(color=COLORS['station2']['tmin_normal'], width=4),
                                    hovertemplate=f'<b>{estacion2} - TMIN Normal</b><br>Mes: {calendar.month_name[month]}<br>Valor: {tmin_normal_value2:.1f}°C<extra></extra>',
                                    legendgroup='tmin_normal_2',
                                    showlegend=(month == sorted(months_in_range2)[0])
                                ))

            # Configurar gráfico de temperatura
            fig_temp.update_layout(
                xaxis=dict(
                    title="Fecha",
                    rangeslider=dict(visible=True),
                    type='date',
                    dtick=86400000,  # 1 día en milisegundos
                    tickformat='%d/%m/%Y'
                ),
                yaxis=dict(title="Temperatura (°C)"),
                hovermode='x unified',
                template='plotly_white',
                height=500,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=1.01
                ),
                dragmode='pan'
            )

            # GRÁFICO 2: PRECIPITACIÓN
            fig_pp = go.Figure()

            # Estación 1 - PP diaria
            fig_pp.add_trace(go.Scatter(
                x=fechas1,
                y=pp1,
                mode='lines+markers',
                name=f'{estacion1} - PP (Diaria)',
                line=dict(color=COLORS['station1']['pp'], width=1.5),
                marker=dict(size=3),
                hovertemplate=f'<b>{estacion1} - PP Diaria</b><br>Fecha: %{{x|%d/%m/%Y}}<br>Valor: %{{y:.1f}}mm<extra></extra>',
            ))

            # Estación 1 - PP normal (líneas horizontales por mes)
            if normales_pp1 is not None:
                # Meses en el rango
                months_in_range_pp = set()
                current = start_date
                while current <= end_date:
                    months_in_range_pp.add(current.month)
                    current += timedelta(days=1)

                for month in sorted(months_in_range_pp):
                    year = start_date.year if start_date.month <= month <= end_date.month else end_date.year

                    first_day_of_month = datetime(year, month, 1)
                    if first_day_of_month < start_date:
                        first_day_of_month = start_date

                    last_day_of_month = datetime(year, month, calendar.monthrange(year, month)[1])
                    if last_day_of_month > end_date:
                        last_day_of_month = end_date

                    # PP Normal - línea horizontal
                    pp_normal_value = normales_pp1[month - 1]
                    fig_pp.add_trace(go.Scatter(
                        x=[first_day_of_month, last_day_of_month],
                        y=[pp_normal_value, pp_normal_value],
                        mode='lines',
                        name=f'{estacion1} - PP Normal (1991-2020)',
                        line=dict(color=COLORS['station1']['pp_normal'], width=4),
                        hovertemplate=f'<b>{estacion1} - PP Normal</b><br>Mes: {calendar.month_name[month]}<br>Valor: {pp_normal_value:.1f}mm<extra></extra>',
                        legendgroup='pp_normal_1',
                        showlegend=(month == sorted(months_in_range_pp)[0])
                    ))

            # Estación 2 - PP
            if estacion2 and fechas2:
                fig_pp.add_trace(go.Scatter(
                    x=fechas2,
                    y=pp2,
                    mode='lines+markers',
                    name=f'{estacion2} - PP (Diaria)',
                    line=dict(color=COLORS['station2']['pp'], width=1.5, dash='dot'),
                    marker=dict(size=3, symbol='square'),
                    hovertemplate=f'<b>{estacion2} - PP Diaria</b><br>Fecha: %{{x|%d/%m/%Y}}<br>Valor: %{{y:.1f}}mm<extra></extra>',
                ))

                # PP Normal estación 2 (líneas horizontales por mes)
                normales_pp2 = list(normales_dict['PP'][estacion2].values()) if estacion2 in normales_dict['PP'] else None
                if normales_pp2 is not None:
                    months_in_range_pp2 = set()
                    current = start_date
                    while current <= end_date:
                        months_in_range_pp2.add(current.month)
                        current += timedelta(days=1)

                    for month in sorted(months_in_range_pp2):
                        year = start_date.year if start_date.month <= month <= end_date.month else end_date.year

                        first_day_of_month = datetime(year, month, 1)
                        if first_day_of_month < start_date:
                            first_day_of_month = start_date

                        last_day_of_month = datetime(year, month, calendar.monthrange(year, month)[1])
                        if last_day_of_month > end_date:
                            last_day_of_month = end_date

                        pp_normal_value2 = normales_pp2[month - 1]
                        fig_pp.add_trace(go.Scatter(
                            x=[first_day_of_month, last_day_of_month],
                            y=[pp_normal_value2, pp_normal_value2],
                            mode='lines',
                            name=f'{estacion2} - PP Normal (1991-2020)',
                            line=dict(color=COLORS['station2']['pp_normal'], width=4),
                            hovertemplate=f'<b>{estacion2} - PP Normal</b><br>Mes: {calendar.month_name[month]}<br>Valor: {pp_normal_value2:.1f}mm<extra></extra>',
                            legendgroup='pp_normal_2',
                            showlegend=(month == sorted(months_in_range_pp2)[0])
                        ))

            # Configurar gráfico de precipitación
            fig_pp.update_layout(
                xaxis=dict(
                    title="Fecha",
                    rangeslider=dict(visible=True),
                    type='date',
                    dtick=86400000,  # 1 día en milisegundos
                    tickformat='%d/%m/%Y'
                ),
                yaxis=dict(title="Precipitación (mm)"),
                hovermode='x unified',
                template='plotly_white',
                height=400,
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=1.01
                ),
                dragmode='pan'
            )

            # Estadísticas
            stats_children = []

            # Estadísticas Estación 1
            stats_children.append(
                dmc.Stack(
                    gap="xs",
                    children=[
                        dmc.Title(f"📍 {estacion1}", order=5, c="blue.7"),
                        dmc.Grid(
                            gutter="md",
                            children=[
                                create_stat_card("TMAX Promedio", tmax1, "°C", "red.6"),
                                create_stat_card("TMIN Promedio", tmin1, "°C", "blue.6"),
                                create_stat_card("PP Total", pp1, "mm", "green.6", is_total=True),
                            ]
                        )
                    ]
                )
            )

            # Estadísticas Estación 2
            if estacion2 and fechas2:
                stats_children.append(
                    dmc.Stack(
                        gap="xs",
                        children=[
                            dmc.Title(f"📍 {estacion2}", order=5, c="violet.7"),
                            dmc.Grid(
                                gutter="md",
                                children=[
                                    create_stat_card("TMAX Promedio", tmax2, "°C", "red.6"),
                                    create_stat_card("TMIN Promedio", tmin2, "°C", "blue.6"),
                                    create_stat_card("PP Total", pp2, "mm", "green.6", is_total=True),
                                ]
                            )
                        ]
                    )
                )

            stats = dmc.Stack(gap="lg", children=stats_children)

            status_msg = f"✅ Datos cargados: {len(fechas1)} días"
            if estacion2 and fechas2:
                status_msg += f" | Comparando 2 estaciones"

            status = dmc.Alert(
                status_msg,
                color="green",
                icon=DashIconify(icon="mdi:check-circle")
            )

            return fig_temp, fig_pp, stats, status

        except Exception as e:
            return no_update, no_update, no_update, dmc.Alert(
                f"Error al cargar datos: {str(e)}",
                color="red",
                icon=DashIconify(icon="mdi:alert")
            )

    return app


def create_stat_card(title, values, unit, color, is_total=False):
    """Crea una tarjeta de estadística"""
    if is_total:
        main_value = sum(values)
        sub_text = f"Max: {max(values):.1f}{unit} | Promedio: {sum(values)/len(values):.1f}{unit}"
    else:
        main_value = sum(values) / len(values)
        sub_text = f"Max: {max(values):.1f}{unit} | Min: {min(values):.1f}{unit}"

    return dmc.GridCol(
        span={"base": 12, "sm": 6, "md": 4},
        children=[
            dmc.Paper(
                p="md",
                withBorder=True,
                radius="md",
                children=[
                    dmc.Stack(
                        gap="xs",
                        children=[
                            dmc.Text(title, size="sm", c="dimmed"),
                            dmc.Text(f"{main_value:.1f}{unit}", size="xl", fw=700, c=color),
                            dmc.Text(sub_text, size="xs", c="dimmed")
                        ]
                    )
                ]
            )
        ]
    )
