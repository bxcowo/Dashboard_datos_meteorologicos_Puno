import os
from data.auth_module import get_access_token
from data.file_managment import get_all_normales, get_registro_diario, get_registro_mensual
from ui.control_semanal import create_app


def load_env_vars(env_file="env"):
    """
    Carga las variables de entorno desde el archivo 'env'
    """
    env_vars = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Eliminar comillas de los valores
                    key, value = line.split('=', 1)
                    env_vars[key] = value.strip('"').strip("'")
    else:
        raise FileNotFoundError(f"Archivo {env_file} no encontrado")

    return env_vars


def main():
    """
    Flujo principal de la aplicacion
    """
    print("=== Dashboard de Datos Meteorologicos Puno ===\n")

    # 1. Cargar variables de entorno
    print("1. Cargando variables de entorno...")
    env_vars = load_env_vars("env")
    client_id = env_vars.get("CLIENT_ID")
    tenant_id = env_vars.get("TENANT_ID", "common")

    if not client_id:
        raise ValueError("CLIENT_ID no encontrado en archivo env")

    print(f"    CLIENT_ID: {client_id[:8]}...")
    print(f"    TENANT_ID: {tenant_id}\n")

    # 2. Autenticaci�n
    print("2. Autenticando con Microsoft Graph API...")
    access_token = get_access_token(client_id, tenant_id)
    print(f"    Token obtenido exitosamente\n")

    # 3. Obtener datos de OneDrive
    print("3. Cargando datos de OneDrive...")

    # Cargar valores normales
    print("   - Cargando valores normales (1991-2020)...")
    normales = get_all_normales(
        "AndreaProyecto/NORMALES CLIMÁTICAS",
        "NORMALES 1991-2020_ME.xlsx",
        access_token
    )
    print(f"     ✓ Normales cargadas: {len(normales)} variables")

    # Cargar registro mensual
    print("   - Cargando registro mensual (Agosto 2024)...")
    registro_mensual = get_registro_mensual(
        "AndreaProyecto/REGISTRO SEMANAL",
        2024,
        8,
        access_token
    )
    print(f"     ✓ Registro mensual cargado: {registro_mensual.shape}\n")

    # 4. Inicializar y ejecutar dashboard
    print("4. Iniciando dashboard...")
    app = create_app(
        normales_data=normales,
        registro_mensual=registro_mensual,
        access_token=access_token
    )
    print("   ✓ Dashboard creado exitosamente")
    print("\n🚀 Abriendo dashboard en http://127.0.0.1:8050")
    print("   Presiona Ctrl+C para detener el servidor\n")

    app.run(debug=True, host='127.0.0.1', port=8050)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nL Error: {e}")
        raise
