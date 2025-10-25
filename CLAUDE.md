# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dashboard de datos meteorológicos para Puno - A meteorological data dashboard that fetches weather data from OneDrive-hosted Excel files and displays them using Dash. The project uses Microsoft Graph API for authentication and data retrieval.

## Running the Application

```bash
# Install dependencies (using uv package manager)
uv sync

# Run the main dashboard (requires Python 3.12+)
python -m src.main
```

The dashboard will start at http://127.0.0.1:8050 after authentication and data loading.

## Architecture

### Application Flow

The application follows this startup sequence (see `src/main.py:98-124`):

1. **Environment loading**: Reads `.env` file for credentials
2. **Authentication**: Obtains Microsoft Graph API access token via device flow
3. **Data loading**: Fetches normal values and monthly records from OneDrive
4. **Dashboard initialization**: Creates Dash app with loaded data
5. **Server start**: Runs on localhost:8050

### Core Modules

#### Authentication (`src/data/auth_module.py`)
- Uses MSAL for OAuth device flow authentication
- Caches tokens in `token_cache.json` (git-ignored)
- On first run, prompts user with device code URL
- Subsequent runs use cached token silently
- CLIENT_ID loaded from `.env` file via `config.py`

#### Data Management (`src/data/file_managment.py`)
The module has been refactored to use a global `data_cache` (from `src/cache.py`) instead of passing `access_token` directly. Functions now are:
- `get_all_normales()`: Returns dict of DataFrames with normal values (TMAX, TMIN, PP) for Puno stations
- `get_registro_diario(year, month, day)`: Returns daily weather records with MultiIndex (ZONA, ESTACION)
- `get_registro_mensual(year, month)`: Returns monthly records with MultiIndex columns
- Helper functions: `convert_month(month)`, `digit_to_string(number)` for OneDrive path construction

#### Caching System (`src/cache.py`)
- Central `data_cache` dictionary stores access token and normal values
- `init_cache()` populates cache at startup with authentication and normal data
- Dashboard callbacks cache daily records by date to avoid redundant API calls

#### Configuration (`src/config.py`)
Uses `dotenv` to load environment variables with defaults:
- `CLIENT_ID`: Microsoft application ID
- Directory paths: `DIRECTORIO_PRINCIPAL`, `DIRECTORIO_REGISTRO_DIARIO`, `DIRECTORIO_REGISTRO_SEMANAL`, `DIRECTORIO_REGISTRO_NORMAL`
- `ARCHIVO_EXCEL_NORMALES`: Normal values Excel filename

### Dashboard UI

#### Weekly Control (`src/ui/control_semanal.py`)
Complete Dash application with Dash Mantine Components v2:
- **Date range selection**: Start and end date pickers
- **Multi-station comparison**: Primary station (required) + optional comparison station
- **Interactive graphs**: Separate temperature and precipitation plots with Plotly
- **Normal values overlay**: Shows 1991-2020 normal values as horizontal lines per month
- **Statistics panel**: Displays TMAX/TMIN averages and PP totals
- **Data loading**: On-demand via "Cargar Datos" button, fetches daily records for date range
- **Callback**: `update_graphs()` at line 387 handles all data fetching and visualization

#### Daily Control (`src/ui/control_diario.py`)
Alternative layout for daily analysis:
- **Variable selector**: Choose between TMAX, TMIN, or PP
- **Date picker**: Single date selection
- **Zone-based subplots**: 4 subplots showing data for different Puno zones (SELVA Y VALLES INTERANDINOS, ALTIPLANO NORTE, ALTIPLANO CENTRO, ALTIPLANO SUR)
- **Comparison bars**: Daily record vs historical normal for selected month
- **Callback**: `create_graph()` at line 61 creates multi-subplot figure

### Data Source Structure

OneDrive files organized as:
- **Normal values**: `AndreaProyecto/NORMALES CLIMÁTICAS/NORMALES 1991-2020_ME.xlsx`
  - Sheets: TMAX, TMIN, PP with monthly columns
- **Daily records**: `AndreaProyecto/REGISTRO DIARIO/{year}/{month}/SENAMHI_DZ13_Datos_{day}_{month}_{year}.xlsx`
  - Contains ZONA, ESTACION, TMAX, TMIN, PP columns
- **Monthly records**: `AndreaProyecto/REGISTRO SEMANAL/{year}/{month}. {month_name} {year}.xlsx`
  - Sheet "METEO" with MultiIndex columns (station name + variable)

### Data Processing Patterns

- **Station normalization**: Accents removed, converted to uppercase (see `file_managment.py:69-71`)
- **Special case**: "TAHUACO - YUNGUYO" → "TAHUACO YUNGUYO"
- **MultiIndex handling**: Daily data indexed by (ZONA, ESTACION), monthly by date with MultiIndex columns
- **Month formatting**: `convert_month()` returns uppercase month names in Spanish, `digit_to_string()` adds leading zeros
- **Puno filtering**: Normal values filtered by `DEPARTAMENTO == "PUNO"` column

## Environment Configuration

Create `.env` file in project root:
```
CLIENT_ID="your-microsoft-app-id"
TENANT_ID="common"
DIRECTORIO_PRINCIPAL="AndreaProyecto"
```

Note: `token_cache.json` and `.env` are git-ignored. Never commit credentials.

## Key Dependencies

- `msal`: Microsoft authentication library
- `requests`: Microsoft Graph API calls
- `pandas`, `openpyxl`: Excel file processing
- `dash`, `dash-mantine-components`: Web UI framework
- `plotly`: Interactive charts
- `dotenv`: Environment variable loading
