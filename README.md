# Peanut Advisor: soil check, growth tracking, nutrient stress alerts

## What the project does
1. **Soil suitability.** Takes soil test values and says whether peanut can grow: Highly suitable, Moderately suitable or Not suitable. It also lists what to fix before sowing.
2. **Growth tracking over time.** Each weekly record is saved per field. The app compares your plant height with the expected curve for a peanut crop and flags a delay (On track, Mild delay below 90%, Severe delay below 75%).
3. **Stress detection.** A model reads growth, leaf greenness (SPAD), leaf scorch, soil N, P, K, Ca and pH, and predicts Healthy, N, P, K or Ca stress.
4. **Farmer alert.** If stress or delay is found, the app sends a Telegram message to the farmer.
5. **Fertilizer recommendation.** Gives a dose per hectare for the detected stress, adjusted for crop age.

## Files
| File | Purpose |
|---|---|
| data/soil_suitability_dataset.csv | 4,000 rows for the soil model |
| data/peanut_growth_stress_dataset.csv | 11,400 rows (760 plants, weekly records, day 7 to 105) |
| generate_data.py | Rebuilds both datasets (you can change sizes and ranges) |
| train_models.py | Trains and compares Random Forest and Gradient Boosting |
| models/ | Saved models used by the app |
| reports/ | Confusion matrices and metrics.json for your review |
| app.py | Streamlit app (the project you demo) |
| recommend.py, common.py | Fertilizer rules, growth curves, stages |

## Results (test data)
- Soil suitability: 90.4% accuracy, macro F1 0.88.
- Stress detection: 93.3% accuracy, macro F1 0.92. The test set uses plants the model never saw in training.

## Data honesty (say this in your review)
Both datasets are simulated from agronomy ranges (pH 6.0 to 6.8, Indian soil test ratings for N, P and K, a growth curve for bunch type peanut). Classes overlap on purpose and 15% of stressed plants have normal soil values, so the accuracy is not 100%. The accuracy shows the model learned the agronomy rules, not that it is proven in the field. Next phase: replace the simulated rows with your own field readings and retrain with `python train_models.py`.

## Run on your laptop
```
pip install -r requirements.txt
python generate_data.py      # optional, data is already included
python train_models.py       # optional, models are already included
streamlit run app.py
```
Open http://localhost:8501.

## Set up farmer alerts (Telegram, free)
1. In Telegram, message **@BotFather**, send `/newbot`, copy the token.
2. The farmer opens the new bot and sends `hi`.
3. Open `https://api.telegram.org/bot<TOKEN>/getUpdates` and copy the number in `"chat":{"id":...}`.
4. Set two values (see the deploy step for where):
```
TELEGRAM_TOKEN = "123456:ABC..."
TELEGRAM_CHAT_ID = "987654321"
```
For SMS instead, replace `send_telegram()` in app.py with a Twilio or Fast2SMS call. The rest stays the same.

## Deploy online (Streamlit Community Cloud, free)
1. Create a GitHub account and a new public repository.
2. Upload every file in this folder, keeping the `data/`, `models/` and `reports/` folders.
3. Go to https://share.streamlit.io and sign in with GitHub.
4. Click **Create app**, pick your repo, branch `main`, main file `app.py`, then **Deploy**.
5. Open **Settings > Secrets** and paste the two Telegram lines above.
6. Share the `*.streamlit.app` link with the farmer. It opens on a phone browser.

Known limit: on Streamlit Cloud the saved history (SQLite) resets when the app restarts. For a review demo this is fine. For real use, point `save_row()` and `read_history()` at a free Supabase or Google Sheets database.

Other options: Hugging Face Spaces (choose the Streamlit template) or Render (start command `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`).

## Adding real IoT later
Your ESP32 posts soil N, P, K, pH and moisture to the cloud. Replace the soil input boxes in tab 2 with the latest sensor reading. The model and rules stay the same.

## Review questions to prepare for
- **Is the data real?** No, it is simulated from agronomy ranges. Show generate_data.py.
- **Why not 99% accuracy?** Classes overlap and some stress cases hide in normal soil, as in a real field.
- **Is the fertilizer dose safe to follow?** The doses are typical starting values. The app tells the farmer to confirm with a soil test or the local agriculture office.
