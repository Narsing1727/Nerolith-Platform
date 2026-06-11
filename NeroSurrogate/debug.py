# Run this in NeroSurrogate folder to check norm stats
import json, sys
sys.path.insert(0, r"D:\Desktop\NeroSurrogate\NeroSurrogate")

with open(r"D:\Desktop\NeroSurrogate\NeroSurrogate\output\datasets\norm_stats.json") as f:
    stats = json.load(f)

print("Channel normalization stats:")
for i, (name, mean, std) in enumerate(zip(stats['channels'], stats['means'], stats['stds'])):
    print(f"  ch{i} [{name:20s}] mean={mean:.4f} std={std:.4f}")

print("\nYour real DEM elevations are likely 200-400m")
print("Training DEM mean:", stats['means'][0], "std:", stats['stds'][0])
print("\nFor elevation=300m:")
print("  normalized =", (300 - stats['means'][0]) / stats['stds'][0])
print("If this is > 5 or < -5, model gets garbage input")