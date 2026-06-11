#pragma once
#include <vector>

#ifdef _WIN32
  #ifdef FLOODENGINE_EXPORTS
    #define FLOOD_API __declspec(dllexport)
  #else
    #define FLOOD_API __declspec(dllimport)
  #endif
#else
  #define FLOOD_API
#endif

extern "C" {

FLOOD_API void* createEngine();

FLOOD_API void destroyEngine(void* engine);

FLOOD_API void setDEM(
    void* engine,
    const double* dem,
    int rows,
    int cols
);

FLOOD_API void setRainfall(
    void* engine,
    double rainfall
);

FLOOD_API void runFlood(void* engine);

FLOOD_API const double* getFloodGrid(void* engine);
FLOOD_API int getRows(void* engine);
FLOOD_API int getCols(void* engine);

}
