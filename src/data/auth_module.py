import msal
import json
import os

TOKEN_CACHE_FILE = "token_cache.json"

class TokenCache(msal.SerializableTokenCache):
    """
    Token cache que permanece en un archivo
    """
    def __init__(self, cache_file):
        super().__init__()
        self.cache_file = cache_file
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                self.deserialize(f.read())

    def save(self):
        if self.has_state_changed:
            with open(self.cache_file, 'w') as f:
                f.write(self.serialize())


def get_access_token(client_id, tenant_id="common"):
    """
    Obtiene token de acceso con persistencia
    """
    cache = TokenCache(TOKEN_CACHE_FILE)

    app = msal.PublicClientApplication(
        client_id=client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        token_cache=cache
    )

    scopes = ["https://graph.microsoft.com/.default"]
    accounts = app.get_accounts()
    result = None

    if accounts:
        result = app.acquire_token_silent(scopes, account=accounts[0])
        if result and "access_token" in result:
            print("Usuario encontrado en caché")
            return result["access_token"]

    print("No se encontró el token. Iniciando dispositivo de autenticación de código...")
    flow = app.initiate_device_flow(scopes=scopes)

    if "user_code" not in flow:
            raise ValueError(f"Fallo al crear dispositivo de flujo: {json.dumps(flow, indent=4)}")

    print(flow["message"])

    result = app.acquire_token_by_device_flow(flow)

    if result and "access_token" in result:
        cache.save()
        return result["access_token"]
    else:
        raise Exception(f"Authentication failed: {result.get('error_description')}")
