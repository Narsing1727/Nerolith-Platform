#include "satelitetexture.h"
#include <QDebug>
#include <QtMath>
#include <QNetworkRequest>
#include <QPainter>

SatelliteTexture::SatelliteTexture(QObject* parent)
    : QObject(parent)
{
    network = new QNetworkAccessManager(this);
    connect(network, &QNetworkAccessManager::finished,
            this,    &SatelliteTexture::onReplyFinished);
}

SatelliteTexture::~SatelliteTexture()
{
    delete texture;
}

/* ========== TILE MATH ========== */

int SatelliteTexture::lonToTileX(double lon, int zoom)
{
    return int(floor((lon + 180.0) / 360.0 * pow(2.0, zoom)));
}

int SatelliteTexture::latToTileY(double lat, int zoom)
{
    double latRad = qDegreesToRadians(lat);
    return int(floor(
        (1.0 - log(tan(latRad) + 1.0/cos(latRad)) / M_PI)
        / 2.0 * pow(2.0, zoom)
        ));
}

/* ========== SINGLE TILE (old method) ========== */

void SatelliteTexture::fetchTile(double lat, double lon, int zoom)
{
    fetchTiles(lat - 0.01, lat + 0.01,
               lon - 0.01, lon + 0.01,
               zoom);
}

/* ========== MULTI TILE ========== */

void SatelliteTexture::fetchTiles(double minLat, double maxLat,
                                  double minLon, double maxLon,
                                  int zoom)
{
    // Clear previous state
    fetchedTiles.clear();
    pendingTiles.clear();
    textureReady  = false;
    multiMode     = true;
    currentZoom   = zoom;

    // Note: Y tile is INVERTED (higher lat = lower Y number)
    tileMinX = lonToTileX(minLon, zoom);
    tileMaxX = lonToTileX(maxLon, zoom);
    tileMinY = latToTileY(maxLat, zoom);  // maxLat → minY
    tileMaxY = latToTileY(minLat, zoom);  // minLat → maxY

    int totalTiles = (tileMaxX - tileMinX + 1) *
                     (tileMaxY - tileMinY + 1);

    qDebug() << "Fetching" << totalTiles << "tiles"
             << "X:" << tileMinX << "-" << tileMaxX
             << "Y:" << tileMinY << "-" << tileMaxY;

    // Limit tiles to avoid too many requests
    if (totalTiles > 256) {
        qWarning() << "Too many tiles! Reducing zoom by 1";
        fetchTiles(minLat, maxLat, minLon, maxLon, zoom - 1);
        return;
    }

    // Fetch each tile
    for (int y = tileMinY; y <= tileMaxY; y++) {
        for (int x = tileMinX; x <= tileMaxX; x++) {
            QPair<int,int> key(x, y);
            pendingTiles.insert(key);

            QString url = QString(
                              "https://server.arcgisonline.com/ArcGIS/rest/services/"
                              "World_Imagery/MapServer/tile/%1/%2/%3")
                              .arg(zoom).arg(y).arg(x);

            QNetworkRequest request(url);
            request.setHeader(QNetworkRequest::UserAgentHeader,
                              "Flood3D/1.0");

            // Store key in request attribute
            request.setAttribute(
                QNetworkRequest::User,
                QVariant::fromValue(key));

            network->get(request);
        }
    }
}

/* ========== REPLY ========== */

void SatelliteTexture::onReplyFinished(QNetworkReply* reply)
{
    if (reply->error() != QNetworkReply::NoError) {
        qWarning() << "Tile fetch failed:" << reply->errorString();
        reply->deleteLater();
        return;
    }

    QByteArray data = reply->readAll();

    // Get tile key from request
    QPair<int,int> key = reply->request()
                              .attribute(QNetworkRequest::User)
                              .value<QPair<int,int>>();

    reply->deleteLater();

    QImage img;
    if (!img.loadFromData(data)) {
        qWarning() << "Failed to decode tile" << key.first << key.second;
        pendingTiles.remove(key);
        return;
    }

    // qDebug() << "Tile received:" << key.first << key.second;

    fetchedTiles[key] = img;
    pendingTiles.remove(key);

    // Try stitching when all tiles received
    if (pendingTiles.isEmpty())
        tryStitch();
}

/* ========== STITCH ========== */

void SatelliteTexture::tryStitch()
{
    int cols = tileMaxX - tileMinX + 1;
    int rows = tileMaxY - tileMinY + 1;

    int tileW = 256;
    int tileH = 256;

    QImage stitched(cols * tileW, rows * tileH,
                    QImage::Format_RGB888);
    stitched.fill(Qt::black);

    QPainter painter(&stitched);

    for (int y = tileMinY; y <= tileMaxY; y++) {
        for (int x = tileMinX; x <= tileMaxX; x++) {
            QPair<int,int> key(x, y);

            if (!fetchedTiles.contains(key)) {
                qWarning() << "Missing tile:" << x << y;
                continue;
            }

            int px = (x - tileMinX) * tileW;
            int py = (y - tileMinY) * tileH;

            painter.drawImage(px, py, fetchedTiles[key]);
        }
    }

    painter.end();

    qDebug() << "Stitched image:"
             << stitched.width() << "x" << stitched.height();

    uploadToGPU(stitched);
}

/* ========== GPU UPLOAD ========== */
void SatelliteTexture::uploadToGPU(const QImage& img)
{
    delete texture;

    // Convert to highest quality format first
    QImage best = img.convertToFormat(QImage::Format_RGBA8888)
                      .mirrored();

    texture = new QOpenGLTexture(best);
    texture->setMinificationFilter(QOpenGLTexture::LinearMipMapLinear);
    texture->setMagnificationFilter(QOpenGLTexture::Linear);
    texture->setWrapMode(QOpenGLTexture::ClampToEdge);
    texture->setMaximumAnisotropy(16.0f);
    texture->generateMipMaps();

    textureReady = true;
    qDebug() << "Texture size:" << img.width() << "x" << img.height();
    emit tileReady();
}
/* ========== BIND ========== */

void SatelliteTexture::bind(int unit)
{
    if (texture && textureReady)
        texture->bind(unit);
}

void SatelliteTexture::release()
{
    if (texture && textureReady)
        texture->release();
}
