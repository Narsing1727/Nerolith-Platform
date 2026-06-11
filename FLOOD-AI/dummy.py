import numpy as np
import os

os.makedirs("data/dem", exist_ok=True)
os.makedirs("data/boundaries", exist_ok=True)

rows, cols = 100, 100

# DEM - elevation grid, higher in top-left, lower bottom-right (water flows down-right)
elevation = np.zeros((rows, cols), dtype=np.float64)
for i in range(rows):
    for j in range(cols):
        elevation[i, j] = 100.0 - (i * 0.5) - (j * 0.3) + np.random.uniform(-2, 2)

np.save("data/dem/elevation.npy", elevation)
print("Saved data/dem/elevation.npy")

# Boundary map - divide grid into 25 watershed regions (5x5 grid of zones)
boundary_map = np.zeros((rows, cols), dtype=np.int32)
label = 1
for i in range(5):
    for j in range(5):
        r_start = i * 20
        r_end = r_start + 20
        c_start = j * 20
        c_end = c_start + 20
        boundary_map[r_start:r_end, c_start:c_end] = label
        label += 1

np.save("data/boundaries/watershed.npy", boundary_map)
print("Saved data/boundaries/watershed.npy")

print(f"\nDEM shape: {elevation.shape}")
print(f"Elevation range: {elevation.min():.1f}m - {elevation.max():.1f}m")
print(f"Boundary regions: {len(np.unique(boundary_map)) - 1} zones")
print("\nDone. Now run: python main.py")