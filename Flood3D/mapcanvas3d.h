#pragma once
#include <QOpenGLWidget>
#include <QOpenGLFunctions>
#include <QOpenGLShaderProgram>
#include "3D/headers/terrainmesh.h"
#include "3D/headers/cameracontroller.h"
#include "satelitetexture.h"
#include "riskmarker.h"
#include<QElapsedTimer>
#include <QPainter>
#include<vector>
#include "3D/headers/waterlayer.h"

#include "3D/headers/buildingmesh.h"
#include "3D/headers/roadnetwork.h"
#include <QFont>
class MapCanvas3D : public QOpenGLWidget, protected QOpenGLFunctions
{
    Q_OBJECT
public:
    explicit MapCanvas3D(QWidget* parent = nullptr);
    ~MapCanvas3D();
    void setDEM(const std::vector<std::vector<float>>& dem);
    void loadSatelliteTile(double lat, double lon, int zoom = 13);
    void loadSatelliteTiles(double minLat, double maxLat,
                            double minLon, double maxLon,
                            int zoom = 14);
    void setFlood(const std::vector<std::vector<float>>& flood);


    void fetchRoads(double minLat, double maxLat,
                    double minLon, double maxLon);
    void setRoadsVisible(bool v);



    void fetchBuildings(double minLat, double maxLat,
                        double minLon, double maxLon);
    void setBuildingsVisible(bool v);


    void setAIRiskMarkers(const std::vector<RiskMarker>& markers);


    void setSWEFrame(const std::vector<std::vector<float>>& frame);

protected:
    void initializeGL() override;
    void resizeGL(int w, int h) override;
    void paintGL() override;
    void mousePressEvent(QMouseEvent* e) override;
    void mouseMoveEvent(QMouseEvent* e) override;
    void wheelEvent(QWheelEvent* e) override;
    void keyPressEvent(QKeyEvent* e) override;
    void paintEvent(QPaintEvent* e) override;
private:


    WaterLayer waterLayer;
    bool showWater = true;



    RiskMarkerRenderer aiRiskMarkers;
    std::vector<RiskMarker> aiCurrentMarkers;
    std::vector<RiskMarker> currentMarkers;
    struct PopupInfo {
        QPoint  screenPos;
        int     row, col;
        float   depth;
        int     riskLevel;
        bool    visible = false;
    };





    RoadNetwork* roadNetwork = nullptr;
    bool showRoads = false;
    double geoMinLat, geoMaxLat, geoMinLon, geoMaxLon;
    PopupInfo activePopup;



    BuildingMesh* buildingMesh = nullptr;
    bool showBuildings = false;


    QPoint markerToScreen(const RiskMarker& m);
    RiskMarkerRenderer riskMarkers;
     QElapsedTimer      timer;
    QOpenGLShaderProgram* program = nullptr;
    TerrainMesh     terrain;
    CameraController camera;
    SatelliteTexture* satellite = nullptr;
    void drawSkyGradient();
    QOpenGLShaderProgram* skyProgram = nullptr;

signals:
    void markerClicked(int row, int col, float depth, int riskLevel);

    void aiMarkerClicked(const QString& regionId);
};
