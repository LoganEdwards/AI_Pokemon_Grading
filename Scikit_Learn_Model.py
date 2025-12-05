import numpy as np
import pickle
import os
from paths import resource_path

# ---------- Load Saved Model ----------
model_path = resource_path("trained_model.pkl")
with open(model_path, "rb") as f:
    model = pickle.load(f)

# ---------- Predict Function ----------
def predict_card_grade(surface, corners, centering_h, centering_v):
    input_data = np.array([[surface, corners, centering_h, centering_v]])
    predicted_grade = model.predict(input_data)[0]
    
    return {
        "surface": round(surface, 2),
        "corners": round(corners, 2),
        "centering_h": round(centering_h, 2),
        "centering_v": round(centering_v, 2),
        "predicted_grade": round(predicted_grade, 1)
    }
