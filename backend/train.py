# train.py
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import joblib
import os

CSV_PATH = "students.csv"
MODEL_PATH = "model.joblib"

# Generate dataset
def create_dataset(n=500, seed=42):
    np.random.seed(seed)

    attendance = np.random.uniform(30, 100, n)
    study_hours = np.random.uniform(0, 10, n)
    internal_marks = np.random.uniform(0, 100, n)
    assignments = np.random.randint(0, 10, n)
    activities = np.random.randint(0, 5, n)

    previous_gpa = np.random.uniform(2, 10, n)
    screen_time = np.random.uniform(1, 12, n)  

    # synthetic score
    score = (
        attendance * 0.3 +
        study_hours * 5 +
        internal_marks * 0.4 +
        assignments * 1.5 +
        activities * 1 +
        previous_gpa * 4 -
        screen_time * 2
    )

    threshold = np.percentile(score, 50)  # median
    target = (score > threshold).astype(int)


    df = pd.DataFrame({
        "attendance": attendance,
        "study_hours": study_hours,
        "internal_marks": internal_marks,
        "assignments_submitted": assignments,
        "activities": activities,
        "previous_gpa": previous_gpa,
        "screen_time": screen_time,
        "pass": target
    })

    df.to_csv(CSV_PATH, index=False)
    print("Dataset created.")
    return df

# Create dataset if not exists
if not os.path.exists(CSV_PATH) or os.path.getsize(CSV_PATH) == 0:
    df = create_dataset()
else:
    df = pd.read_csv(CSV_PATH)

feature_cols = [
    "attendance",
    "study_hours",
    "internal_marks",
    "assignments_submitted",
    "activities",
    "previous_gpa",
    "screen_time"
]

X = df[feature_cols]
y = df["pass"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ML model pipeline
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("model", RandomForestClassifier(n_estimators=150, random_state=42))
])

pipeline.fit(X_train, y_train)

preds = pipeline.predict(X_test)
acc = accuracy_score(y_test, preds)

print("Accuracy:", acc)
print(classification_report(y_test, preds))

# feature importances
rf = pipeline.named_steps["model"]
importances = dict(zip(feature_cols, rf.feature_importances_.tolist()))

means = X_train.mean().to_dict()

joblib.dump({
    "pipeline": pipeline,
    "features": feature_cols,
    "means": means,
    "importances": importances
}, MODEL_PATH)

print("Model saved.")
