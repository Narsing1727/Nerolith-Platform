#include "mapcanvas2d.h"
#include <QGraphicsRectItem>
#include <QBrush>
#include <QPen>
#include <QImage>
#include <QPixmap>
#include <QWheelEvent>
#include <QMouseEvent>
#include <QNetworkRequest>
#include <QPainter>
#include <QtMath>
#include<queue>
MapCanvas2D::MapCanvas2D(QWidget* parent)
    : QGraphicsView(parent)
{
    scene = new QGraphicsScene(this);
    setScene(scene);
    setRenderHint(QPainter::Antialiasing);
    setRenderHint(QPainter::SmoothPixmapTransform);
    setDragMode(QGraphicsView::ScrollHandDrag);
    setHorizontalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    setVerticalScrollBarPolicy(Qt::ScrollBarAlwaysOff);
    setBackgroundBrush(QColor(25, 25, 25));
    setTransformationAnchor(QGraphicsView::AnchorUnderMouse);

    network = new QNetworkAccessManager(this);
    connect(network, &QNetworkAccessManager::finished,
            this,    &MapCanvas2D::onTileReady);
}

/* ========== TILE MATH ========== */

int MapCanvas2D::lonToTileX(double lon, int zoom)
{
    return int(floor((lon + 180.0) / 360.0 * pow(2.0, zoom)));
}

int MapCanvas2D::latToTileY(double lat, int zoom)
{
    double latRad = qDegreesToRadians(lat);
    return int(floor(
        (1.0 - log(tan(latRad) + 1.0/cos(latRad)) / M_PI)
        / 2.0 * pow(2.0, zoom)));
}


void MapCanvas2D::fetchSatelliteTiles(
    double minLat, double maxLat,
    double minLon, double maxLon,
    int zoom)
{
    fetchedTiles.clear();
    pendingTiles.clear();
    hasSatellite = false;
    currentZoom  = zoom;

    tileMinX = lonToTileX(minLon, zoom);
    tileMaxX = lonToTileX(maxLon, zoom);
    tileMinY = latToTileY(maxLat, zoom);
    tileMaxY = latToTileY(minLat, zoom);

    int total = (tileMaxX - tileMinX + 1) *
                (tileMaxY - tileMinY + 1);

    qDebug() << "2D fetching" << total << "tiles at zoom" << zoom;

    if (total > 256) {
        fetchSatelliteTiles(minLat, maxLat,
                            minLon, maxLon, zoom - 1);
        return;
    }

    for (int y = tileMinY; y <= tileMaxY; y++) {
        for (int x = tileMinX; x <= tileMaxX; x++) {
            QPair<int,int> key(x, y);
            pendingTiles.insert(key);

            QString url = QString(
                              "https://server.arcgisonline.com/ArcGIS/"
                              "rest/services/World_Imagery/MapServer/"
                              "tile/%1/%2/%3")
                              .arg(zoom).arg(y).arg(x);

            QNetworkRequest req(url);
            req.setHeader(QNetworkRequest::UserAgentHeader,
                          "Flood3D/1.0");
            req.setAttribute(QNetworkRequest::User,
                             QVariant::fromValue(key));
            network->get(req);
        }
    }
}


void MapCanvas2D::onTileReady(QNetworkReply* reply)
{
    if (reply->error() != QNetworkReply::NoError) {
        QPair<int,int> key = reply->request()
        .attribute(QNetworkRequest::User)
            .value<QPair<int,int>>();
        pendingTiles.remove(key);
        reply->deleteLater();
        if (pendingTiles.isEmpty() && !fetchedTiles.isEmpty())
            tryStitch();
        return;
    }

    QPair<int,int> key = reply->request()
                              .attribute(QNetworkRequest::User)
                              .value<QPair<int,int>>();

    QByteArray data = reply->readAll();
    reply->deleteLater();

    QImage img;
    if (!img.loadFromData(data)) {
        pendingTiles.remove(key);
        if (pendingTiles.isEmpty())
            tryStitch();
        return;
    }

    fetchedTiles[key] = img;
    pendingTiles.remove(key);

    if (pendingTiles.isEmpty())
        tryStitch();
}

/* ========== STITCH ========== */

