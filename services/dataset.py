import os
import csv
from typing import Dict, List, Any, Optional

DATASET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "namibia_rangeland_synthetic.csv"
)


def safe_float(value: Any, default: float = 0.0) -> float:
    """Convert value to float safely, returning default for empty/invalid values."""
    try:
        if value is None:
            return default
        # If already a float/int
        if isinstance(value, (float, int)):
            return float(value)
        # Strip whitespace
        s = str(value).strip()
        if s == "":
            return default
        return float(s)
    except (TypeError, ValueError):
        return default


class RangelandDatasetService:
    """Service to load, query, and aggregate Namibian rangeland and pasture data."""

    def __init__(self, csv_path: str = DATASET_PATH):
        self.csv_path = csv_path

    def load_all_records(self) -> List[Dict[str, Any]]:
        """Reads all records from the dataset CSV."""
        if not os.path.exists(self.csv_path):
            return []
        
        records: List[Dict[str, Any]] = []
        with open(self.csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Safely parse numeric fields
                try:
                    latitude = safe_float(row.get("latitude"), 0.0)
                    longitude = safe_float(row.get("longitude"), 0.0)
                    vegetation_cover_pct = safe_float(row.get("vegetation_cover_pct"), 0.0)
                    ndvi = safe_float(row.get("ndvi"), 0.0)
                    grass_biomass = safe_float(row.get("grass_biomass_kg_ha"), 0.0)
                    bush_biomass = safe_float(row.get("bush_biomass_kg_ha"), 0.0)
                    livestock_density = safe_float(row.get("livestock_density_lsu_ha"), 0.0)
                    carrying_capacity = safe_float(row.get("carrying_capacity_ha_lsu"), 0.0)
                except Exception:
                    latitude = longitude = vegetation_cover_pct = ndvi = 0.0
                    grass_biomass = bush_biomass = livestock_density = carrying_capacity = 0.0

                records.append({
                    "site_id": row.get("site_id"),
                    "region": row.get("region") or "",
                    "constituency": row.get("constituency") or "",
                    "latitude": latitude,
                    "longitude": longitude,
                    "land_tenure": row.get("land_tenure") or "",
                    "vegetation_cover_pct": vegetation_cover_pct,
                    "ndvi": ndvi,
                    "grass_biomass_kg_ha": grass_biomass,
                    "bush_biomass_kg_ha": bush_biomass,
                    "bush_encroachment_level": row.get("bush_encroachment_level") or "",
                    "grazing_pressure": row.get("grazing_pressure") or "",
                    "livestock_density_lsu_ha": livestock_density,
                    "carrying_capacity_ha_lsu": carrying_capacity,
                    "pasture_condition_score": row.get("pasture_condition_score") or "",
                    "last_survey_date": row.get("last_survey_date") or ""
                })
        return records

    def query_dataset(
        self,
        region: Optional[str] = None,
        land_tenure: Optional[str] = None,
        constituency: Optional[str] = None
    ) -> Dict[str, Any]:
        """Queries dataset filtered by region, land tenure, and/or constituency."""
        records = self.load_all_records()

        if region:
            records = [r for r in records if (r.get("region") or "").lower() == region.lower()]

        if constituency:
            records = [r for r in records if constituency.lower() in (r.get("constituency") or "").lower()]

        if land_tenure:
            records = [r for r in records if (r.get("land_tenure") or "").lower() == land_tenure.lower()]

        if not records:
            return {
                "found": False,
                "record_count": 0,
                "message": f"No data found matching criteria (region={region}, land_tenure={land_tenure}, constituency={constituency}).",
                "summary": None,
                "records": []
            }

        # Calculate averages and distributions
        total = len(records)
        avg_veg_cover = sum(safe_float(r.get("vegetation_cover_pct"), 0.0) for r in records) / total
        avg_ndvi = sum(safe_float(r.get("ndvi"), 0.0) for r in records) / total
        avg_grass = sum(safe_float(r.get("grass_biomass_kg_ha"), 0.0) for r in records) / total
        avg_bush = sum(safe_float(r.get("bush_biomass_kg_ha"), 0.0) for r in records) / total
        avg_carrying_cap = sum(safe_float(r.get("carrying_capacity_ha_lsu"), 0.0) for r in records) / total
        avg_density = sum(safe_float(r.get("livestock_density_lsu_ha"), 0.0) for r in records) / total

        # Count frequencies
        encroachment_counts: Dict[str, int] = {}
        grazing_pressure_counts: Dict[str, int] = {}
        condition_counts: Dict[str, int] = {}

        for r in records:
            enc = r.get("bush_encroachment_level") or "Unknown"
            gp = r.get("grazing_pressure") or "Unknown"
            cond = r.get("pasture_condition_score") or "Unknown"
            encroachment_counts[enc] = encroachment_counts.get(enc, 0) + 1
            grazing_pressure_counts[gp] = grazing_pressure_counts.get(gp, 0) + 1
            condition_counts[cond] = condition_counts.get(cond, 0) + 1

        summary = {
            "region_queried": region or "All Regions",
            "land_tenure_queried": land_tenure or "All Tenure Types",
            "sites_matched": total,
            "avg_vegetation_cover_pct": round(avg_veg_cover, 2),
            "avg_ndvi": round(avg_ndvi, 3),
            "avg_grass_biomass_kg_ha": round(avg_grass, 1),
            "avg_bush_biomass_kg_ha": round(avg_bush, 1),
            "avg_recommended_carrying_capacity_ha_lsu": round(avg_carrying_cap, 2),
            "avg_current_livestock_density_lsu_ha": round(avg_density, 3),
            "bush_encroachment_breakdown": encroachment_counts,
            "grazing_pressure_breakdown": grazing_pressure_counts,
            "pasture_condition_breakdown": condition_counts,
        }

        return {
            "found": True,
            "record_count": total,
            "summary": summary,
            "records": records[:10]  # Limit detailed records preview
        }
