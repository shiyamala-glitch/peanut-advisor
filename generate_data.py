"""Creates the two datasets. Run: python generate_data.py"""
import numpy as np, pandas as pd
from common import *

rng = np.random.default_rng(42)


def cn(mean, sd, lo, hi, size=None):
    return np.clip(rng.normal(mean, sd, size), lo, hi)


# ---------------------------------------------------------------- dataset 1
TYPE_SCORE = {"Sandy loam": 1.0, "Red loam": 0.95, "Loamy sand": 0.9,
              "Sandy clay loam": 0.7, "Clay": 0.25, "Black cotton": 0.2}
HEAVY = {"Clay", "Black cotton"}


def make_suitability(n=4000):
    types = rng.choice(list(TYPE_SCORE), n, p=[.22, .22, .15, .15, .13, .13])
    drain = np.array([rng.choice(["Poor", "Moderate", "Good"],
                      p=[.5, .35, .15] if t in HEAVY else [.08, .30, .62]) for t in types])
    df = pd.DataFrame({
        "soil_type": types, "drainage": drain,
        "soil_ph": cn(6.5, 0.9, 4.3, 9.0, n).round(2),
        "ec_dsm": np.clip(rng.gamma(2, 0.3, n), 0.05, 4).round(2),
        "organic_carbon_pct": cn(0.55, 0.25, 0.1, 1.5, n).round(2),
        "n_kg_ha": cn(300, 110, 80, 600, n).round(0),
        "p_kg_ha": cn(18, 9, 2, 50, n).round(1),
        "k_kg_ha": cn(180, 70, 40, 400, n).round(0),
        "ca_ppm": cn(900, 450, 150, 2500, n).round(0),
        "soil_temp_c": cn(27, 4, 15, 38, n).round(1),
        "rainfall_mm": cn(650, 250, 150, 1500, n).round(0),
    })
    ph, t, r, ec = df.soil_ph, df.soil_temp_c, df.rainfall_mm, df.ec_dsm
    ph_s = np.where(ph < 6.0, np.clip(ph - 5.0, 0, 1), np.where(ph <= 6.8, 1, np.clip((8.0 - ph) / 1.2, 0, 1)))
    t_s = np.where(t < 25, np.clip((t - 15) / 10, 0, 1), np.where(t <= 32, 1, np.clip((40 - t) / 8, 0, 1)))
    r_s = np.where(r < 500, np.clip((r - 200) / 300, 0, 1), np.where(r <= 900, 1, np.clip((1500 - r) / 600, 0, 1)))
    ec_s = np.where(ec <= 1, 1, np.clip((3 - ec) / 2, 0, 1))
    d_s = df.drainage.map({"Good": 1, "Moderate": .7, "Poor": .15}).values
    ty_s = df.soil_type.map(TYPE_SCORE).values
    oc_s = np.clip(df.organic_carbon_pct / 0.5, 0, 1)
    p_s = 0.3 + 0.7 * np.clip(df.p_kg_ha / 15, 0, 1)
    k_s = 0.3 + 0.7 * np.clip(df.k_kg_ha / 120, 0, 1)
    ca_s = 0.3 + 0.7 * np.clip(df.ca_ppm / 500, 0, 1)
    weighted = (.25 * ph_s + .15 * d_s + .15 * ty_s + .12 * t_s + .12 * r_s +
                .08 * ec_s + .04 * oc_s + .03 * p_s + .03 * k_s + .03 * ca_s)
    limiting = np.minimum.reduce([ph_s, d_s, t_s, ec_s])
    score = weighted * (0.4 + 0.6 * limiting) + rng.normal(0, 0.04, n)
    df["suitability"] = np.where(score >= 0.62, "Highly suitable",
                         np.where(score >= 0.40, "Moderately suitable", "Not suitable"))
    return df


# ---------------------------------------------------------------- dataset 2
ONSET = {"N_stress": (14, 56), "P_stress": (14, 49), "K_stress": (28, 63), "Ca_stress": (42, 70)}
LOW_SOIL = {"N_stress": ("soil_n", 190, 40), "P_stress": ("soil_p", 9, 3),
            "K_stress": ("soil_k", 105, 25), "Ca_stress": ("soil_ca", 350, 100)}
