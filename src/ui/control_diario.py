from data.file_managment import get_registro_diario, convert_month
from dash import Output, Input, callback, dcc
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
                        w=400,
                        mb=10
                    ),
                    dmc.DatePickerInput(
                        id="registro-diario-date-selector",
                        label="Selecciona una fecha a analizar",
                        minDate=date(1985, 1, 1),
                        value=date(2025, 10, 22),
                        size="lg",
                        w=400,
                        mb=10
                    )
                ],
                cols=2,
                spacing="md"
            )
        ],
        strategy="grid",
        fluid=True),
        dcc.Graph(id="registro-diario-graph")
    ],
    theme=dmc.DEFAULT_THEME)

    return content


@callback(
    Output('registro-diario-graph', 'figure'),
    Input('variable-selector', 'value'),
    Input('registro-diario-date-selector', 'value')
)
def create_graph(variable, fecha):
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

    # Extraemos los datos esenciales
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
            go.Bar(
                x=estaciones_zona,
                y=data_zona,
                name=f"Registro {fecha_obj.strftime(nuevo_formato_fecha)}",
                legendgroup="registro",
                showlegend=(i == 0),
                marker_color=color_registro
            ),
            row=(i // 2) + 1,
            col=(i % 2) + 1
        )

        fig.add_trace(
            go.Bar(
                x=estaciones_zona,
                y=data_normal_zona,
                name=f"Normal histórica ({convert_month(fecha_obj.month)})",
                legendgroup="normal",
                showlegend=(i == 0),
                marker_color=color_normal
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
        gridcolor='gray'
    )

    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='gray'
    )

    return fig