void MapCanvas2D::tryStitch()
{
    int tileCols = tileMaxX - tileMinX + 1;
    int tileRows = tileMaxY - tileMinY + 1;

    int imgW = tileCols * 256;
    int imgH = tileRows * 256;

    QImage stitched(imgW, imgH, QImage::Format_RGB888);
    stitched.fill(Qt::black);

    QPainter painter(&stitched);
    for (int y = tileMinY; y <= tileMaxY; y++) {
        for (int x = tileMinX; x <= tileMaxX; x++) {
            QPair<int,int> key(x, y);
            if (!fetchedTiles.contains(key)) continue;
            int px = (x - tileMinX) * 256;
            int py = (y - tileMinY) * 256;
            painter.drawImage(px, py, fetchedTiles[key]);
        }
    }
    painter.end();

    satelliteImage = stitched;
    hasSatellite   = true;

    qDebug() << "2D stitched:" << imgW << "x" << imgH;
    renderDEM();
}

/* ========== SET DEM ========== */

void MapCanvas2D::setDEM(
    const std::vector<std::vector<float>>& dem)
{
    demGrid = dem;
    renderDEM();
}

/* ========== RENDER ========== */

void MapCanvas2D::renderDEM()
{
    scene->clear();
    if (demGrid.empty()) return;

    int demRows = demGrid.size();
    int demCols = demGrid[0].size();

    // ── SATELLITE MODE — full resolution ──
    if (hasSatellite) {
        int satW = satelliteImage.width();
        int satH = satelliteImage.height();

        QPixmap satPix = QPixmap::fromImage(satelliteImage);
        scene->addPixmap(satPix);

        // Flood overlay at satellite resolution
        if (showFlood && !floodGrid.empty()) {
            float maxD = 0;
            for (auto& r : floodGrid)
                for (float d : r)
                    maxD = std::max(maxD, d);

            if (maxD > 0) {
                QImage overlay(satW, satH,
                               QImage::Format_ARGB32);
                overlay.fill(Qt::transparent);

                QPainter p(&overlay);
                p.setRenderHint(QPainter::Antialiasing);

                float cellW = float(satW) / demCols;
                float cellH = float(satH) / demRows;

                for (int i = 0; i < demRows; i++) {
                    for (int j = 0; j < demCols; j++) {
                        float d = floodGrid[i][j];
                        if (d <= 0) continue;
                        float norm = d / maxD;

                        QColor water;
                        if (norm < 0.3)
                            water = QColor(30,144,255,120);
                        else if (norm < 0.6)
                            water = QColor(255,165,0,140);
                        else
                            water = QColor(255,0,0,160);

                        p.fillRect(
                            QRectF(j*cellW, i*cellH,
                                   cellW+1, cellH+1),
                            water);
                    }
                }
                p.end();

                scene->addPixmap(
                    QPixmap::fromImage(overlay));
            }
        }

        scene->setSceneRect(satPix.rect());
        fitInView(scene->sceneRect(),
                  Qt::KeepAspectRatioByExpanding);
        if (showTWI && !twiGrid.empty()) {
            QImage twiOverlay(satW, satH,
                              QImage::Format_ARGB32);
            twiOverlay.fill(Qt::transparent);
            QPainter tp(&twiOverlay);
            drawTWIZones(tp, satW, satH);
            tp.end();
            scene->addPixmap(
                QPixmap::fromImage(twiOverlay));
        }

        if (showContours) {
            QImage contourOverlay(satW, satH,
                                  QImage::Format_ARGB32);
            contourOverlay.fill(Qt::transparent);
            QPainter cp(&contourOverlay);
            cp.setRenderHint(QPainter::Antialiasing);
            drawContourLines(cp, satW, satH);
            cp.end();
            scene->addPixmap(
                QPixmap::fromImage(contourOverlay));
        }
        if (showWatershed) {
            QImage wsOverlay(satW, satH,
                             QImage::Format_ARGB32);
            wsOverlay.fill(Qt::transparent);
            QPainter wp(&wsOverlay);
            wp.setRenderHint(QPainter::Antialiasing);
            drawWatershed(wp, satW, satH);
            wp.end();
            scene->addPixmap(
                QPixmap::fromImage(wsOverlay));
        }
        return;
    }

    // ── FALLBACK: procedural colors ──
    float minE = 1e9, maxE = -1e9;
    for (auto& r : demGrid)
        for (float v : r) {
            minE = std::min(minE, v);
            maxE = std::max(maxE, v);
        }
    if (maxE - minE < 0.0001f) maxE = minE + 1.0f;

    QImage img(demCols, demRows, QImage::Format_ARGB32);
    for (int i = 0; i < demRows; i++) {
        for (int j = 0; j < demCols; j++) {
            float norm =
                (demGrid[i][j] - minE) / (maxE - minE);
            QColor color;
            if (norm < 0.4)      color = QColor(120,85,60);
            else if (norm < 0.7) color = QColor(90,60,40);
            else                 color = QColor(30,30,30);
            img.setPixelColor(j, i, color);
        }
    }

    // Flood on procedural
    if (showFlood && !floodGrid.empty()) {
        float maxD = 0;
        for (auto& r : floodGrid)
            for (float d : r)
                maxD = std::max(maxD, d);

        if (maxD > 0) {
            for (int i = 0; i < demRows; i++) {
                for (int j = 0; j < demCols; j++) {
                    float d = floodGrid[i][j];
                    if (d <= 0) continue;
                    float norm = d / maxD;

                    QColor water;
                    if (norm < 0.3)
                        water = QColor(30,144,255,150);
                    else if (norm < 0.6)
                        water = QColor(255,165,0,170);
                    else
                        water = QColor(255,0,0,200);

                    int alpha = water.alpha();
                    QColor base = img.pixelColor(j, i);
                    int r = (base.red()  *(255-alpha)+
                             water.red()  *alpha)/255;
                    int g = (base.green()*(255-alpha)+
                             water.green()*alpha)/255;
                    int b = (base.blue() *(255-alpha)+
                             water.blue() *alpha)/255;
                    img.setPixelColor(j, i, QColor(r,g,b));
                }
            }
        }
    }

    QPixmap pix = QPixmap::fromImage(img);
    scene->addPixmap(pix);
    scene->setSceneRect(pix.rect());
    fitInView(scene->sceneRect(),
              Qt::KeepAspectRatioByExpanding);
}

