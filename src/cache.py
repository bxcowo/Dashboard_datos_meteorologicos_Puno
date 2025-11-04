from config import CLIENT_ID
from data.auth_module import get_access_token

data_cache = {}

def init_cache():
    # Extraemos y guardamos token de acceso
    data_cache["ACCESS_TOKEN"] = get_access_token(CLIENT_ID)

    # Extraemos y guardamos registros normales
    from data.file_managment import get_all_normales, get_metadata
    resultados_normales = get_all_normales()
    sheets = ["TMAX", "TMIN", "PP"]
    for sheet in sheets:
        data_cache[f"NORMAL_{sheet}"] = resultados_normales[sheet]
    data_cache["LISTA_ESTACIONES"] = data_cache["NORMAL_TMAX"].index.tolist()
    data_cache["METADATA"] = get_metadata()
