import csv
import numpy as np
from sklearn.ensemble import RandomForestRegressor

# ---------- File Path ----------
csv_file_path = r"C:\Users\LEdwa\AI_Pokegrader\trainingData.txt"  # update with your CSV path

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

# ---------- Optional: Sample Predictions ----------
# sample_preds = model.predict(X_train[:5])
# print("Sample predictions:", sample_preds)
