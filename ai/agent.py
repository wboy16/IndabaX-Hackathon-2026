import os
import json
import logging
from typing import Dict, Any, Optional, List

from services.dataset import RangelandDatasetService
from services.weather import WeatherService
from ai.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Initialize services
dataset_service = RangelandDatasetService()
weather_service = WeatherService()

class RangelandAgent:
    """LLM Agent with tool calling for Namibian Rangeland & Livestock Advisory."""

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = model_name
        self.api_key = os.getenv("OPENAI_API_KEY")

    def run_agent(
        self,
        user_query: str,
        region: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        land_tenure: Optional[str] = None,
        herd_size: Optional[int] = None,
        farm_size_ha: Optional[float] = None
    ) -> Dict[str, Any]:
        """Executes agent logic, selecting tools to query dataset & weather before generating transparent response."""

        # Step 1: Execute tool calls to gather ground truth & live weather evidence
        rangeland_data = dataset_service.query_dataset(
            region=region,
            land_tenure=land_tenure
        )

        weather_data = weather_service.get_weather_for_region_or_coords(
            region=region,
            lat=lat,
            lon=lon
        )

        tools_called = ["query_rangeland_data", "get_recent_weather"]

        # Step 2: Attempt OpenAI Agent call if API key is provided
        if self.api_key:
            try:
                from langchain_openai import ChatOpenAI
                from langchain_core.messages import SystemMessage, HumanMessage

                llm = ChatOpenAI(
                    model=self.model_name,
                    openai_api_key=self.api_key,
                    temperature=0.3
                )

                context_prompt = (
                    f"{SYSTEM_PROMPT}\n\n"
                    f"FARMER INQUIRY: {user_query}\n"
                    f"FARMER CONTEXT: Region={region}, Land Tenure={land_tenure}, Herd Size={herd_size} cattle, Farm Size={farm_size_ha} ha.\n\n"
                    f"GROUND TRUTH RANGELAND DATA:\n{json.dumps(rangeland_data['summary'], indent=2)}\n\n"
                    f"LIVE WEATHER & RECENT RAINFALL:\n{json.dumps(weather_data, indent=2)}\n\n"
                    f"Generate a clear, transparent recommendation explaining all reasoning and data limitations."
                )

                messages = [
                    SystemMessage(content=SYSTEM_PROMPT),
                    HumanMessage(content=context_prompt)
                ]

                response = llm.invoke(messages)
                advice_text = response.content

                return {
                    "query": user_query,
                    "region": region,
                    "land_tenure": land_tenure,
                    "advice": advice_text,
                    "reasoning_explained": True,
                    "data_sources_used": {
                        "rangeland_dataset": rangeland_data["summary"],
                        "weather_api": weather_data
                    },
                    "tools_executed": tools_called,
                    "llm_engine": f"OpenAI ({self.model_name})"
                }
            except Exception as e:
                logger.warning(f"OpenAI LLM execution failed or key invalid ({str(e)}). Falling back to rule-based agentic reasoning engine.")

        # Step 3: Fallback Expert Reasoning Engine (Ensures full API functionality without API key)
        advice_text = self._generate_transparent_reasoning_fallback(
            user_query=user_query,
            region=region or "Namibia",
            land_tenure=land_tenure or "Commercial/Communal",
            rangeland_data=rangeland_data,
            weather_data=weather_data,
            herd_size=herd_size,
            farm_size_ha=farm_size_ha
        )

        return {
            "query": user_query,
            "region": region or "Namibia",
            "land_tenure": land_tenure,
            "advice": advice_text,
            "reasoning_explained": True,
            "data_sources_used": {
                "rangeland_dataset": rangeland_data.get("summary"),
                "weather_api": weather_data
            },
            "tools_executed": tools_called,
            "llm_engine": "Omiti Rule-Based Reasoning Engine (Fallback Active)"
        }

    def _generate_transparent_reasoning_fallback(
        self,
        user_query: str,
        region: str,
        land_tenure: str,
        rangeland_data: Dict[str, Any],
        weather_data: Dict[str, Any],
        herd_size: Optional[int],
        farm_size_ha: Optional[float]
    ) -> str:
        """Generates evidence-backed advisory response following Namibian rangeland guidelines."""

        summary = rangeland_data.get("summary") or {}
        avg_veg = summary.get("avg_vegetation_cover_pct", 30.0)
        avg_ndvi = summary.get("avg_ndvi", 0.3)
        avg_grass = summary.get("avg_grass_biomass_kg_ha", 800.0)
        avg_bush = summary.get("avg_bush_biomass_kg_ha", 1200.0)
        carrying_cap = summary.get("avg_recommended_carrying_capacity_ha_lsu", 12.0)
        encroachment_breakdown = summary.get("bush_encroachment_breakdown", {})
        
        recent_rain = weather_data.get("past_14_days_total_rainfall_mm", 0.0)
        rain_status = weather_data.get("rainfall_condition_status", "Moderate")
        temp = weather_data.get("current_temperature_c", "N/A")

        # Calculations if herd_size and farm_size_ha provided
        stocking_capacity_text = ""
        if herd_size and farm_size_ha and carrying_cap > 0:
            max_recommended_lsu = round(farm_size_ha / carrying_cap, 1)
            current_ratio = round(herd_size / max_recommended_lsu, 2) if max_recommended_lsu > 0 else 1.0

            if current_ratio > 1.2:
                stocking_status = f"⚠️ OVERSTOCKED: Your herd of {herd_size} LSU exceeds the safe carrying capacity of {max_recommended_lsu} LSU for {farm_size_ha} hectares."
            elif current_ratio >= 0.8:
                stocking_status = f"✅ SAFE STOCKING: Your herd of {herd_size} LSU is appropriately aligned with the safe capacity of {max_recommended_lsu} LSU."
            else:
                stocking_status = f"🌿 UNDERSTOCKED: Your farm has reserve grazing capacity for up to {max_recommended_lsu} LSU."
            
            stocking_capacity_text = f"\n\n**Herd & Carrying Capacity Evaluation:**\n- Farm Size: {farm_size_ha} ha | Recommended Rate: {carrying_cap} ha/LSU\n- Safe Maximum Herd: {max_recommended_lsu} Large Stock Units (LSU)\n- Assessment: {stocking_status}"

        # Bush encroachment note
        bush_note = "Bush encroachment is currently manageable."
        if "Severe" in encroachment_breakdown or "High" in encroachment_breakdown:
            bush_note = f"Bush encroachment in {region} is elevated (Bush Biomass ~{avg_bush} kg/ha). Consider targeted bush thinning to allow grass biomass (~{avg_grass} kg/ha) to recover."

        return f"""### 🌾 Omiti Rangeland & Livestock Advisory Report ({region} Region)

**Re:** "{user_query}"

---

#### 📊 1. Current Pasture & Weather Evidence Synthesis
- **Location / Region:** {region} ({land_tenure} Land Tenure)
- **Recent Rainfall (Past 14 Days):** {recent_rain} mm ({rain_status}) | Temp: {temp}°C
- **Vegetation Health (NDVI):** {avg_ndvi} (Vegetation Cover: {avg_veg}%)
- **Available Forage:** Grass Biomass ~{avg_grass} kg/ha | Bush Biomass ~{avg_bush} kg/ha
- **Recommended Regional Carrying Capacity:** {carrying_cap} ha / LSU

---

#### 🐄 2. Recommended Management Strategy
- **Grazing Pressure & Rotational Advice:** Based on recent rainfall of **{recent_rain} mm** and an NDVI score of **{avg_ndvi}**, pasture growth is in a **{rain_status}** state.{stocking_capacity_text}
- **Camp Resting:** Rotate herds every 4 to 6 weeks to allow degraded camps at least 60 days of uninterrupted rest for seed set and root recovery.
- **Bush Control:** {bush_note}

---

#### ⚠️ 3. Transparent Data Limitations & Reasoning
*This advisory is generated by combining ground survey metrics from the Namibia Rangeland Dataset for {region} with live satellite-derived weather data from Open-Meteo.*
- **Data Limitation:** Field survey sampling reflects regional averages. Local soil moisture, camp fencing, and micro-climates on your specific farm should be inspected prior to major herd movements.
- **Drought Caution:** If total 30-day rainfall remains under 20mm, proactive destocking or supplemental feeding is advised before dry season peaks.
"""
