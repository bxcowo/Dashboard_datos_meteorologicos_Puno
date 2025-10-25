"""
Dashboard de Datos Meteorológicos - Puno
Aplicación multi-página con análisis diario y semanal
"""
import os
import sys
from dash import Dash, html, Input, Output
import dash_mantine_components as dmc
from dash_iconify import DashIconify

# Agregar el directorio src al path para imports relativos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cache import init_cache
from ui.control_diario import registro_diario_layout
from ui.control_semanal import control_semanal_layout


def load_env_vars(env_file=".env"):
    """Carga las variables de entorno desde el archivo '.env'"""
    env_vars = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key] = value.strip('"').strip("'")
    else:
        raise FileNotFoundError(f"Archivo {env_file} no encontrado")
    return env_vars


def create_navbar():
    """Crea la barra de navegación para cambiar entre páginas"""
    return dmc.Paper(p="md", shadow="lg", radius="md", mb="md", children=[
        dmc.Group(justify="space-between", children=[
            dmc.Group(gap="md", children=[
                dmc.ActionIcon(
                    DashIconify(icon="mdi:weather-partly-cloudy", width=32),
                    size="xl", variant="light", color="blue", radius="xl"
                ),
                dmc.Stack(gap=0, children=[
                    dmc.Title("Dashboard Meteorológico - Puno", order=3, c="blue.7"),
                    dmc.Text("SENAMHI - Datos Históricos", size="sm", c="dimmed")
                ])
            ]),
            dmc.SegmentedControl(
                id="page-selector",
                value="diario",
                data=[
                    {"value": "diario", "label": dmc.Group(gap="xs", children=[
                        DashIconify(icon="mdi:calendar-today", width=18),
                        dmc.Text("Análisis Diario")
                    ])},
                    {"value": "semanal", "label": dmc.Group(gap="xs", children=[
                        DashIconify(icon="mdi:calendar-range", width=18),
                        dmc.Text("Análisis Semanal")
                    ])}
                ],
                size="md",
                radius="md",
                color="blue"
            )
        ])
    ])


def create_multi_page_app():
    """Crea la aplicación Dash multi-página"""
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

    # Callback para cambiar entre páginas
    @app.callback(
        Output("page-content", "children"),
        Input("page-selector", "value")
    )
    def display_page(page):
        if page == "diario":
            return registro_diario_layout()
        elif page == "semanal":
            return control_semanal_layout()
        return html.Div("Página no encontrada")

    return app


def main():
    """Flujo principal de la aplicación"""
    print("=== Dashboard de Datos Meteorológicos Puno ===\n")

    # 1. Cargar variables de entorno
    print("1. Cargando variables de entorno...")
    env_vars = load_env_vars(".env")
    client_id = env_vars.get("CLIENT_ID")

    if not client_id:
        raise ValueError("CLIENT_ID no encontrado en archivo .env")

    print(f"    CLIENT_ID: {client_id[:8]}...")
    print("    ✓ Variables cargadas\n")

    # 2. Inicializar cache (autenticación + datos normales)
    print("2. Inicializando cache (autenticación y datos normales)...")
    init_cache()
    print("    ✓ Cache inicializado\n")

    # 3. Crear y ejecutar app multi-página
    print("3. Creando aplicación multi-página...")
    app = create_multi_page_app()
    print("    ✓ Aplicación creada\n")

    print("🚀 Abriendo dashboard en http://127.0.0.1:8050")
    print("   📊 Análisis Diario: Vista por zonas de Puno")
    print("   📈 Análisis Semanal: Comparación entre estaciones")
    print("   Presiona Ctrl+C para detener el servidor\n")

    app.run(debug=True, host='127.0.0.1', port=8050)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise
