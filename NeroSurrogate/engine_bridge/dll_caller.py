import ctypes
import numpy as np
from pathlib import Path
from loguru import logger
from config import DLL_PATH


class FloodEngineDLL:
    def __init__(self, dll_path: str = DLL_PATH):
        self._ptr = None
        self._lib = self._load(dll_path)
        self._bind()
        self._ptr = self._lib.createEngine()
        if not self._ptr:
            raise RuntimeError("createEngine() returned null")

    def _load(self, path: str):
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"FloodEngine.dll not found: {path}")
        return ctypes.CDLL(str(p))

    def _bind(self):
        lib = self._lib
        vp  = ctypes.c_void_p

        lib.createEngine.restype  = vp
        lib.createEngine.argtypes = []

        lib.destroyEngine.restype  = None
        lib.destroyEngine.argtypes = [vp]

        lib.setDEM.restype  = None
        lib.setDEM.argtypes = [vp, ctypes.POINTER(ctypes.c_double),
                                ctypes.c_int, ctypes.c_int]

        lib.setRainfall.restype  = None
        lib.setRainfall.argtypes = [vp, ctypes.c_double]

        lib.setCellSize.restype  = None
        lib.setCellSize.argtypes = [vp, ctypes.c_double]

        lib.setManningN.restype  = None
        lib.setManningN.argtypes = [vp, ctypes.c_double]

        lib.setDuration.restype  = None
        lib.setDuration.argtypes = [vp, ctypes.c_double]

        lib.setSoilParams.restype  = None
        lib.setSoilParams.argtypes = [vp, ctypes.c_double,
                                          ctypes.c_double,
                                          ctypes.c_double]

        lib.runFlood.restype  = None
        lib.runFlood.argtypes = [vp]

        lib.runFloodBlended.restype  = None
        lib.runFloodBlended.argtypes = [vp]

        lib.getFloodGrid.restype  = ctypes.POINTER(ctypes.c_double)
        lib.getFloodGrid.argtypes = [vp]

        lib.getRows.restype  = ctypes.c_int
        lib.getRows.argtypes = [vp]

        lib.getCols.restype  = ctypes.c_int
        lib.getCols.argtypes = [vp]

        lib.getTWIGrid.restype  = ctypes.POINTER(ctypes.c_double)
        lib.getTWIGrid.argtypes = [vp]

        lib.freeTWIGrid.restype  = None
        lib.freeTWIGrid.argtypes = [ctypes.POINTER(ctypes.c_double)]

    def set_dem(self, dem: np.ndarray):
        if dem.ndim != 2:
            raise ValueError(f"DEM must be 2D, got {dem.shape}")
        dem_c = np.ascontiguousarray(dem, dtype=np.float64)
        rows, cols = dem_c.shape
        ptr = dem_c.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        self._lib.setDEM(self._ptr, ptr, rows, cols)

    def set_rainfall(self, v: float):   self._lib.setRainfall(self._ptr, float(v))
    def set_cell_size(self, v: float):  self._lib.setCellSize(self._ptr, float(v))
    def set_manning_n(self, v: float):  self._lib.setManningN(self._ptr, float(v))
    def set_duration(self, v: float):   self._lib.setDuration(self._ptr, float(v))

    def set_soil_params(self, Ks: float, psi: float, dTheta: float):
        self._lib.setSoilParams(self._ptr, float(Ks), float(psi), float(dTheta))

    def run_flood(self):         self._lib.runFlood(self._ptr)
    def run_flood_blended(self): self._lib.runFloodBlended(self._ptr)

    def get_flood_grid(self) -> np.ndarray:
        rows = self._lib.getRows(self._ptr)
        cols = self._lib.getCols(self._ptr)
        if rows == 0 or cols == 0:
            raise RuntimeError("No DEM set — call set_dem() first")
        ptr = self._lib.getFloodGrid(self._ptr)
        return np.ctypeslib.as_array(ptr, shape=(rows * cols,)).copy().reshape(rows, cols)

    def get_twi_grid(self) -> np.ndarray:
        rows = self._lib.getRows(self._ptr)
        cols = self._lib.getCols(self._ptr)
        ptr  = self._lib.getTWIGrid(self._ptr)
        arr  = np.ctypeslib.as_array(ptr, shape=(rows * cols,)).copy()
        self._lib.freeTWIGrid(ptr)
        return arr.reshape(rows, cols)

    def get_shape(self) -> tuple[int, int]:
        return self._lib.getRows(self._ptr), self._lib.getCols(self._ptr)

    def run_scenario(self, dem, rainfall, duration, manning_n,
                     Ks, psi, dTheta, cell_size=30.0, blended=False) -> np.ndarray:
        self.set_dem(dem)
        self.set_rainfall(rainfall)
        self.set_duration(duration)
        self.set_manning_n(manning_n)
        self.set_soil_params(Ks, psi, dTheta)
        self.set_cell_size(cell_size)
        if blended:
            self.run_flood_blended()
        else:
            self.run_flood()
        return self.get_flood_grid()

    def destroy(self):
        if self._ptr:
            self._lib.destroyEngine(self._ptr)
            self._ptr = None

    def __del__(self):      self.destroy()
    def __enter__(self):    return self
    def __exit__(self, *_): self.destroy()