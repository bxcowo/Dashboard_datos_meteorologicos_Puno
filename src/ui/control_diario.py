from data.file_managment import get_registro_diario, convert_month
from dash import Output, Input, State, callback, dcc, html
from dash_iconify import DashIconify
from plotly.subplots import make_subplots
from datetime import date, datetime
from cache import data_cache
import dash_mantine_components as dmc
import plotly.graph_objects as go

DICCIONARIO_VARIABLES = {
    'TMAX' : 'temperatura máxima',
    'TMIN' : 'temperatura mínima',
    'PP' : 'precipitación'
}

def registro_diario_layout():
    content = dmc.MantineProvider([
        dmc.Container([
            dmc.Paper(p="md", shadow="sm", radius="md", withBorder=True, children=[
                dmc.Stack(gap="md", children=[
                    dmc.SimpleGrid(
                        children=[
                            dmc.Select(
                                id="variable-selector",
                                label="Selecciona la variable a representar",
                                value="TMAX",
                                data=[
                                    {"value" : "TMAX", "label" : "Temperatura máxima"},
                                    {"value" : "TMIN", "label" : "Temperatura mínima"},
                                    {"value" : "PP", "label" : "Precipitación"},
                                ],
                                size="lg",
                                w=400
                            ),
                            dmc.DatePickerInput(
                                id="registro-diario-date-selector",
                                label="Selecciona una fecha a analizar",
                                minDate=date(1985, 1, 1),
                                value=None,
                                size="lg",
                                w=400
                            )
                        ],
                        cols=2,
                        spacing="md"
                    ),
                    dmc.Group(justify="flex-end", children=[
                        dmc.Button("Cargar Datos", id='cargar-datos-btn-diario',
                                  leftSection=DashIconify(icon="mdi:refresh", width=20), size="md", variant="filled")
                    ]),
                    html.Div(id='loading-status-diario')
                ])
            ]),
        ],
        strategy="grid",
        fluid=True),
        dcc.Graph(id="registro-diario-graph")
    ])

    return content


@callback(
    [Output('registro-diario-graph', 'figure'), Output('loading-status-diario', 'children')],
    [Input('cargar-datos-btn-diario', 'n_clicks')],
    [State('variable-selector', 'value'), State('registro-diario-date-selector', 'value')]
)
def create_graph(n_clicks, variable, fecha):
    if not n_clicks or not fecha:
        empty_fig = go.Figure(layout=dict(
            title="Selecciona una fecha y presiona 'Cargar Datos'",
            template='plotly_white'
        ))
        return empty_fig, None
    formato_fecha = "%Y-%m-%d"
    nuevo_formato_fecha = "%d/%m/%Y"
    fecha_obj = datetime.strptime(fecha, formato_fecha)
    zonas = ["SELVA Y VALLES INTERANDINOS", "ALTIPLANO NORTE", "ALTIPLANO CENTRO", "ALTIPLANO SUR"]

    if data_cache.get(fecha) is None:
        data_cache[fecha] = get_registro_diario(
            year=fecha_obj.year,
            month=fecha_obj.month,
            day=fecha_obj.day,
        )

    data_registro_diario = data_cache[fecha]
    data_normal = data_cache[f"NORMAL_{variable}"][convert_month(fecha_obj.month)]

    fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=zonas,
            vertical_spacing=0.12,
            horizontal_spacing=0.08,
        )

    color_registro = '#636EFA'
    color_normal = '#EF553B'

    for i in range(len(zonas)):
        data_zona = data_registro_diario.loc[zonas[i], variable]
        estaciones_zona = data_zona.index.to_numpy()
        data_normal_zona = data_normal.reindex(estaciones_zona)

        fig.add_trace(
            go.Scatter(
                x=estaciones_zona,
                y=data_zona,
                mode='lines+markers',
                name=f"Registro {fecha_obj.strftime(nuevo_formato_fecha)}",
                legendgroup="registro",
                showlegend=(i == 0),
                line=dict(color=color_registro, width=2),
                marker=dict(size=8)
            ),
            row=(i // 2) + 1,
            col=(i % 2) + 1
        )

        fig.add_trace(
            go.Scatter(
                x=estaciones_zona,
                y=data_normal_zona,
                mode='lines+markers',
                name=f"Normal histórica ({convert_month(fecha_obj.month)})",
                legendgroup="normal",
                showlegend=(i == 0),
                line=dict(color=color_normal, width=2),
                marker=dict(size=8)
            ),
            row=(i // 2) + 1,
            col=(i % 2) + 1
        )

    fig.update_layout(
        title={
            'text' : f"Análisis de {DICCIONARIO_VARIABLES[variable]} - {fecha_obj.strftime(nuevo_formato_fecha)}",
            'x' : 0.5,
            'xanchor' : 'center',
            'font' : { 'size' : 35 }
        },
        height=1400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1,
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=100, b=50, l=50, r=50)
    )

    fig.update_xaxes(
        tickangle=-45,
        showgrid=True,
        gridwidth=1,
        gridcolor='lightgray'
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='lightgray'
    )

    return fig, dmc.Alert(
        f"Datos cargados para {fecha_obj.strftime(nuevo_formato_fecha)}",
        color="green",
        icon=DashIconify(icon="mdi:check-circle")
    )