/* ========== REST ========== */

void MapCanvas2D::wheelEvent(QWheelEvent* event)
{
    const double scaleFactor = 1.15;
    if (event->angleDelta().y() > 0)
        scale(scaleFactor, scaleFactor);
    else
        scale(1.0 / scaleFactor, 1.0 / scaleFactor);
}

void MapCanvas2D::setFlood(
    const std::vector<std::vector<float>>& flood)
{
    floodGrid = flood;
    showFlood = true;

    if (!hasSatellite || demGrid.empty()) {
        renderDEM();
        return;
    }

    // Fast path — just update flood overlay without full re-render
    int demRows = demGrid.size();
    int demCols = demGrid[0].size();
    int satW = satelliteImage.width();
    int satH = satelliteImage.height();

    float maxD = 0;
    for (auto& r : floodGrid)
        for (float d : r)
            maxD = std::max(maxD, d);

    QImage overlay(satW, satH, QImage::Format_ARGB32);
    overlay.fill(Qt::transparent);

    if (maxD > 0) {
        QPainter p(&overlay);
        float cellW = float(satW) / demCols;
        float cellH = float(satH) / demRows;
        for (int i = 0; i < demRows; i++) {
            for (int j = 0; j < demCols; j++) {
                float d = floodGrid[i][j];
                if (d <= 0) continue;
                float norm = d / maxD;
                QColor water;
                if (norm < 0.3)
                    water = QColor(30,144,255,120);
                else if (norm < 0.6)
                    water = QColor(255,165,0,140);
                else
                    water = QColor(255,0,0,160);
                p.fillRect(QRectF(j*cellW, i*cellH,
                                  cellW+1, cellH+1), water);
            }
        }
        p.end();
    }

    if (!floodOverlayItem) {
        floodOverlayItem = scene->addPixmap(
            QPixmap::fromImage(overlay));
        floodOverlayItem->setZValue(1);
    } else {
        floodOverlayItem->setPixmap(
            QPixmap::fromImage(overlay));
    }

    viewport()->update();
}

