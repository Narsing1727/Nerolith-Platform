#ifndef FLOODENGINECLIENT_H
#define FLOODENGINECLIENT_H
#include <vector>
#include <QLibrary>

class FloodEngineClient
{
public:
    FloodEngineClient();
    ~FloodEngineClient();

    bool init();
    void loadDEM(const std::vector<std::vector<float>>& dem);

    std::vector<std::vector<float>> predictFlood(double rainfall);
    std::vector<std::vector<float>> predictFloodBlended(double rainfall, double alpha = 0.7);
    std::vector<std::vector<float>> getTWI();

    bool loadRFModel(const char* path);
    void setBlendAlpha(double alpha);
    void setCellSize(double metres);
    void setManningN(double n);
    void setDuration(double hours);
    void setSWEDuration(double seconds);
    void setRainfall(double mm_per_hr);
    void setSoilParams(double Ks, double psi, double dTheta);
    bool isReady() const;

    int                            getRowCount()      const { return rows; }
    int                            getColCount()      const { return cols; }
    std::vector<std::vector<float>> getLastFloodGrid() const { return m_lastGrid; }



private:
    QLibrary engineLib;
    void* engineHandle = nullptr;

    typedef void*          (*createEngine_t)();
    typedef void           (*destroyEngine_t)(void*);
    typedef void           (*setDEM_t)(void*, const double*, int, int);
    typedef void           (*setRainfall_t)(void*, double);
    typedef void           (*runFlood_t)(void*);
    typedef void           (*runFloodBlended_t)(void*);
    typedef const double*  (*getFloodGrid_t)(void*);
    typedef int            (*getRows_t)(void*);
    typedef int            (*getCols_t)(void*);
    typedef int            (*loadRFModel_t)(void*, const char*);
    typedef void           (*setBlendAlpha_t)(void*, double);
    typedef void           (*setCellSize_t)(void*, double);
    typedef void           (*setManningN_t)(void*, double);
    typedef void           (*setDuration_t)(void*, double);
    typedef void           (*setSWEDuration_t)(void*, double);
    typedef void           (*setSoilParams_t)(void*, double, double, double);
    typedef double*        (*getTWIGrid_t)(void*);
    typedef void           (*freeTWIGrid_t)(double*);

    createEngine_t     createEngine     = nullptr;
    destroyEngine_t    destroyEngine    = nullptr;
    setDEM_t           setDEM           = nullptr;
    setRainfall_t      setRainfall_fn   = nullptr;
    runFlood_t         runFlood         = nullptr;
    runFloodBlended_t  runFloodBlended  = nullptr;
    getFloodGrid_t     getFloodGrid     = nullptr;
    getRows_t          getRows          = nullptr;
    getCols_t          getCols          = nullptr;
    loadRFModel_t      loadRFModel_fn   = nullptr;
    setBlendAlpha_t    setBlendAlpha_fn = nullptr;
    setCellSize_t      setCellSize_fn   = nullptr;
    setManningN_t      setManningN_fn   = nullptr;
    setDuration_t      setDuration_fn   = nullptr;
    setSWEDuration_t   setSWEDuration_fn = nullptr;
    setSoilParams_t    setSoilParams_fn = nullptr;
    getTWIGrid_t       getTWIGrid_fn    = nullptr;
    freeTWIGrid_t      freeTWIGrid_fn   = nullptr;

    std::vector<std::vector<float>> m_lastGrid;


    int rows = 0;
    int cols = 0;
};
#endif
