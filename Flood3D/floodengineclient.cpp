#include "FloodEngineClient.h"
#include <QDebug>

FloodEngineClient::FloodEngineClient() {}

FloodEngineClient::~FloodEngineClient()
{
    if (engineHandle && destroyEngine)
        destroyEngine(engineHandle);
    if (engineLib.isLoaded())
        engineLib.unload();
}

bool FloodEngineClient::init()
{
    engineLib.setFileName("FloodEngine");



    if (!engineLib.load()) {
        qDebug() << "DLL load failed:" << engineLib.errorString();
        return false;
    }

    createEngine     = (createEngine_t)    engineLib.resolve("createEngine");
    destroyEngine    = (destroyEngine_t)   engineLib.resolve("destroyEngine");
    setDEM           = (setDEM_t)          engineLib.resolve("setDEM");
    setRainfall_fn   = (setRainfall_t)     engineLib.resolve("setRainfall");
    runFlood         = (runFlood_t)        engineLib.resolve("runFlood");
    runFloodBlended  = (runFloodBlended_t) engineLib.resolve("runFloodBlended");
    getFloodGrid     = (getFloodGrid_t)    engineLib.resolve("getFloodGrid");
    getRows          = (getRows_t)         engineLib.resolve("getRows");
    getCols          = (getCols_t)         engineLib.resolve("getCols");
    loadRFModel_fn   = (loadRFModel_t)     engineLib.resolve("loadRFModel");
    setBlendAlpha_fn = (setBlendAlpha_t)   engineLib.resolve("setBlendAlpha");
    setCellSize_fn   = (setCellSize_t)     engineLib.resolve("setCellSize");
    setManningN_fn   = (setManningN_t)     engineLib.resolve("setManningN");
    setDuration_fn   = (setDuration_t)     engineLib.resolve("setDuration");
    setSoilParams_fn = (setSoilParams_t)   engineLib.resolve("setSoilParams");
    getTWIGrid_fn    = (getTWIGrid_t)      engineLib.resolve("getTWIGrid");
    freeTWIGrid_fn   = (freeTWIGrid_t)     engineLib.resolve("freeTWIGrid");

    if (!createEngine || !setDEM || !runFlood || !getFloodGrid) {
        qDebug() << "DLL symbols missing";
        return false;
    }



    setSWEDuration_fn = (setSWEDuration_t)engineLib.resolve("setSWEDuration");

    engineHandle = createEngine();
    qDebug() << "FloodEngine initialized";
    return true;
}

bool FloodEngineClient::isReady() const
{
    return engineHandle && setDEM && setRainfall_fn && runFlood && getFloodGrid;
}

void FloodEngineClient::loadDEM(const std::vector<std::vector<float>>& dem)
{
    if (!engineHandle) return;
    rows = dem.size();
    cols = dem[0].size();
    std::vector<double> flat(rows * cols);
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            flat[i * cols + j] = dem[i][j];
    setDEM(engineHandle, flat.data(), rows, cols);
}

std::vector<std::vector<float>> FloodEngineClient::predictFlood(double rainfall)
{
    std::vector<std::vector<float>> grid;
    if (!engineHandle) return grid;
    setRainfall_fn(engineHandle, rainfall);
    runFlood(engineHandle);
    int r = getRows(engineHandle);
    int c = getCols(engineHandle);
    const double* flat = getFloodGrid(engineHandle);
    grid.assign(r, std::vector<float>(c));
    for (int i = 0; i < r; i++)
        for (int j = 0; j < c; j++)
            grid[i][j] = static_cast<float>(flat[i * c + j]);

    m_lastGrid = grid;
    return grid;
}

std::vector<std::vector<float>> FloodEngineClient::predictFloodBlended(
    double rainfall, double alpha)
{
    std::vector<std::vector<float>> grid;
    if (!engineHandle) return grid;

    setRainfall_fn(engineHandle, rainfall);
    if (setBlendAlpha_fn) setBlendAlpha_fn(engineHandle, alpha);

    if (runFloodBlended)
        runFloodBlended(engineHandle);
    else
        runFlood(engineHandle);  // fallback to pure physics

    int r = getRows(engineHandle);
    int c = getCols(engineHandle);
    const double* flat = getFloodGrid(engineHandle);
    grid.assign(r, std::vector<float>(c));
    for (int i = 0; i < r; i++)
        for (int j = 0; j < c; j++)
            grid[i][j] = static_cast<float>(flat[i * c + j]);
    return grid;
}

std::vector<std::vector<float>> FloodEngineClient::getTWI()
{
    std::vector<std::vector<float>> grid;
    qDebug() << "getTWI called, rows=" << rows << "cols=" << cols;
    if (!engineHandle || !getTWIGrid_fn || !freeTWIGrid_fn) return grid;

    double* flat = getTWIGrid_fn(engineHandle);
    if (!flat) return grid;

    grid.assign(rows, std::vector<float>(cols));
    for (int i = 0; i < rows; i++)
        for (int j = 0; j < cols; j++)
            grid[i][j] = static_cast<float>(flat[i * cols + j]);

    freeTWIGrid_fn(flat);
    return grid;
}

bool FloodEngineClient::loadRFModel(const char* path)
{
    if (!engineHandle || !loadRFModel_fn) return false;
    return loadRFModel_fn(engineHandle, path) == 1;
}

void FloodEngineClient::setBlendAlpha(double alpha)
{
    if (engineHandle && setBlendAlpha_fn)
        setBlendAlpha_fn(engineHandle, alpha);
}

void FloodEngineClient::setCellSize(double metres)
{
    if (engineHandle && setCellSize_fn)
        setCellSize_fn(engineHandle, metres);
}

void FloodEngineClient::setManningN(double n)
{
    if (engineHandle && setManningN_fn)
        setManningN_fn(engineHandle, n);
}

void FloodEngineClient::setDuration(double hours)
{
    if (engineHandle && setDuration_fn)
        setDuration_fn(engineHandle, hours);
}

void FloodEngineClient::setSoilParams(double Ks, double psi, double dTheta)
{
    if (engineHandle && setSoilParams_fn)
        setSoilParams_fn(engineHandle, Ks, psi, dTheta);
}

void FloodEngineClient::setSWEDuration(double seconds)
{
    if (engineHandle && setSWEDuration_fn)
        setSWEDuration_fn(engineHandle, seconds);
}

void FloodEngineClient::setRainfall(double mm_per_hr)
{
    if (engineHandle && setRainfall_fn)
        setRainfall_fn(engineHandle, mm_per_hr);
}
