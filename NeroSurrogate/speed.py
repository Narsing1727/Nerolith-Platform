import numpy as np
import time
import sys
import matplotlib.pyplot as plt

sys.path.insert(0, r"D:\Desktop\NeroSurrogate\NeroSurrogate")

from engine_bridge.dll_caller import FloodEngineDLL
from inference.surrogate_runner import SurrogateRunner

runner = SurrogateRunner()

rainfall, duration, manning_n = 120.0, 6.0, 0.035
Ks, psi, dTheta = 6.8, 166.8, 0.3

GRID_SIZES = [64, 128, 256, 512, 768, 1024]

cells_list      = []
physics_times   = []
surrogate_times = []

print("=" * 64)
print("  PHYSICS vs SURROGATE — SCALING BENCHMARK")
print("=" * 64)
print(f"\n  {'Grid':>10} {'Cells':>12} {'Physics(ms)':>14} {'Surrogate(ms)':>16} {'Speedup':>10}")
print("  " + "-" * 62)

for size in GRID_SIZES:
    rng = np.random.default_rng(42)
    x   = np.linspace(100, 50, size)
    dem = np.outer(np.ones(size), x) + rng.uniform(-2, 2, (size, size))

    with FloodEngineDLL() as eng:
        t0 = time.perf_counter()
        eng.run_scenario(dem=dem, rainfall=rainfall, duration=duration,
                         manning_n=manning_n, Ks=Ks, psi=psi, dTheta=dTheta)
        physics_ms = (time.perf_counter() - t0) * 1000

    runner.predict(dem=dem, rainfall=rainfall, duration=duration,
                   dTheta=dTheta, manning_n=manning_n)  # warmup
    t0 = time.perf_counter()
    runner.predict(dem=dem, rainfall=rainfall, duration=duration,
                   dTheta=dTheta, manning_n=manning_n)
    surrogate_ms = (time.perf_counter() - t0) * 1000

    cells = size * size
    cells_list.append(cells)
    physics_times.append(physics_ms)
    surrogate_times.append(surrogate_ms)

    speedup = physics_ms / surrogate_ms
    print(f"  {size:>4}x{size:<4} {cells:>12,} {physics_ms:>14.1f} {surrogate_ms:>16.1f} {speedup:>9.1f}x")

print("\n" + "=" * 64)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

ax1.plot(cells_list, physics_times,   'o-', color='#e74c3c', linewidth=2,
         markersize=8, label='FloodEngine (Physics)')
ax1.plot(cells_list, surrogate_times, 's-', color='#2ecc71', linewidth=2,
         markersize=8, label='NeroSurrogate (ML)')
ax1.set_xlabel('Grid Cells', fontsize=12)
ax1.set_ylabel('Time (ms)', fontsize=12)
ax1.set_title('Linear Scale', fontsize=13, fontweight='bold')
ax1.legend(fontsize=11)
ax1.grid(True, alpha=0.3)

ax2.loglog(cells_list, physics_times,   'o-', color='#e74c3c', linewidth=2,
           markersize=8, label='FloodEngine (Physics)')
ax2.loglog(cells_list, surrogate_times, 's-', color='#2ecc71', linewidth=2,
           markersize=8, label='NeroSurrogate (ML)')
ax2.set_xlabel('Grid Cells (log)', fontsize=12)
ax2.set_ylabel('Time (ms, log)', fontsize=12)
ax2.set_title('Log-Log Scale', fontsize=13, fontweight='bold')
ax2.legend(fontsize=11)
ax2.grid(True, alpha=0.3, which='both')

fig.suptitle('Nerolith: Physics Engine vs ML Surrogate Performance',
             fontsize=15, fontweight='bold')
plt.tight_layout()
plt.savefig('speed_comparison.png', dpi=150, bbox_inches='tight')
print("\n  Graph saved: speed_comparison.png")
plt.show()