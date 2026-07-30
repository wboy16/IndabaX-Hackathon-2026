import pandas as pd
import numpy as np

from data_loader import load_cover, load_standing, load_quant, load_grazing


def _to_numeric(val, default=np.nan):
    v = pd.to_numeric(val, errors='coerce')
    return default if pd.isna(v) else v

def _to_int(val, default=0):
    v = pd.to_numeric(val, errors='coerce')
    return default if pd.isna(v) else int(v)


def analyze_ground_cover(plot_name: str):
    df = load_cover()
    mask = df['plot_name'].astype(str).str.lower() == plot_name.lower()
    plot_data = df[mask].copy()

    if plot_data.empty:
        return {"error": f"No cover data for plot '{plot_name}'."}

    plot_data['presence'] = pd.to_numeric(plot_data.get('presence'), errors='coerce')
    pct = plot_data.groupby('functional_group')['presence'].mean() * 100

    avg_bare = float(pct.get('bare_ground', np.nan))
    avg_peren = float(pct.get('perennial_grass', np.nan))
    avg_annual = float(pct.get('annual_grass', np.nan))

    erosion_risk = "Unknown"
    if not np.isnan(avg_bare):
        erosion_risk = "High" if avg_bare > 40.0 else "Moderate" if avg_bare > 20.0 else "Low"

    stability = "Unknown"
    if not (np.isnan(avg_peren) or np.isnan(avg_annual)):
        stability = "Stable (Perennial)" if avg_peren > avg_annual else "Vulnerable (Annual)"

    return {
        "Metric": "Ground Cover",
        "Bare ground (%)": None if np.isnan(avg_bare) else round(avg_bare, 2),
        "Erosion risk": erosion_risk,
        "Pasture stability": stability
    }


def evaluate_pasture_biomass(plot_name: str):
    df = load_standing()
    mask = df['plot_name'].astype(str).str.lower() == plot_name.lower()
    plot_data = df[mask].copy()

    if plot_data.empty:
        return {"error": f"No biomass data for plot '{plot_name}'."}

    crop_col = pd.to_numeric(plot_data.get('standing_crop_estimate'), errors='coerce')
    height_col = pd.to_numeric(plot_data.get('max_height'), errors='coerce')
    old_col = pd.to_numeric(plot_data.get('old_standing_%'), errors='coerce')

    avg_crop = _to_numeric(crop_col.mean())
    avg_height = _to_numeric(height_col.mean())
    avg_old_grass = _to_numeric(old_col.mean())

    forage_status = "Unknown"
    if not np.isnan(avg_crop):
        forage_status = "Depleted" if avg_crop < 500 else "Adequate" if avg_crop < 1500 else "Abundant"

    quality = "Unknown"
    if not np.isnan(avg_old_grass):
        quality = "Low (Highly Oxidized)" if avg_old_grass > 60.0 else "Good (Fresh Growth)"

    return {
        "Metric": "Biomass & Yield",
        "Standing crop (kg per ha)": None if np.isnan(avg_crop) else round(avg_crop, 2),
        "Max height (cm)": None if np.isnan(avg_height) else round(avg_height, 2),
        "Forage status": forage_status,
        "Forage quality": quality
    }


def assess_bush_encroachment(plot_name: str):
    df = load_quant()
    mask = df['plot_name'].astype(str).str.lower() == plot_name.lower()
    plot_data = df[mask].copy()

    if plot_data.empty:
        return {"error": f"No quantitative woody data for plot '{plot_name}'."}

    seedlings_col = pd.to_numeric(plot_data.get('seedlings_number'), errors='coerce')
    avg_seedlings = _to_numeric(seedlings_col.mean())

    c1 = pd.to_numeric(plot_data.get('canopy_diam_1'), errors='coerce')
    c2 = pd.to_numeric(plot_data.get('canopy_diam_2'), errors='coerce')
    per_row_canopy = pd.concat([c1, c2], axis=1).mean(axis=1, skipna=True)
    avg_canopy = _to_numeric(per_row_canopy.mean())

    encroachment_risk = "Unknown"
    if not (np.isnan(avg_seedlings) and np.isnan(avg_canopy)):
        high_risk = (
            (not np.isnan(avg_seedlings) and avg_seedlings > 10)
            or (not np.isnan(avg_canopy) and avg_canopy > 3.0)
        )
        encroachment_risk = "High Risk" if high_risk else "Manageable"

    return {
        "Metric": "Bush Encroachment",
        "Average seedling count": None if np.isnan(avg_seedlings) else round(avg_seedlings, 1),
        "Average canopy diameter (m)": None if np.isnan(avg_canopy) else round(avg_canopy, 2),
        "Encroachment risk": encroachment_risk
    }


def calculate_grazing_pressure(plot_name: str):
    df = load_grazing()
    if 'plot_name' not in df.columns:
        return {"error": "grazing data missing 'plot_name' column."}

    mask = df['plot_name'].astype(str).str.lower() == plot_name.lower()
    plot_data = df[mask].copy()

    if plot_data.empty:
        return {"error": f"No grazing data for plot '{plot_name}'."}

    if 'date' in plot_data.columns:
        plot_data['date'] = pd.to_datetime(plot_data['date'], errors='coerce')
        plot_data = plot_data.sort_values('date', na_position='first')

    latest = plot_data.iloc[-1]

    area = _to_numeric(latest.get('area'), default=np.nan)
    if np.isnan(area) or area <= 0:
        return {"error": f"Plot area is missing for '{plot_name}', cannot calculate grazing pressure."}

    cattle = _to_int(latest.get('number_cattle', latest.get('cattle', 0)), default=0)
    sheep = _to_int(latest.get('number_sheep', latest.get('sheep', 0)), default=0)
    goats = _to_int(latest.get('number_goat', latest.get('number_goats', latest.get('goats', 0))), default=0)

    game_cols = ['number_oryx', 'number_kudu', 'number_springbok', 'oryx', 'kudu', 'springbok']
    game = sum(_to_int(latest.get(col, 0), default=0) for col in game_cols)

    total_animals = cattle + sheep + goats + game
    density = total_animals / area

    pressure = "Heavy" if density > 0.5 else "Moderate" if density > 0.2 else "Light"
    latest_rain = _to_numeric(latest.get('rainfall', 0.0), default=0.0)

    return {
        "Metric": "Grazing Pressure",
        "Total animals": int(total_animals),
        "Plot area (ha)": float(area),
        "Animals per ha": round(density, 2),
        "Pressure level": pressure,
        "Latest rainfall (mm)": float(latest_rain)
    }


def generate_plot_command_summary(plot_name: str):
    return {
        "Plot name": plot_name.upper(),
        "Ground cover analysis": analyze_ground_cover(plot_name),
        "Biomass analysis": evaluate_pasture_biomass(plot_name),
        "Encroachment analysis": assess_bush_encroachment(plot_name),
        "Grazing analysis": calculate_grazing_pressure(plot_name)
    }