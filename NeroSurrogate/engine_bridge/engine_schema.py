from pydantic import BaseModel, Field


class SimulationInput(BaseModel):
    scenario_id:    str
    rainfall_mm_hr: float = Field(..., ge=1.0,   le=300.0)
    duration_hr:    float = Field(..., ge=0.5,   le=120.0)
    manning_n:      float = Field(..., ge=0.005, le=0.3)
    Ks:             float = Field(..., ge=0.1,   le=200.0)
    psi:            float = Field(..., ge=10.0,  le=500.0)
    dTheta:         float = Field(..., ge=0.05,  le=0.7)
    cell_size_m:    float = Field(30.0, ge=5.0,  le=100.0)
    dem_path:       str   = ""
    blended:        bool  = False


class SimulationOutput(BaseModel):
    scenario_id:        str
    rows:               int
    cols:               int
    max_depth_m:        float
    mean_depth_m:       float
    flooded_fraction:   float
    high_risk_cells:    int
    medium_risk_cells:  int
    flood_path:         str = ""
