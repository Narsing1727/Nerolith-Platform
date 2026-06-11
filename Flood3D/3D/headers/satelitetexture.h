#pragma once
#include <QObject>
#include <QImage>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QOpenGLTexture>
#include <QMap>

class SatelliteTexture : public QObject
{
    Q_OBJECT

public:
    explicit SatelliteTexture(QObject* parent = nullptr);
    ~SatelliteTexture();

    // Single tile (old)
    void fetchTile(double lat, double lon, int zoom = 13);

    // Multi-tile stitching (new)
    void fetchTiles(double minLat, double maxLat,
                    double minLon, double maxLon,
                    int zoom = 14);

    void bind(int unit = 0);
    void release();
    bool isReady() const { return textureReady; }

signals:
    void tileReady();

private slots:
    void onReplyFinished(QNetworkReply* reply);

private:
    // Tile math
    int    lonToTileX(double lon, int zoom);
    int    latToTileY(double lat, int zoom);

    // GPU
    void uploadToGPU(const QImage& img);

    // Stitching
    void tryStitch();

    QNetworkAccessManager* network  = nullptr;
    QOpenGLTexture*        texture  = nullptr;
    bool textureReady = false;

    // Multi-tile state
    struct TileKey {
        int x, y, zoom;
        bool operator<(const TileKey& o) const {
            if (zoom != o.zoom) return zoom < o.zoom;
            if (y != o.y) return y < o.y;
            return x < o.x;
        }
    };

    QMap<QPair<int,int>, QImage> fetchedTiles;  // (x,y) → image
    QSet<QPair<int,int>>         pendingTiles;  // still loading

    int tileMinX = 0, tileMaxX = 0;
    int tileMinY = 0, tileMaxY = 0;
    int currentZoom = 14;
    bool multiMode = false;
};
