"""Trains both models, prints metrics, saves models and charts. Run: python train_models.py"""
import json, joblib, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, f1_score, classification_report, ConfusionMatrixDisplay
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from common import *


def candidates(cat_cols):
    pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_cols)],
                            remainder="passthrough") if cat_cols else "passthrough"
    return {
        "RandomForest": Pipeline([("pre", pre), ("m", RandomForestClassifier(n_estimators=200, min_samples_leaf=2, class_weight="balanced", random_state=1, n_jobs=-1))]),
        "GradientBoosting": Pipeline([("pre", pre), ("m", HistGradientBoostingClassifier(random_state=1))]),
    }


def run(name, X_tr, X_te, y_tr, y_te, cat_cols, features, out_model, out_png):
    results, best, best_f1 = {}, None, -1
    for label, pipe in candidates(cat_cols).items():
        pipe.fit(X_tr, y_tr)
        pred = pipe.predict(X_te)
        acc, f1 = accuracy_score(y_te, pred), f1_score(y_te, pred, average="macro")
        results[label] = {"accuracy": round(acc, 4), "macro_f1": round(f1, 4)}
        if f1 > best_f1: best, best_f1, best_name = pipe, f1, label
    print(f"\n=== {name} ===\n{json.dumps(results, indent=2)}\nBest: {best_name}")
    pred = best.predict(X_te)
    print(classification_report(y_te, pred))
    fig, ax = plt.subplots(figsize=(6, 5))
    ConfusionMatrixDisplay.from_predictions(y_te, pred, ax=ax, xticks_rotation=30, colorbar=False)
    ax.set_title(f"{name}: {best_name}"); fig.tight_layout(); fig.savefig(out_png, dpi=150); plt.close(fig)
    joblib.dump({"model": best, "features": features, "classes": list(best.classes_)}, out_model, compress=3)
    return {"best": best_name, **results[best_name], "all": results}


# 1. Soil suitability
s = pd.read_csv("data/soil_suitability_dataset.csv")
feats = SOIL_CAT + SOIL_NUM
Xtr, Xte, ytr, yte = train_test_split(s[feats], s["suitability"], test_size=0.2, stratify=s["suitability"], random_state=1)
m1 = run("Soil suitability", Xtr, Xte, ytr, yte, SOIL_CAT, feats, "models/soil_model.joblib", "reports/soil_confusion_matrix.png")

# 2. Stress detection. Split by plant so one plant never appears in both train and test.
g = pd.read_csv("data/peanut_growth_stress_dataset.csv")
tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=1).split(g, groups=g.plant_id))
m2 = run("Nutrient stress", g.iloc[tr][STRESS_FEATURES], g.iloc[te][STRESS_FEATURES],
         g.iloc[tr]["stress_label"], g.iloc[te]["stress_label"], [], STRESS_FEATURES,
         "models/stress_model.joblib", "reports/stress_confusion_matrix.png")
json.dump({"soil": m1, "stress": m2}, open("reports/metrics.json", "w"), indent=2)
