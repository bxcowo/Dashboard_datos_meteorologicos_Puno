import dash_mantine_components as dmc
from dash import Dash, Input, Output, callback, html
from dash_iconify import DashIconify

from cache import init_cache
from config import CLIENT_ID
from ui.control_diario import registro_diario_layout
from ui.control_semanal import control_semanal_layout


def create_navbar():
    """
    Crea la barra de navegación para cambiar entre páginas
    """

    return dmc.Paper(p="md", shadow="lg", radius="md", mb="md", children=[
        dmc.Group(justify="space-between", children=[
            dmc.Group(gap="md", children=[
                dmc.ActionIcon(
                    DashIconify(icon="mdi:weather-partly-cloudy", width=32),
                    size="xl", variant="light", color="blue", radius="xl"
                ),
                dmc.Stack(gap=0, children=[
                    dmc.Title("Dashboard Meteorológico - Puno", order=3, c="blue"),
                    dmc.Text("SENAMHI - Datos Históricos", size="sm", c="dimmed")
                ])
            ]),
            dmc.SegmentedControl(
                id="page-selector",
                value="diario",
                data=[  # type: ignore[arg-type]
                    {"value": "diario", "label": dmc.Group(gap="xs", children=[
                        DashIconify(icon="mdi:calendar-today", width=18),
                        dmc.Text("Análisis Diario")
                    ])},
                    {"value": "semanal", "label": dmc.Group(gap="xs", children=[
                        DashIconify(icon="mdi:calendar-range", width=18),
                        dmc.Text("Análisis Semanal")
                    ])},
                    {}
                ],
                size="md",
                radius="md",
                color="blue"
            )
        ])
    ])


def create_multi_page_app():
    """
    Crea la aplicación Dash multi-página
    """

    app = Dash(__name__, suppress_callback_exceptions=True)

    app.layout = dmc.MantineProvider(
        theme={"fontFamily": "Inter, sans-serif", "primaryColor": "blue", "defaultRadius": "md"},
        children=[
            html.Div(style={"padding": "20px"}, children=[
                create_navbar(),
                html.Div(id="page-content")
            ])
        ]
    )

    return app

# Callback para cambiar entre páginas
@callback(
    Output("page-content", "children"),
    Input("page-selector", "value")
)
def display_page(page):
    if page == "diario":
        return registro_diario_layout()
    elif page == "semanal":
        return control_semanal_layout()
    return html.Div("Página no encontrada")

def main():
    """
    Flujo principal de la aplicación
    """

    print("=== Dashboard de Datos Meteorológicos Puno ===\n")

    if not CLIENT_ID:
        raise ValueError("CLIENT_ID no encontrado en archivo .env")

    # 1. Inicializar cache (autenticación + datos normales)
    print("1. Inicializando cache (autenticación y datos normales)...")
    init_cache()
    print("    Cache inicializado\n")

    # 2. Crear y ejecutar app multi-página
    print("2. Creando aplicación multi-página...")
    app = create_multi_page_app()
    print("    Aplicación creada\n")

    # 3. Ejecutando el dashboard
    print("3. Abriendo dashboard en http://127.0.0.1:8050")
    print("   Análisis Diario: Vista por zonas de Puno")
    print("   Análisis Semanal: Comparación entre estaciones")
    print("   Presiona Ctrl+C para detener el servidor\n")

    app.run(debug=True, host='127.0.0.1', port=8050)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n Error: {e}")
        raise
