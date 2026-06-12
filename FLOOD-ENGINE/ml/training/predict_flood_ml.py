import joblib
import numpy as np

model = joblib.load("flood_rf_model.pkl")

x = np.array([[10,0,3,145]])  # SAME ORDER
y = model.predict(x)

print("Python RF prediction:", y[0])
