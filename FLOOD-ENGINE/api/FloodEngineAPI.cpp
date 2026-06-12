#define FLOODENGINE_EXPORTS
#include "FloodEngineAPI.h"
#include "raster.h"

// Internal engine state
struct FloodEngine {
    Raster      raster;
    RandomForest rf;
    bool        rfLoaded   = false;

    // last computed flood grid (flat, row-major)
    std::vector<double> flood;

    // params (all have sensible defaults)
    int    rows       = 0;
    int    cols       = 0;
    double rainfall   = 10.0;  // mm/hr
    double cellSize   = 30.0;  // metres
    double manningN   = 0.035;
    double durationHr = 1.0;
    double Ks         = 6.8;
    double psi        = 166.8;
    double dTheta     = 0.486;
    double alpha      = 0.7;   // ML blend weight
    double sweSeconds = 3600.0; // SWE sim duration
};

// Flatten a 2-D grid into engine->flood (row-major)
static void flatten(FloodEngine* e,
                    const std::vector<std::vector<double>>& g)
{
    e->flood.clear();
    e->flood.reserve(e->rows * e->cols);
    for (auto& row : g)
        for (double v : row)
            e->flood.push_back(v);
}

extern "C" {

void* createEngine() { return new FloodEngine(); }

void destroyEngine(void* ptr) {
    delete static_cast<FloodEngine*>(ptr);
}

//dem 

void setDEM(void* ptr, const double* dem, int rows, int cols) {
    auto* e = static_cast<FloodEngine*>(ptr);
    e->rows = rows;
    e->cols = cols;

    std::vector<std::vector<double>> g(rows, std::vector<double>(cols));
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            g[i][j] = dem[i * cols + j];

    e->raster.loadFromGrid(g);   
}


void setRainfall(void* ptr, double mm_per_hr) {
    static_cast<FloodEngine*>(ptr)->rainfall = mm_per_hr;
}

void setCellSize(void* ptr, double metres) {
    static_cast<FloodEngine*>(ptr)->cellSize = metres;
}

void setManningN(void* ptr, double n) {
    static_cast<FloodEngine*>(ptr)->manningN = n;
}

void setDuration(void* ptr, double hours) {
    static_cast<FloodEngine*>(ptr)->durationHr = hours;
}

void setSoilParams(void* ptr, double Ks, double psi, double dTheta) {
    auto* e  = static_cast<FloodEngine*>(ptr);
    e->Ks    = Ks;
    e->psi   = psi;
    e->dTheta = dTheta;
}


int loadRFModel(void* ptr, const char* path) {
    auto* e = static_cast<FloodEngine*>(ptr);
    e->rfLoaded = e->rf.loadModel(path);
    return e->rfLoaded ? 1 : 0;
}

void setBlendAlpha(void* ptr, double alpha) {
    static_cast<FloodEngine*>(ptr)->alpha = alpha;
}

void setSWEDuration(void* ptr, double seconds) {
    static_cast<FloodEngine*>(ptr)->sweSeconds = seconds;
}


// Mode 1 — static Manning + Green-Ampt (fast, no time stepping)
void runFlood(void* ptr) {
    auto* e = static_cast<FloodEngine*>(ptr);
    auto g  = e->raster.FloodDepthGridFinal(
        e->rainfall, e->cellSize, e->manningN,
        e->durationHr, e->Ks, e->psi, e->dTheta);
    flatten(e, g);
}

// Mode 2 — physics-ML blend (static, uses RF if loaded)
void runFloodBlended(void* ptr) {
    auto* e = static_cast<FloodEngine*>(ptr);

    if (!e->rfLoaded) {
        runFlood(ptr);   // fall back to pure physics if no model
        return;
    }

    auto g = e->raster.FloodDepthBlended(
        e->rf, e->rainfall, e->alpha,
        e->cellSize, e->manningN, e->durationHr,
        e->Ks, e->psi, e->dTheta);
    flatten(e, g);
}

// Mode 3 — SWE time-stepping; onFrame called per timestep for Qt animation.
// Qt side: pass a C function pointer that copies the frame into a QImage buffer.
void runSWE(void* ptr,
            void (*onFrame)(const double* grid, int rows, int cols, double elapsed))
{
    auto* e = static_cast<FloodEngine*>(ptr);

    e->raster.runSWE(
        e->rainfall,
        e->sweSeconds,
        e->manningN,
        e->cellSize,
        [e, onFrame](const std::vector<std::vector<double>>& h, double elapsed) {
            // flatten to a temporary buffer and fire the Qt callback
            std::vector<double> buf;
            buf.reserve(e->rows * e->cols);
            for (auto& row : h)
                for (double v : row)
                    buf.push_back(v);

            if (onFrame)
                onFrame(buf.data(), e->rows, e->cols, elapsed);

            // also keep the last frame in engine->flood for getFloodGrid()
            e->flood = std::move(buf);
        }
    );
}


const double* getFloodGrid(void* ptr) {
    return static_cast<FloodEngine*>(ptr)->flood.data();
}

int getRows(void* ptr) { return static_cast<FloodEngine*>(ptr)->rows; }
int getCols(void* ptr) { return static_cast<FloodEngine*>(ptr)->cols; }

// TWI grid — Qt uses this to colour risk overlay
// Caller must free the returned array with freeTWI()
double* getTWIGrid(void* ptr) {
    auto* e = static_cast<FloodEngine*>(ptr);
    auto twi = e->raster.computeTWI(e->cellSize);

    int n = e->rows * e->cols;
    double* buf = new double[n];
    int k = 0;
    for (auto& row : twi)
        for (double v : row)
            buf[k++] = v;
    return buf;
}

void freeTWIGrid(double* ptr) { delete[] ptr; }

}  