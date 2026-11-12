"""Peanut Advisor: soil check, growth tracking, stress detection, farmer alerts, fertilizer advice."""
import os, sqlite3, datetime as dt
import joblib, pandas as pd, requests, streamlit as st
from common import expected_height, expected_leaves, stage_of, delay_status, STRESS_FEATURES
from recommend import soil_advice, stress_plan, delay_plan, stage_tip

st.set_page_config(page_title="Peanut Advisor", layout="wide")
DB = "data/farm_history.db"


@st.cache_resource
def load_models():
    return joblib.load("models/soil_model.joblib"), joblib.load("models/stress_model.joblib")


def secret(name):
    try:
        return os.getenv(name) or st.secrets.get(name)
    except Exception:
        return os.getenv(name)


def send_telegram(text):
    """Sends the alert to the farmer's Telegram chat. Returns a status message."""
    token, chat = secret("TELEGRAM_TOKEN"), secret("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return "Telegram is not configured. Alert shown here only."
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          data={"chat_id": chat, "text": text}, timeout=10)
        return "Alert sent to the farmer on Telegram." if r.ok else f"Telegram error: {r.text[:100]}"
    except requests.RequestException as e:
        return f"Could not reach Telegram: {e}"


def read_history(field=None):
    con = sqlite3.connect(DB)
    try:
        q = "SELECT rowid AS id, * FROM obs" + (" WHERE field_name=? ORDER BY das" if field else " ORDER BY rowid")
        return pd.read_sql(q, con, params=(field,) if field else None)
    except Exception:
        return pd.DataFrame()
    finally:
        con.close()


def save_row(row):
    con = sqlite3.connect(DB)
    pd.DataFrame([row]).to_sql("obs", con, if_exists="append", index=False)
    con.close()


soil_b, stress_b = load_models()
st.title("Peanut Advisor")
tab1, tab2, tab3 = st.tabs(["1. Soil suitability", "2. Growth and stress tracking", "3. History and alerts"])

# ------------------------------------------------------------------ tab 1
with tab1:
    st.subheader("Can peanut grow in this soil?")
    c1, c2, c3 = st.columns(3)
    soil_type = c1.selectbox("Soil type", ["Sandy loam", "Red loam", "Loamy sand", "Sandy clay loam", "Clay", "Black cotton"])
    drainage = c1.selectbox("Drainage", ["Good", "Moderate", "Poor"])
    ph = c1.number_input("Soil pH", 3.5, 10.0, 6.5, 0.1)
    ec = c2.number_input("EC (dS/m)", 0.0, 6.0, 0.5, 0.1)
    oc = c2.number_input("Organic carbon (%)", 0.0, 3.0, 0.5, 0.05)
    n = c2.number_input("Available N (kg/ha)", 0, 800, 300, 10)
    p = c3.number_input("Available P (kg/ha)", 0.0, 80.0, 18.0, 1.0)
    k = c3.number_input("Available K (kg/ha)", 0, 600, 180, 10)
    ca = c3.number_input("Calcium (ppm)", 0, 3000, 900, 50)
    t = c1.number_input("Soil temperature at sowing (C)", 5.0, 45.0, 27.0, 0.5)
    rain = c2.number_input("Season rainfall plus irrigation (mm)", 0, 2000, 650, 50)
    if st.button("Check soil", type="primary"):
        r = dict(soil_type=soil_type, drainage=drainage, soil_ph=ph, ec_dsm=ec, organic_carbon_pct=oc,
                 n_kg_ha=n, p_kg_ha=p, k_kg_ha=k, ca_ppm=ca, soil_temp_c=t, rainfall_mm=rain)
        X = pd.DataFrame([r])[soil_b["features"]]
        proba = soil_b["model"].predict_proba(X)[0]
        label = soil_b["classes"][proba.argmax()]
        msg = f"{label} ({proba.max():.0%} confidence)"
        {"Highly suitable": st.success, "Moderately suitable": st.warning, "Not suitable": st.error}[label](
            ("Peanut can grow here. " if label != "Not suitable" else "Peanut is unlikely to do well here. ") + msg)
        st.bar_chart(pd.Series(proba, index=soil_b["classes"]))
        st.markdown("**What to fix before sowing**")
        for tip in soil_advice(r):
            st.write("- " + tip)

