"""Rule based advice. Doses are typical starting values per hectare.
Confirm the final dose with a soil test and your local agriculture office or KVK."""
from common import stage_of


def soil_advice(r):
    tips = []
    if r["soil_ph"] < 6.0:
        tips.append(f"Soil is acidic (pH {r['soil_ph']}). Apply agricultural lime based on a soil test. Peanut grows best at pH 6.0 to 6.8.")
    if r["soil_ph"] > 7.5:
        tips.append(f"Soil is alkaline (pH {r['soil_ph']}). Add gypsum and farmyard manure, and avoid fertilizers that raise pH.")
    if r["drainage"] == "Poor":
        tips.append("Drainage is poor. Make raised beds or drain channels. Waterlogged soil rots pods.")
    if r["soil_type"] in ("Clay", "Black cotton"):
        tips.append("Heavy soil gives small pods and a hard harvest. Add 10 to 12 t/ha farmyard manure and use raised beds.")
    if r["ec_dsm"] > 2.0:
        tips.append(f"Salinity is high (EC {r['ec_dsm']} dS/m). Leach with good quality water. Peanut is salt sensitive.")
    if r["rainfall_mm"] < 500:
        tips.append("Season water is below 500 mm. Plan irrigation at flowering and pod filling.")
    if r["soil_temp_c"] < 20 or r["soil_temp_c"] > 35:
        tips.append("Sow when soil temperature is 25 to 32 C. Seed germination drops outside 20 to 35 C.")
    if r["n_kg_ha"] < 280:
        tips.append("Low nitrogen. Treat seed with Rhizobium and give a starter dose of 20 kg N/ha (about 45 kg urea).")
    if r["p_kg_ha"] < 10:
        tips.append("Low phosphorus. Apply 40 kg P2O5/ha at sowing (about 250 kg SSP).")
    if r["k_kg_ha"] < 110:
        tips.append("Low potassium. Apply 40 kg K2O/ha at sowing (about 65 kg muriate of potash).")
    if r["ca_ppm"] < 500:
        tips.append("Low calcium. Apply 400 kg/ha gypsum at flowering (40 to 45 days after sowing).")
    return tips or ["Soil values are in a good range. Follow the standard fertilizer schedule."]


PLANS = {
    "N_stress": ("Nitrogen stress",
                 ["Top dress 20 kg N/ha (about 45 kg urea/ha) and irrigate lightly.",
                  "Spray 2% urea (20 g per litre of water) in the evening."],
                 ["Check for root nodules. Few pink nodules means weak nitrogen fixation.", "Check for waterlogging and low pH."]),
    "P_stress": ("Phosphorus stress",
                 ["Apply 20 kg P2O5/ha (about 125 kg SSP/ha) near the root zone.",
                  "Spray 2% DAP (20 g per litre, filter the solution first)."],
                 ["Cold or wet soil blocks phosphorus uptake. Check soil temperature and drainage."]),
    "K_stress": ("Potassium stress",
                 ["Apply 40 kg K2O/ha (about 65 kg muriate of potash/ha).",
                  "Spray 1% potassium nitrate (10 g per litre)."],
                 ["Look for yellow, scorched leaf edges on older leaves."]),
    "Ca_stress": ("Calcium stress (pod filling)",
                  ["Apply 400 kg/ha gypsum around the plant base and do light earthing up.",
                   "Keep the pegging zone moist, because calcium reaches pods from the soil."],
                  ["If pH is below 5.5, add lime. Gypsum alone will not fix acidity."]),
}


def stress_plan(stress, das):
    """Returns (title, actions, checks). After 75 days soil dressing is too late, so only sprays are advised."""
    if stress == "Healthy":
        return "No nutrient stress", [], []
    title, actions, checks = PLANS[stress]
    if das > 75 and stress != "Ca_stress":
        actions = [a for a in actions if a.lower().startswith("spray")]
        checks = checks + ["Plant is past 75 days. Soil dressing will not reach the crop in time, so use sprays only."]
    if das > 80 and stress == "Ca_stress":
        actions = ["Gypsum is too late now. Keep soil moist and plan gypsum at 40 to 45 days next season."]
    return title, actions, checks


def delay_plan(status):
    if status == "On track":
        return []
    return ["Check soil moisture, weeds and pests (leaf miner, thrips, aphids).",
            "Compare with the stress result below before adding any fertilizer."]


STAGE_TIPS = {
    "Emergence": "Keep soil moist, check stand count at 10 days and gap fill.",
    "Vegetative": "Weed at 15 to 20 days. Confirm Rhizobium nodules are forming.",
    "Flowering": "Apply gypsum 400 kg/ha at 40 to 45 days and earth up.",
    "Pegging": "Keep the pegging zone moist. Avoid disturbing the soil.",
    "Pod development": "Irrigate at pod filling. Watch for leaf spot disease.",
    "Maturity": "Stop irrigation 10 days before harvest. Harvest when inner pod shell shows dark veins.",
}


def stage_tip(das):
    return STAGE_TIPS[stage_of(das)]