void MapCanvas2D::clearDEM()
{
    demGrid.clear();
    hasDEM = false;
    scene->clear();
}

void MapCanvas2D::clearFlood()
{
    floodGrid.clear();
    showFlood = false;
    renderDEM();
}

void MapCanvas2D::resizeEvent(QResizeEvent* event)
{
    QGraphicsView::resizeEvent(event);
    if (!scene->sceneRect().isEmpty())
        fitInView(scene->sceneRect(),
                  Qt::KeepAspectRatioByExpanding);
}

bool MapCanvas2D::saveRiskMap(const QString& path)
{
    if (!scene) return false;
    QRectF rect = scene->sceneRect();
    QImage image(rect.size().toSize(),
                 QImage::Format_ARGB32);
    image.fill(Qt::transparent);
    QPainter painter(&image);
    scene->render(&painter);
    painter.end();
    return image.save(path);
}

void MapCanvas2D::mousePressEvent(QMouseEvent* event)
{
    if (demGrid.empty()) return;

    QPointF scenePos = mapToScene(event->pos());

    // Map scene coords to DEM grid
    // Scene is satellite size, DEM is smaller
    int demRows = demGrid.size();
    int demCols = demGrid[0].size();

    int col, row;

    if (hasSatellite) {
        int satW = satelliteImage.width();
        int satH = satelliteImage.height();
        col = int(scenePos.x() * demCols / satW);
        row = int(scenePos.y() * demRows / satH);
    } else {
        col = scenePos.x();
        row = scenePos.y();
    }

    if (row >= 0 && row < demRows &&
        col >= 0 && col < demCols)
        emit cellClicked(row, col);

    QGraphicsView::mousePressEvent(event);
}
void MapCanvas2D::setContourLines(bool enabled)
{
    showContours = enabled;
    renderDEM();
}
void MapCanvas2D::drawContourLines(
    QPainter& painter, int satW, int satH)
{
    if (demGrid.empty()) return;

    int demRows = demGrid.size();
    int demCols = demGrid[0].size();

    // Find elevation range
    float minE = 1e9, maxE = -1e9;
    for (auto& r : demGrid)
        for (float v : r) {
            minE = std::min(minE, v);
            maxE = std::max(maxE, v);
        }

    float range = maxE - minE;
    if (range < 1.0f) return;

    // Choose contour interval based on range
    float minorInterval, majorInterval;
    if (range < 50.0f) {
        minorInterval = 2.0f;
        majorInterval = 10.0f;
    } else if (range < 200.0f) {
        minorInterval = 10.0f;
        majorInterval = 50.0f;
    } else if (range < 500.0f) {
        minorInterval = 20.0f;
        majorInterval = 100.0f;
    } else {
        minorInterval = 50.0f;
        majorInterval = 250.0f;
    }

    float cellW = float(satW) / demCols;
    float cellH = float(satH) / demRows;

    // Draw contours by marching through grid
    for (float elev = minE; elev <= maxE;
         elev += minorInterval)
    {
        bool isMajor = (fmod(elev - minE,
                             majorInterval) < minorInterval);

        if (isMajor) {
            painter.setPen(QPen(
                QColor(255, 220, 100, 180), 1.5));
        } else {
            painter.setPen(QPen(
                QColor(200, 180, 80, 100), 0.8));
        }

        // March squares algorithm (simplified)
        for (int i = 0; i < demRows-1; i++) {
            for (int j = 0; j < demCols-1; j++) {

                float h00 = demGrid[i][j];
                float h10 = demGrid[i][j+1];
                float h01 = demGrid[i+1][j];
                float h11 = demGrid[i+1][j+1];

                // Check if contour passes through cell
                bool above00 = h00 >= elev;
                bool above10 = h10 >= elev;
                bool above01 = h01 >= elev;
                bool above11 = h11 >= elev;

                int code = (above00 ? 8 : 0) |
                           (above10 ? 4 : 0) |
                           (above11 ? 2 : 0) |
                           (above01 ? 1 : 0);

                if (code == 0 || code == 15) continue;

                // Pixel coords of cell corners
                float x0 = j     * cellW;
                float x1 = (j+1) * cellW;
                float y0 = i     * cellH;
                float y1 = (i+1) * cellH;

                // Interpolate crossing points
                auto interp = [](float a, float b,
                                 float e) {
                    if (abs(b-a) < 0.001f) return 0.5f;
                    return (e-a)/(b-a);
                };

                // Edge midpoints
                float tTop   = interp(h00,h10,elev);
                float tBot   = interp(h01,h11,elev);
                float tLeft  = interp(h00,h01,elev);
                float tRight = interp(h10,h11,elev);

                QPointF top  (x0+tTop  *(x1-x0), y0);
                QPointF bot  (x0+tBot  *(x1-x0), y1);
                QPointF left (x0,       y0+tLeft *(y1-y0));
                QPointF right(x1,       y0+tRight*(y1-y0));

                switch(code) {
                case 1: case 14:
                    painter.drawLine(left, bot); break;
                case 2: case 13:
                    painter.drawLine(bot, right); break;
                case 3: case 12:
                    painter.drawLine(left, right); break;
                case 4: case 11:
                    painter.drawLine(top, right); break;
                case 5:
                    painter.drawLine(top, left);
                    painter.drawLine(bot, right); break;
                case 6: case 9:
                    painter.drawLine(top, bot); break;
                case 7: case 8:
                    painter.drawLine(top, left); break;
                case 10:
                    painter.drawLine(top, right);
                    painter.drawLine(left, bot); break;
                }
            }
        }
    }

    painter.setFont(QFont("Arial", 7));
    for (float elev = minE; elev <= maxE;
         elev += majorInterval)
    {
        for (int i = 0; i < demRows-1;
             i += demRows/8)
        {
            for (int j = 0; j < demCols-1; j++) {
                float h0 = demGrid[i][j];
                float h1 = demGrid[i][j+1];

                if ((h0 < elev && h1 >= elev) ||
                    (h0 >= elev && h1 < elev))
                {
                    float t = (elev-h0)/(h1-h0);
                    float px = (j+t) * cellW;
                    float py = i     * cellH;

                    painter.setPen(
                        QColor(255, 230, 120, 200));
                    painter.drawText(
                        QPointF(px+2, py-2),
                        QString::number(
                            int(elev)) + "m");
                    break;
                }
            }
        }
    }
}
void MapCanvas2D::computeWatershed()
{
    if (demGrid.empty()) return;


    float minE = 1e9, maxE = -1e9;
    for (auto& r : demGrid)
        for (float v : r) {
            minE = std::min(minE, v);
            maxE = std::max(maxE, v);
        }

    if (maxE - minE < 50.0f) {
        qDebug() << "Terrain too flat for watershed";
        return;
    }
    int rows = demGrid.size();
    int cols = demGrid[0].size();

    // Flow direction for each cell
    // 0=N 1=NE 2=E 3=SE 4=S 5=SW 6=W 7=NW
    int dx[] = {0,1,1,1,0,-1,-1,-1};
    int dz[] = {-1,-1,0,1,1,1,0,-1};

    std::vector<std::vector<int>> flowDir(
        rows, std::vector<int>(cols, -1));

    // Calculate flow direction for each cell
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            float minH = demGrid[i][j];
            int   minD = -1;

            for (int d = 0; d < 8; d++) {
                int ni = i + dz[d];
                int nj = j + dx[d];

                if (ni < 0 || ni >= rows ||
                    nj < 0 || nj >= cols)
                    continue;

                if (demGrid[ni][nj] < minH) {
                    minH = demGrid[ni][nj];
                    minD = d;
                }
            }
            flowDir[i][j] = minD;
        }
    }

    // Label watersheds using flood fill
    watershedGrid.assign(rows,
                         std::vector<int>(cols, -1));

    int watershedID = 0;

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (watershedGrid[i][j] != -1) continue;
            if (flowDir[i][j] != -1) continue;

            // This is a pour point (local minimum)
            // Flood fill backwards
            std::queue<std::pair<int,int>> q;
            q.push({i, j});
            watershedGrid[i][j] = watershedID;

            while (!q.empty()) {
                auto [ci, cj] = q.front();
                q.pop();

                for (int d = 0; d < 8; d++) {
                    int ni = ci + dz[d];
                    int nj = cj + dx[d];

                    if (ni < 0 || ni >= rows ||
                        nj < 0 || nj >= cols)
                        continue;

                    if (watershedGrid[ni][nj] != -1)
                        continue;

                    // Does this neighbor flow to us?
                    int nd = flowDir[ni][nj];
                    if (nd == -1) continue;

                    int fi = ni + dz[nd];
                    int fj = nj + dx[nd];

                    if (fi == ci && fj == cj) {
                        watershedGrid[ni][nj] =
                            watershedID;
                        q.push({ni, nj});
                    }
                }
            }
            watershedID++;
        }
    }

    qDebug() << "Watersheds found:" << watershedID;
    showWatershed = false;
    renderDEM();
}

