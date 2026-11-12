"""Shared helpers: growth curves, stages, delay rule and feature lists."""
import numpy as np

SOIL_CAT = ["soil_type", "drainage"]
SOIL_NUM = ["soil_ph", "ec_dsm", "organic_carbon_pct", "n_kg_ha", "p_kg_ha",
            "k_kg_ha", "ca_ppm", "soil_temp_c", "rainfall_mm"]

STRESS_FEATURES = ["das", "height_cm", "leaf_count", "spad", "leaf_scorch",
                   "empty_pod_pct", "soil_n", "soil_p", "soil_k", "soil_ca",
                   "soil_ph", "soil_moisture", "growth_ratio", "leaf_ratio",
                   "ratio_change"]
STRESS_CLASSES = ["Healthy", "N_stress", "P_stress", "K_stress", "Ca_stress"]

STAGES = [(10, "Emergence"), (30, "Vegetative"), (50, "Flowering"),
          (70, "Pegging"), (100, "Pod development")]


def expected_height(das):
    """Expected height (cm) of a bunch type peanut plant at a given day after sowing."""
    return 40 / (1 + np.exp(-0.09 * (np.asarray(das, float) - 35)))


def expected_leaves(das):
    return 4 + 110 / (1 + np.exp(-0.08 * (np.asarray(das, float) - 50)))


def stage_of(das):
    for limit, name in STAGES:
        if das < limit:
            return name
    return "Maturity"


def delay_status(ratio):
    if ratio >= 0.90:
        return "On track"
    if ratio >= 0.75:
        return "Mild delay"
    return "Severe delay"
