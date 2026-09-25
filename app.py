from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, render_template, request
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "StudentsPerformance.csv"


def train_model():
    data = pd.read_csv(DATA_PATH)
    features = data[["reading score"]]
    target = data["math score"]
    x_train, x_test, y_train, y_test = train_test_split(
        features, target, test_size=0.2, random_state=42
    )

    model = LinearRegression()
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)

    return {
        "model": model,
        "data": data,
        "r2": float(r2_score(y_test, predictions)),
        "mse": float(mean_squared_error(y_test, predictions)),
    }


artifacts = train_model()
model = artifacts["model"]
data = artifacts["data"]
app = Flask(__name__)


@app.get("/")
def index():
    return render_template(
        "index.html",
        metrics={
            "r2": artifacts["r2"],
            "mse": artifacts["mse"],
            "students": len(data),
            "slope": float(model.coef_[0]),
            "intercept": float(model.intercept_),
        },
    )


@app.post("/api/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    value = payload.get("reading_score")

    try:
        reading_score = float(value)
    except (TypeError, ValueError):
        return jsonify({"error": "Enter a numeric reading score."}), 400

    if not 0 <= reading_score <= 100:
        return jsonify({"error": "Reading score must be between 0 and 100."}), 400

    prediction = float(model.predict(pd.DataFrame({"reading score": [reading_score]}))[0])
    return jsonify(
        {
            "reading_score": reading_score,
            "predicted_math_score": round(prediction, 1),
            "confidence_note": "Estimated from the relationship learned from 1,000 student records.",
        }
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
