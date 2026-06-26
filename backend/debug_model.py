# debug_model.py
import joblib
import numpy as np
import pandas as pd
import os

MODEL_PATH = "model.joblib"
CSV_PATH = "students.csv"

saved = joblib.load(MODEL_PATH)
pipeline = saved["pipeline"]
features = saved["features"]
means = saved.get("means", {})
importances = saved.get("importances", {})

print("FEATURES:", features)
print("MEANS (sample):", {k: round(means.get(k,0),3) for k in features})
clf = pipeline.named_steps.get("model", None)
if clf is None:
    # maybe different name
    print("Pipeline steps:", pipeline.named_steps)
    clf = list(pipeline.named_steps.values())[-1]

print("Classifier type:", type(clf))
print("Classifier classes_:", getattr(clf, "classes_", "NO classes_"))
if hasattr(clf, "classes_"):
    print("classes_ array:", clf.classes_)

# Check dataset class balance if csv exists
if os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
    if "pass" in df.columns:
        print("Label distribution in CSV:")
        print(df["pass"].value_counts(normalize=False))
        print(df["pass"].value_counts(normalize=True))
    else:
        print("No 'pass' column in csv")

# Try some sample inputs (varied)
samples = [
    {f: means.get(f, 0) for f in features},  # mean input
    {features[0]: 95, features[1]:5, features[2]:95, features[3]:5, features[4]:3, features[5]:9, features[6]:1}, # very strong student
    {features[0]: 40, features[1]:1, features[2]:30, features[3]:0, features[4]:0, features[5]:3, features[6]:8}, # weak student
]

for s in samples:
    # fill missing features with mean
    row = [float(s.get(f, means.get(f, 0))) for f in features]
    X = pd.DataFrame([row], columns=features)
    probs = pipeline.predict_proba(X)[0]
    pred = pipeline.predict(X)[0]
    # get index of class 1 in classifier classes_
    cls = list(clf.classes_) if hasattr(clf, "classes_") else None
    print("\nSAMPLE:", s)
    print("predict ->", pred, "classes_ ->", cls)
    print("raw probs:", probs)
    if cls is not None:
        try:
            idx1 = list(cls).index(1)
            prob_pass = probs[idx1]
        except ValueError:
            # no class '1' in classes_
            prob_pass = None
        print("prob_pass (mapped):", prob_pass)
