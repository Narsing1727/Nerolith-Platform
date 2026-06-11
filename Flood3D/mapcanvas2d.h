#ifndef MAPCANVAS2D_H
#define MAPCANVAS2D_H
#include <QGraphicsView>
#include <QGraphicsScene>
#include <QMouseEvent>
#include <QWheelEvent>
#include <QResizeEvent>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <vector>

class MapCanvas2D : public QGraphicsView
{
    Q_OBJECT
public:
    explicit MapCanvas2D(QWidget* parent = nullptr);
    void setFlood(const std::vector<std::vector<float>>& flood);
    void setDEM(const std::vector<std::vector<float>>& dem);
    void clearDEM();
    void clearFlood();
    bool saveRiskMap(const QString& path);
    void mousePressEvent(QMouseEvent* event) override;
      void setContourLines(bool enabled);
    // NEW
    void fetchSatelliteTiles(double minLat, double maxLat,
                             double minLon, double maxLon,
                             int zoom = 16);
      void computeWatershed();
      void setWatershedVisible(bool v);

    //smart zones
      void setTWI(const std::vector<std::vector<float>>& twi);
      void clearTWI();
      void setTWIVisible(bool enabled);
signals:
    void cellClicked(int row, int col);

protected:
    void wheelEvent(QWheelEvent* event) override;
    void resizeEvent(QResizeEvent* event) override;

private:
    QGraphicsScene* scene;
    QGraphicsPixmapItem* floodOverlayItem = nullptr;
    std::vector<std::vector<float>> demGrid;
    std::vector<std::vector<float>> floodGrid;
    bool showFlood = false;
    bool hasDEM    = false;
    void renderDEM();

    // Satellite
    QNetworkAccessManager* network = nullptr;
    QImage satelliteImage;
    bool   hasSatellite = false;

    int tileMinX = 0, tileMaxX = 0;
    int tileMinY = 0, tileMaxY = 0;
    int currentZoom = 16;

    QMap<QPair<int,int>, QImage> fetchedTiles;
    QSet<QPair<int,int>>         pendingTiles;

    int  lonToTileX(double lon, int zoom);
    int  latToTileY(double lat, int zoom);
    void tryStitch();
    void onTileReady(QNetworkReply* reply);
    //Contour lines
    bool showContours = false;
    void drawContourLines(QPainter& painter,
                          int satW, int satH);
    //watershed
    std::vector<std::vector<int>> watershedGrid;
    bool showWatershed = false;
    void drawWatershed(QPainter& painter,
                       int satW, int satH);
    //smart zones

    std::vector<std::vector<float>> twiGrid;
    bool showTWI = false;
    void drawTWIZones(QPainter& painter, int satW, int satH);


};
#endif
