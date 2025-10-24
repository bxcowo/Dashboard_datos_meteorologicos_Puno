from urllib.parse import quote
from io import BytesIO
import pandas as pd
import requests

def get_all_normales(folder_path, filename, access_token):
    """
    Obtener lista de Dataframes de valores normales para cada estación por mes
    """

    headers = {"Authorization" : f"Bearer {access_token}"}

    full_path = f"{folder_path}/{filename}"
    encoded_path = quote(full_path, safe='/')
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{encoded_path}:/content"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = BytesIO(response.content)
        sheets = ["TMAX", "TMIN", "PP"]
        normales = {}

        for sheet in sheets:
            df = pd.read_excel(
                content,
                sheet_name=sheet,
                usecols='C,D,L:W',
                header=1
            )
            df = df[df["DEPARTAMENTO"] == "PUNO"]
            df = df.drop("DEPARTAMENTO", axis=1)
            df = df.set_index('NOMBRE ESTACION', drop=True)
            normales[sheet] = df

        return normales
    else:
        raise Exception(f"Fallo al descargar {filename}: {response.status_code}")

def get_registro_diario(folder_path, year, month, day, access_token):
    """
    Obtener un Dataframe de variables registradas por estación diario
    """

    headers = {"Authorization" : f"Bearer {access_token}"}
    month = convert_month(month - 1)
    if day < 10:
        day = digit_to_string(day)

    full_path = f"{folder_path}/{year}/{month}/SENAMHI_DZ13_Datos_{day}_{month}_{year}.xlsx"
    encoded_path = quote(full_path, safe='/')
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{encoded_path}:/content"

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        content = BytesIO(response.content)
        df = pd.read_excel(
            content,
            usecols='A,C:F',
            nrows=42,
            header=3
        )
        df.columns = ["ZONA", "ESTACION", "TMAX", "TMIN", "PP"]
        df['ZONA'] = df["ZONA"].ffill()
        df["ESTACION"] = df["ESTACION"].str.translate(str.maketrans('áéíóú', 'aeiou'))
        df["ESTACION"] = df["ESTACION"].str.upper()
        df["ESTACION"] = df["ESTACION"].str.replace("TAHUACO - YUNGUYO", "TAHUACO YUNGUYO")
        df = df.set_index(["ZONA", "ESTACION"])
        return df
    else:
        raise Exception(f"Fallo al descargar el registro diario: {response.status_code}")

def get_registro_mensual(folder_path, year, month, access_token):
    """
    Obtener un Dataframe de los datos mensuales de todas las estaciones
    """

    name_month = convert_month(month - 1)
    if month < 10:
        month = digit_to_string(month)

    full_path = f"{folder_path}/{year}/{month}. {name_month} {year}.xlsx"
    encoded_path = quote(full_path, safe='/')
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{encoded_path}:/content"

    headers = {"Authorization" : f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        content = BytesIO(response.content)
        df = pd.read_excel(
            content,
            sheet_name="METEO",
            skiprows=4,
            usecols='B:FU',
            nrows=33
        )
        df.iloc[0] = df.iloc[0].ffill()
        df.columns = pd.MultiIndex.from_arrays([df.iloc[0], df.iloc[1]])
        df = df.iloc[2:].reset_index(drop=True)
        return df
    else:
        raise Exception(f"Fallo al descargar el registro diario: {response.status_code}")

def convert_month(month):
    """
    Conversion de número de mes a nombre de mes
    """

    monts_match = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
        "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
    return monts_match[month]

def digit_to_string(number):
    """
    Conversion a texto para números en búsqueda
    """

    digit_match = ["01", "02", "03", "04", "05", "06", "07", "08", "09"]
    return digit_match[number]
