from urllib.parse import quote
from io import BytesIO
from cache import data_cache
import config as cf
import pandas as pd
import requests
import calendar

def get_all_normales():
    """
    Obtener lista de Dataframes de valores normales para cada estación por mes
    """

    headers = {"Authorization" : f"Bearer {data_cache["ACCESS_TOKEN"]}"}

    full_path = f"{cf.DIRECTORIO_PRINCIPAL}/{cf.DIRECTORIO_REGISTRO_NORMAL}/{cf.ARCHIVO_EXCEL_NORMALES}"
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
            df.columns = df.columns.str.upper()
            normales[sheet] = df

        return normales
    else:
        raise Exception(f"Fallo al descargar {cf.ARCHIVO_EXCEL_NORMALES}: {response.status_code}")

def get_registro_diario(year, month, day):
    """
    Obtener un Dataframe de variables registradas por estación diario
    """

    headers = {"Authorization" : f"Bearer {data_cache["ACCESS_TOKEN"]}"}
    folder_path = f"{cf.DIRECTORIO_PRINCIPAL}/{cf.DIRECTORIO_REGISTRO_DIARIO}"
    month = convert_month(month)
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
            usecols='A,C:E,I',
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

def get_registro_mensual(year, month):
    """
    Obtener un Dataframe de los datos mensuales de todas las estaciones
    """

    headers = {"Authorization" : f"Bearer {data_cache["ACCESS_TOKEN"]}"}
    folder_path = f"{cf.DIRECTORIO_PRINCIPAL}/{cf.DIRECTORIO_REGISTRO_SEMANAL}"

    name_month = convert_month(month)
    if month < 10:
        num_month = digit_to_string(month)
    else:
        num_month = month

    full_path = f"{folder_path}/{year}/{num_month}. {name_month} {year}.xlsx"
    encoded_path = quote(full_path, safe='/')
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{encoded_path}:/content"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        content = BytesIO(response.content)
        df = pd.read_excel(
            content,
            sheet_name="METEO",
            skiprows=4,
            usecols='B:FU',
            nrows=calendar.monthrange(year, month)[1] + 2
        )
        df.iloc[0] = df.iloc[0].ffill()
        df.columns = pd.MultiIndex.from_arrays([df.iloc[0], df.iloc[1]])
        df = df.iloc[2:].reset_index(drop=True)
        return df
    else:
        raise Exception(f"Fallo al descargar el registro diario: {response.status_code}")

def get_metadata():
    """
    Obtener metadata en forma de Dataframe para los archivos excel
    """

    headers = {"Authorization" : f"Bearer {data_cache["ACCESS_TOKEN"]}"}

    full_path = f"{cf.DIRECTORIO_PRINCIPAL}/{cf.DIRECTORIO_METADATA}/{cf.ARCHIVO_EXCEL_METADATA}"
    encoded_path = quote(full_path, safe='/')
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{encoded_path}:/content"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        content = BytesIO(response.content)
        df = pd.read_excel(
            content,
            sheet_name="GEOGRAFICAS",
            usecols='A:G',
            header=0,
            nrows=42
        )
        df["ESTACION"] = df["ESTACION"].str.translate(str.maketrans('áéíóú', 'aeiou'))
        df["ESTACION"] = df["ESTACION"].str.upper()
        df["ESTACION"] = df["ESTACION"].str.replace("TAHUACO - YUNGUYO", "TAHUACO YUNGUYO")
        df = df.set_index('ESTACION', drop=True)

        return df
    else:
        raise Exception(f"Fallo al descargar {cf.ARCHIVO_EXCEL_METADATA}: {response.status_code}")

def get_planilla_climatologica(station_name, year, month):
    """
    Obtener Dataframe de los datos Voz y Data de una estación para planilla

    Nota: Falta implantar year en los archivos, se mantiene por ahora para demo.
    """

    headers = {"Authorization" : f"Bearer {data_cache["ACCESS_TOKEN"]}"}
    folder_path = f"{cf.DIRECTORIO_PRINCIPAL}/{cf.DIRECTORIO_PLANILLA}/{year}/{station_name}"

    month_name = convert_month(month)
    file_name = f"{month_name}.xlsx"
    full_path = f"{folder_path}/{file_name}"
    encoded_path = quote(full_path, safe='/')
    url = f"https://graph.microsoft.com/v1.0/me/drive/root:/{encoded_path}:/content"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        content = BytesIO(response.content)
        df = pd.read_excel(
            content,
            sheet_name=station_name,
            usecols='A:U',
            nrows=91
        )
        return df
    else:
        raise Exception(f"Fallo al descargar planilla climatológica: {response.status_code}")

def convert_month(month):
    """
    Conversion de número de mes a nombre de mes
    """

    monts_match = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
        "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
    return monts_match[month - 1]

def digit_to_string(number):
    """
    Conversion a texto para números en búsqueda
    """

    digit_match = ["01", "02", "03", "04", "05", "06", "07", "08", "09"]
    return digit_match[number - 1]