void MapCanvas2D::setWatershedVisible(bool v)
{
    showWatershed = v;
    renderDEM();
}

void MapCanvas2D::drawWatershed(
    QPainter& painter, int satW, int satH)
{
    if (watershedGrid.empty()) return;

    int rows = watershedGrid.size();
    int cols = watershedGrid[0].size();

    float cellW = float(satW) / cols;
    float cellH = float(satH) / rows;

    // Unique colors per watershed
    QList<QColor> colors = {
        QColor(255, 100, 100, 80),  // red
        QColor(100, 255, 100, 80),  // green
        QColor(100, 100, 255, 80),  // blue
        QColor(255, 255, 100, 80),  // yellow
        QColor(255, 100, 255, 80),  // magenta
        QColor(100, 255, 255, 80),  // cyan
        QColor(255, 180, 100, 80),  // orange
        QColor(180, 100, 255, 80),  // purple
    };

    // Fill watershed regions
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            int id = watershedGrid[i][j];
            if (id < 0) continue;

            QColor c = colors[id % colors.size()];
            painter.fillRect(
                QRectF(j*cellW, i*cellH,
                       cellW+1, cellH+1), c);
        }
    }

    // Draw boundary lines
    painter.setPen(QPen(QColor(255,255,255,160), 1.0));

    for (int i = 0; i < rows-1; i++) {
        for (int j = 0; j < cols-1; j++) {
            int id = watershedGrid[i][j];

            // Right neighbor
            if (watershedGrid[i][j+1] != id) {
                painter.drawLine(
                    QPointF((j+1)*cellW, i*cellH),
                    QPointF((j+1)*cellW, (i+1)*cellH));
            }
            // Bottom neighbor
            if (watershedGrid[i+1][j] != id) {
                painter.drawLine(
                    QPointF(j*cellW,     (i+1)*cellH),
                    QPointF((j+1)*cellW, (i+1)*cellH));
            }
        }
    }
}
void MapCanvas2D::setTWI(
    const std::vector<std::vector<float>>& twi)
{
    twiGrid = twi;
    showTWI = true;
    renderDEM();
}

