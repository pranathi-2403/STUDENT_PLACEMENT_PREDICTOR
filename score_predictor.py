
# ===== score_predictor.py =====
import pandas as pd
import joblib

def predict_score(input_data: dict) -> dict:
    placement_model = joblib.load("models/placement_model.pkl")
    company_model = joblib.load("models/company_fit_model.pkl")
    scaler = joblib.load("models/scaler.pkl")
    feature_cols = joblib.load("models/feature_columns.pkl")

    df = pd.DataFrame([input_data])
    df_encoded = pd.get_dummies(df)
    df_encoded = df_encoded.reindex(columns=feature_cols, fill_value=0)

    scaled_input = scaler.transform(df_encoded)

    placement_prediction = placement_model.predict(scaled_input)[0]
    company_prediction = company_model.predict(scaled_input)[0]

    return {
        "placement_readiness": placement_prediction,
        "company_fit": company_prediction
    }
