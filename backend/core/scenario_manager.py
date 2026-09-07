"""
Scenario Management and Comparison Framework
Saves, manages, and performs comparative multi-scenario analysis
(e.g., SPH vs Delft3D/Fallback, or Small vs Medium vs Large breach dimensions).
"""

from typing import Dict, Any, List, Optional
import os
import json
import uuid


class ScenarioManager:
    def __init__(self, scenarios_dir: str = r"C:\Users\sahua\.gemini\antigravity\scratch\dam-break-prototype\outputs\scenarios"):
        self.scenarios_dir = scenarios_dir
        os.makedirs(self.scenarios_dir, exist_ok=True)

    def save_scenario(
        self,
        scenario_data: Dict[str, Any],
        scenario_id: Optional[str] = None
    ) -> str:
        """Save a simulation result scenario to disk."""
        if not scenario_id:
            scenario_id = str(uuid.uuid4())[:8]

        scenario_data["scenario_id"] = scenario_id
        file_path = os.path.join(self.scenarios_dir, f"scenario_{scenario_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(scenario_data, f, indent=2)

        return scenario_id

    def get_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific scenario by its ID."""
        file_path = os.path.join(self.scenarios_dir, f"scenario_{scenario_id}.json")
        if not os.path.exists(file_path):
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_scenarios(self) -> List[Dict[str, Any]]:
        """List all available saved scenarios with brief summary headers."""
        summaries = []
        for fname in os.listdir(self.scenarios_dir):
            if fname.startswith("scenario_") and fname.endswith(".json"):
                full_p = os.path.join(self.scenarios_dir, fname)
                try:
                    with open(full_p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        meta = data.get("metadata", {})
                        risk = data.get("risk_summary", {})
                        summaries.append({
                            "scenario_id": data.get("scenario_id", fname.replace("scenario_", "").replace(".json", "")),
                            "scenario_name": data.get("scenario_name", "Scenario"),
                            "engine": data.get("engine", "SPH"),
                            "dam_name": data.get("dam_name", "Hirakud Dam"),
                            "max_discharge": data.get("max_discharge", 0.0),
                            "max_depth": data.get("max_depth", 0.0),
                            "arrival_time": data.get("arrival_time", 0.0),
                            "inundated_area_sqkm": meta.get("inundated_area_sqkm", 0.0),
                            "population_affected": risk.get("population_affected", 0),
                            "risk_level": risk.get("risk_level", "MODERATE")
                        })
                except Exception:
                    continue
        return summaries

    def compare_scenarios(self, scenario_ids: List[str]) -> Dict[str, Any]:
        """
        Produce a side-by-side comparison matrix for two or more scenarios.
        Computes differences and deltas.
        """
        loaded = []
        for sid in scenario_ids:
            sc = self.get_scenario(sid)
            if sc:
                loaded.append(sc)

        if not loaded:
            raise ValueError("None of the specified scenario IDs could be found.")

        rows = []
        for sc in loaded:
            meta = sc.get("metadata", {})
            risk = sc.get("risk_summary", {})
            rows.append({
                "scenario_id": sc.get("scenario_id"),
                "scenario_name": sc.get("scenario_name", f"Scenario {sc.get('scenario_id')}"),
                "engine": sc.get("engine"),
                "max_discharge_m3s": sc.get("max_discharge"),
                "max_depth_m": sc.get("max_depth"),
                "arrival_time_min": sc.get("arrival_time"),
                "flood_area_sqkm": meta.get("inundated_area_sqkm", 0.0),
                "population_affected": risk.get("population_affected", 0),
                "infrastructure_affected": risk.get("infrastructure_affected", 0),
                "risk_level": risk.get("risk_level", "MODERATE")
            })

        # Calculate deltas if exactly 2 scenarios are compared
        deltas = {}
        if len(rows) >= 2:
            base = rows[0]
            comp = rows[1]
            deltas = {
                "discharge_delta_m3s": round(comp["max_discharge_m3s"] - base["max_discharge_m3s"], 1),
                "discharge_delta_percent": round(((comp["max_discharge_m3s"] - base["max_discharge_m3s"]) / max(1.0, base["max_discharge_m3s"])) * 100, 1),
                "depth_delta_m": round(comp["max_depth_m"] - base["max_depth_m"], 2),
                "arrival_delta_min": round(comp["arrival_time_min"] - base["arrival_time_min"], 1),
                "area_delta_sqkm": round(comp["flood_area_sqkm"] - base["flood_area_sqkm"], 2),
                "pop_affected_delta": comp["population_affected"] - base["population_affected"]
            }

        return {
            "num_scenarios": len(rows),
            "scenarios": rows,
            "deltas": deltas,
            "summary_text": self._generate_summary_text(rows, deltas)
        }

    def _generate_summary_text(self, rows: List[Dict[str, Any]], deltas: Dict[str, Any]) -> str:
        if len(rows) < 2:
            return f"Single scenario evaluated ({rows[0]['engine']})."
        
        s1, s2 = rows[0], rows[1]
        text = (
            f"Comparison between '{s1['scenario_name']}' ({s1['engine']}) and "
            f"'{s2['scenario_name']}' ({s2['engine']}):\n"
            f"- Peak Discharge: {s1['max_discharge_m3s']} m3/s vs {s2['max_discharge_m3s']} m3/s (Δ {deltas.get('discharge_delta_percent', 0)}%)\n"
            f"- Maximum Flood Depth: {s1['max_depth_m']} m vs {s2['max_depth_m']} m (Δ {deltas.get('depth_delta_m', 0)} m)\n"
            f"- Flood Arrival: {s1['arrival_time_min']} min vs {s2['arrival_time_min']} min\n"
            f"- Affected Population: {s1['population_affected']} vs {s2['population_affected']}\n"
            f"- Inundated Area: {s1['flood_area_sqkm']} km² vs {s2['flood_area_sqkm']} km²"
        )
        return text