void MapCanvas2D::clearTWI()
{
    twiGrid.clear();
    showTWI = false;

}

void MapCanvas2D::setTWIVisible(bool enabled)
{
    showTWI = enabled;
    renderDEM();
}

void MapCanvas2D::drawTWIZones(
    QPainter& painter, int satW, int satH)
{
    if (twiGrid.empty()) return;

    int rows = twiGrid.size();
    int cols = twiGrid[0].size();
    float minT = 1e9, maxT = -1e9;
    for (auto& r : twiGrid)
        for (float v : r) {
            minT = std::min(minT, v);
            maxT = std::max(maxT, v);
        }

    qDebug() << "TWI range:" << minT << "to" << maxT
             << "| grid:" << rows << "x" << cols;
    float cellW = float(satW) / cols;
    float cellH = float(satH) / rows;

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            float twi = twiGrid[i][j];

            QColor zone;
            if (twi > 12.0f)
                zone = QColor(220, 20, 20, 130);   // high risk
            else if (twi > 9.0f)
                zone = QColor(255, 165, 0, 110);   // medium risk
            else if (twi > 6.0f)
                zone = QColor(255, 255, 0, 80);    // low risk
            else
                continue;                           // safe, skip

            painter.fillRect(
                QRectF(j*cellW, i*cellH,
                       cellW+1, cellH+1),
                zone);
        }
    }
}
