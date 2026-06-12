import pandas as pd
import numpy as np
import joblib
import json
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

# ---------------- LOAD DATA ----------------
df = pd.read_csv("./flood_ml_dataset.csv")

FEATURES = [
    "rain_t",
    "rain_t_1",
    "flow_acc",
    "elevation"
]

TARGET = "depth_t1"

X = df[FEATURES]
y = df[TARGET]

# ---------------- SPLIT ----------------
split_idx = int(0.8 * len(df))

X_train = X.iloc[:split_idx]
X_test  = X.iloc[split_idx:]

y_train = y.iloc[:split_idx]
y_test  = y.iloc[split_idx:]

# ---------------- TRAIN RF ----------------
model = RandomForestRegressor(
    n_estimators=200,
    max_depth=20,
    n_jobs=-1,
    random_state=42
)

model.fit(X_train, y_train)

# ---------------- EVAL ----------------
y_pred = model.predict(X_test)

mae  = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print("MAE :", mae)
print("RMSE:", rmse)

# ---------------- FEATURE IMPORTANCE ----------------
importances = model.feature_importances_
for f, imp in zip(FEATURES, importances):
    print(f"{f}: {imp:.4f}")

# ---------------- SAVE PKL (OPTIONAL BACKUP) ----------------
joblib.dump(model, "flood_rf_model.pkl")

with open("ml_features.json", "w") as f:
    json.dump(FEATURES, f)

# ==========================================================
# 🔥 NEW PART: EXPORT RANDOM FOREST TO TXT (C++ EMBEDDING)
# ==========================================================

with open("rf_model.txt", "w") as f:
    # number of trees
    f.write(f"{len(model.estimators_)}\n")

    for est in model.estimators_:
        tree = est.tree_

        # number of nodes in this tree
        f.write(f"{tree.node_count}\n")

        for i in range(tree.node_count):
            left  = tree.children_left[i]
            right = tree.children_right[i]

            # leaf node
            if left == -1 and right == -1:
                value = tree.value[i][0][0]
                f.write(f"L {value}\n")
            else:
                feature   = tree.feature[i]
                threshold = tree.threshold[i]
                f.write(f"N {feature} {threshold} {left} {right}\n")

print("RF model exported to rf_model.txt (old-feature pipeline)")
