import csv
import os
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import pickle

from paths import resource_path

# ---------- File Path ----------
csv_file_path = resource_path(os.path.join("trainingData.txt"))  # update with your CSV path

# ---------- Initialize Training Lists ----------
x_training = []
y_training = []

# ---------- Read CSV and Parse ----------
with open(csv_file_path, "r", newline="") as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if not row:
            continue  # skip empty lines

        # Extract PSA score from filename
        filename = row[0]  # e.g., "1.0PSA_Synthetic001.jpg"
        psa_score_str = filename.split('PSA')[0]  # get part before 'PSA'
        psa_score = float(psa_score_str)  # convert to float for regression

        # Extract features: surface, corners, center_h, center_v
        features = [float(val) for val in row[1:5]]  # convert to floats

        # Append to training lists
        x_training.append(features)
        y_training.append(psa_score)

# ---------- Convert to NumPy Arrays ----------
X_train = np.array(x_training)
y_train = np.array(y_training)

# ---------- Optional: Print Shapes ----------
print("X_train shape:", X_train.shape)
print("y_train shape:", y_train.shape)

# ---------- Train RandomForestRegressor ----------
model = RandomForestRegressor(n_estimators=200, random_state=42)
model.fit(X_train, y_train)

def predict_card_grade(surface, corners, centering_h, centering_v):
    # Create feature array for prediction
    input_data = np.array([[surface, corners, centering_h, centering_v]])
    predicted_grade = model.predict(input_data)[0]  # fetch scalar value

    return {
        "surface": round(surface, 2),
        "corners": round(corners, 2),
        "centering_h": round(centering_h, 2),
        "centering_v": round(centering_v, 2),
        "predicted_grade": round(predicted_grade, 1)
    }

# Save model to file
model_save_path = resource_path(os.path.join("trained_model.pkl"))
with open(model_save_path, "wb") as f:
    pickle.dump(model, f)

print(f"Model saved to: {model_save_path}")