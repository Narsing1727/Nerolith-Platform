import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("error_grid.csv")

# reshape into grid
rows = df["i"].max() + 1
cols = df["j"].max() + 1

error_grid = df.pivot(index="i", columns="j", values="error").values

plt.figure(figsize=(8, 6))
plt.imshow(error_grid, cmap="seismic")
plt.colorbar(label="ML - Physics Error")
plt.title("Flood ML Error Grid")
plt.xlabel("j")
plt.ylabel("i")
plt.show()