H_LOSS = {"N_stress": .20, "P_stress": .30, "K_stress": .15, "Ca_stress": .04}
L_LOSS = {"N_stress": .22, "P_stress": .18, "K_stress": .12, "Ca_stress": .03}


def make_growth(healthy_plants=200, stressed_plants=140):
    rows, pid = [], 0
    plan = [("Healthy", healthy_plants)] + [(c, stressed_plants) for c in ONSET]
    for cls, count in plan:
        for _ in range(count):
            pid += 1
            onset = rng.integers(*ONSET[cls]) if cls != "Healthy" else 999
            sev = rng.uniform(0.6, 1.3)
            gf, lf = rng.normal(1, 0.05), rng.normal(1, 0.05)
            soil = {"soil_n": cn(340, 50, 150, 520), "soil_p": cn(24, 6, 8, 45),
                    "soil_k": cn(190, 35, 80, 320), "soil_ca": cn(1000, 250, 300, 2000)}
            if cls != "Healthy" and rng.random() < 0.85:      # 15% hidden stress, soil looks normal
                k, m, s = LOW_SOIL[cls]
                soil[k] = cn(m, s, 20, 600)
            ph = cn(6.4, 0.35, 5.2, 7.5)
            spad0 = rng.normal(40, 1.5)
            prev = None
            for das in range(7, 106, 7):
                t = max(0, das - onset)
                ramp = 1 - np.exp(-t / 12)
                hf = 1 - H_LOSS.get(cls, 0) * sev * ramp
                lfac = 1 - L_LOSS.get(cls, 0) * sev * ramp
                h = expected_height(das) * gf * hf * (1 + rng.normal(0, .04))
                lv = expected_leaves(das) * lf * lfac * (1 + rng.normal(0, .05))
                spad = spad0 + rng.normal(0, 1.2) - max(0, das - 95) * 0.4
                if cls == "N_stress": spad -= 10 * sev * ramp
                if cls == "K_stress": spad -= 4 * sev * ramp
                if cls == "P_stress": spad += 1.5 * sev * ramp
                scorch = rng.poisson(0.25) + (3 * sev * ramp + rng.normal(0, .7) if cls == "K_stress" else 0)
                pods = 0.0
                if das >= 70:
                    pods = rng.normal(5, 2) + (35 * sev * min(1, t / 21) if cls == "Ca_stress" else 0) \
                           + (4 if cls == "P_stress" else 0)
                ratio = h / float(expected_height(das))
                rows.append(dict(
                    plant_id=pid, das=das, stage=stage_of(das),
                    height_cm=round(h, 1), leaf_count=int(round(lv)), spad=round(spad, 1),
                    leaf_scorch=int(np.clip(round(scorch), 0, 5)), empty_pod_pct=round(float(np.clip(pods, 0, 80)), 1),
                    soil_n=round(soil["soil_n"] * (1 + rng.normal(0, .03))), soil_p=round(soil["soil_p"] * (1 + rng.normal(0, .03)), 1),
                    soil_k=round(soil["soil_k"] * (1 + rng.normal(0, .03))), soil_ca=round(soil["soil_ca"] * (1 + rng.normal(0, .03))),
                    soil_ph=round(ph + rng.normal(0, .05), 2), soil_moisture=round(float(cn(22, 4, 8, 35)), 1),
                    growth_ratio=round(ratio, 3), leaf_ratio=round(lv / float(expected_leaves(das)), 3),
                    ratio_change=round(0.0 if prev is None else ratio - prev, 3),
                    growth_status=delay_status(ratio),
                    stress_label=cls if das >= onset else "Healthy"))
                prev = ratio
    return pd.DataFrame(rows)


if __name__ == "__main__":
    s = make_suitability(); g = make_growth()
    s.to_csv("data/soil_suitability_dataset.csv", index=False)
    g.to_csv("data/peanut_growth_stress_dataset.csv", index=False)
    print(s.shape, s.suitability.value_counts().to_dict())
    print(g.shape, g.stress_label.value_counts().to_dict())
    print(g.growth_status.value_counts().to_dict())