# ------------------------------------------------------------------ tab 2
with tab2:
    st.subheader("Weekly field record")
    with st.form("obs"):
        a, b, c = st.columns(3)
        field = a.text_input("Field name", "Field 1")
        sow = a.date_input("Sowing date", dt.date.today() - dt.timedelta(days=42))
        obs_date = a.date_input("Observation date", dt.date.today())
        height = b.number_input("Plant height (cm)", 0.0, 80.0, 14.0, 0.5)
        leaves = b.number_input("Leaf count per plant", 0, 300, 28)
        spad = b.number_input("Leaf greenness (SPAD)", 0.0, 60.0, 40.0, 0.5)
        scorch = c.slider("Leaf edge scorch (0 none, 5 severe)", 0, 5, 0)
        pods = c.number_input("Empty pods (%), after day 70", 0.0, 100.0, 0.0, 1.0)
        moist = c.number_input("Soil moisture (%)", 0.0, 60.0, 22.0, 1.0)
        d, e, f = st.columns(3)
        sn = d.number_input("Soil N (kg/ha)", 0, 800, 330, 10)
        sp = d.number_input("Soil P (kg/ha)", 0.0, 80.0, 22.0, 1.0)
        sk = e.number_input("Soil K (kg/ha)", 0, 600, 190, 10)
        sca = e.number_input("Soil Ca (ppm)", 0, 3000, 950, 50)
        sph = f.number_input("Soil pH ", 3.5, 10.0, 6.4, 0.1)
        go = st.form_submit_button("Analyse and save", type="primary")

    if go:
        das = (obs_date - sow).days
        if das < 1:
            st.error("Observation date must be after the sowing date.")
            st.stop()
        hist = read_history(field)
        prev = hist.growth_ratio.iloc[-1] if len(hist) else None
        ratio = height / float(expected_height(das))
        row = dict(das=das, height_cm=height, leaf_count=leaves, spad=spad, leaf_scorch=scorch,
                   empty_pod_pct=pods if das >= 70 else 0.0, soil_n=sn, soil_p=sp, soil_k=sk, soil_ca=sca,
                   soil_ph=sph, soil_moisture=moist, growth_ratio=ratio,
                   leaf_ratio=leaves / float(expected_leaves(das)),
                   ratio_change=0.0 if prev is None else ratio - prev)
        proba = stress_b["model"].predict_proba(pd.DataFrame([row])[STRESS_FEATURES])[0]
        stress, conf = stress_b["classes"][proba.argmax()], proba.max()
        status = delay_status(ratio)
        title, actions, checks = stress_plan(stress, das)

        m1, m2, m3 = st.columns(3)
        m1.metric("Growth stage", stage_of(das), f"day {das}")
        m2.metric("Growth vs expected", f"{ratio:.0%}", status, delta_color="off")
        m3.metric("Stress result", title, f"{conf:.0%} confidence", delta_color="off")

        needs_alert = (stress != "Healthy" and conf >= 0.6) or status != "On track"
        if needs_alert:
            lines = [f"Peanut alert for {field} (day {das}, {stage_of(das)})",
                     f"Growth: {status}, {ratio:.0%} of expected height."]
            if stress != "Healthy":
                lines.append(f"Likely problem: {title} ({conf:.0%} confidence).")
                lines += ["Do: " + x for x in actions]
            else:
                lines += delay_plan(status)
            text = "\n".join(lines)
            st.error(text)
            st.info(send_telegram(text))
        else:
            st.success("Crop is healthy and on track.")

        if actions or checks or status != "On track":
            st.markdown("**Fertilizer and field advice**")
            for x in actions + checks + delay_plan(status):
                st.write("- " + x)
        st.caption("Next step for this stage: " + stage_tip(das))
        st.caption("Doses are typical starting values per hectare. Confirm with a soil test or your local agriculture office.")
        save_row(dict(field_name=field, obs_date=str(obs_date), das=das, height_cm=height, leaf_count=leaves,
                      spad=spad, soil_n=sn, soil_p=sp, soil_k=sk, soil_ca=sca, growth_ratio=round(ratio, 3),
                      growth_status=status, stress=stress, confidence=round(float(conf), 3),
                      alert_sent=int(needs_alert)))

    h = read_history()
    if len(h):
        st.subheader("Growth curve")
        sel = st.selectbox("Field", sorted(h.field_name.unique()))
        fh = read_history(sel)
        chart = pd.DataFrame({"Actual height (cm)": fh.height_cm.values,
                              "Expected height (cm)": expected_height(fh.das.values)}, index=fh.das.values)
        chart.index.name = "Days after sowing"
        st.line_chart(chart)

# ------------------------------------------------------------------ tab 3
with tab3:
    st.subheader("All saved records")
    h = read_history()
    if len(h):
        st.dataframe(h.sort_values("id", ascending=False))
        st.download_button("Download CSV", h.to_csv(index=False), "peanut_history.csv")
    else:
        st.info("No records yet. Add a weekly record in tab 2.")
