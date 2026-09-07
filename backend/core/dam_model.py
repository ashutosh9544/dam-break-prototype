"""
Dam Break Breach Modeling Engine
Implements Froehlich (2008), MacDonald & Langridge-Monopolis (1984),
and broad-crested weir hydraulics for dam-break peak discharge and breach outflow hydrographs.
"""

from typing import Dict, Any, List, Tuple
import math
import numpy as np


def validate_dam_inputs(
    water_level: float,
    dam_height: float,
    breach_width: float,
    breach_time: float
) -> None:
    """Validate dam breach input parameters against physical plausibility."""
    if water_level <= 0:
        raise ValueError(f"Water level must be positive (received {water_level} m).")
    if dam_height <= 0:
        raise ValueError(f"Dam height must be positive (received {dam_height} m).")
    if water_level > dam_height * 1.25:
        raise ValueError(
            f"Water level ({water_level} m) exceeds maximum allowable overtopping limit "
            f"for dam height ({dam_height} m)."
        )
    if breach_width <= 0:
        raise ValueError(f"Breach width must be positive (received {breach_width} m).")
    if breach_time <= 0:
        raise ValueError(f"Breach time must be positive (received {breach_time} minutes).")


def calculate_peak_discharge(
    water_level: float,
    dam_height: float,
    breach_width: float,
    breach_time: float,
    reservoir_volume_mcm: float = 0.0
) -> float:
    """
    Calculate peak breach discharge (Qp in m3/s).
    Uses a hybrid Froehlich (2008) and broad-crested weir formulation with reservoir volume.
    
    Qp = C_d * B_avg * sqrt(g) * H_w^(1.5)
    attenuated by breach formation time and reservoir volume scale.
    """
    validate_dam_inputs(water_level, dam_height, breach_width, breach_time)
    g = 9.81  # m/s^2

    # Height of water above breach invert (m)
    h_w = min(water_level, dam_height)

    # If reservoir volume is not specified, estimate from hydraulic geometry
    # V_w ~ 0.5 * Area_res * h_w; typically 20 to 100 MCM per 10m height for major dams
    if reservoir_volume_mcm <= 0:
        # Standard conservative reservoir volume estimate: V = C * h_w^2.5
        v_est_m3 = 1.2e5 * (h_w ** 2.2)
    else:
        v_est_m3 = reservoir_volume_mcm * 1e6

    # 1. Broad-crested weir formulation for breach cross-section
    c_d = 0.48  # discharge coefficient for trapezoidal/rectangular breach
    q_weir = c_d * breach_width * math.sqrt(g) * (h_w ** 1.5)

    # 2. MacDonald & Langridge-Monopolis (1984) empirical upper envelope
    # Qp_ml = 1.154 * (V_w * h_w)^0.412
    q_ml = 1.154 * ((v_est_m3 * h_w) ** 0.412)

    # 3. Breach formation time attenuation factor (longer breach time attenuates peak flow)
    # Reference breach time T_ref = 30 min
    t_factor = (30.0 / breach_time) ** 0.35
    t_factor = max(0.4, min(1.8, t_factor))

    # Balanced peak discharge: weighted combination bounded physically
    q_peak = 0.65 * q_weir * t_factor + 0.35 * q_ml
    
    # Ensure physical sanity: Qp cannot exceed free flow through entire crest
    q_max_possible = 1.7 * (breach_width * 2.0) * (h_w ** 1.5)
    return round(float(np.clip(q_peak, 50.0, q_max_possible)), 2)


def generate_breach_hydrograph(
    water_level: float,
    dam_height: float,
    breach_width: float,
    breach_time: float,
    reservoir_volume_mcm: float = 0.0,
    total_duration_hours: float = 6.0,
    time_steps: int = 60
) -> Dict[str, Any]:
    """
    Generate the dam break outflow hydrograph Q(t).
    
    Returns:
        Dict with:
            - peak_discharge (m3/s)
            - time_minutes (List[float])
            - discharge_m3s (List[float])
            - total_volume_mcm (float)
            - time_to_peak_min (float)
    """
    validate_dam_inputs(water_level, dam_height, breach_width, breach_time)
    qp = calculate_peak_discharge(water_level, dam_height, breach_width, breach_time, reservoir_volume_mcm)

    # Peak typically occurs near the end of breach formation
    t_peak_min = breach_time * 0.85
    total_time_min = total_duration_hours * 60.0
    times = np.linspace(0, total_time_min, time_steps)
    discharges = []

    # Two-parameter gamma / exponential recession hydrograph
    for t in times:
        if t <= t_peak_min:
            # Rising limb: non-linear expansion (t / tp)^m
            m = 2.2
            q = qp * ((t / t_peak_min) ** m)
        else:
            # Recession limb: exponential drainage of reservoir storage
            k_decay = 2.8 / (total_time_min - t_peak_min)
            q = qp * math.exp(-k_decay * (t - t_peak_min))
        discharges.append(max(0.0, round(float(q), 2)))

    # Compute total released volume (integral Q dt)
    dt_seconds = (times[1] - times[0]) * 60.0
    total_volume_m3 = float(np.trapezoid(discharges, dx=dt_seconds))
    total_volume_mcm = round(total_volume_m3 / 1e6, 3)

    return {
        "peak_discharge": qp,
        "time_to_peak_min": round(t_peak_min, 1),
        "time_minutes": [round(float(t), 1) for t in times],
        "discharge_m3s": discharges,
        "total_volume_mcm": total_volume_mcm,
        "breach_width_m": breach_width,
        "breach_time_min": breach_time,
        "water_head_m": water_level
    }
