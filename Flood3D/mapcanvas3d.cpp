#include "mapcanvas3d.h"
#include <QOpenGLShaderProgram>
#include"roadnetwork.h"
#include <QMatrix4x4>
#include <QDebug>
#include <QMouseEvent>
#include <QKeyEvent>
#include <QTimer>
#include <QElapsedTimer>
MapCanvas3D::MapCanvas3D(QWidget* parent)
    : QOpenGLWidget(parent)
{
    setMinimumSize(400, 400);

    satellite = new SatelliteTexture(this);

    connect(satellite, &SatelliteTexture::tileReady,
            this,      QOverload<>::of(&QOpenGLWidget::update));
}

MapCanvas3D::~MapCanvas3D()
{
    makeCurrent();
    delete program;
    delete skyProgram;
    doneCurrent();
}

void MapCanvas3D::initializeGL()
{
    initializeOpenGLFunctions();
    glEnable(GL_DEPTH_TEST);
    glDepthFunc(GL_LESS);
    glDisable(GL_CULL_FACE);

    program = new QOpenGLShaderProgram(this);

    if (!program->addShaderFromSourceFile(QOpenGLShader::Vertex, ":/shaders/vertex.vert")) {
        qCritical() << "Vertex shader error:" << program->log();
    }
    if (!program->addShaderFromSourceFile(QOpenGLShader::Fragment, ":/shaders/fragment.frag")) {
        qCritical() << "Fragment shader error:" << program->log();
    }
    if (!program->link()) {
        qCritical() << "Link error:" << program->log();
    }
    // program->addShaderFromSourceFile(QOpenGLShader::Vertex,   ":/shaders/vertex.vert");
    // program->addShaderFromSourceFile(QOpenGLShader::Fragment, ":/shaders/fragment.vert");
    // program->link();

    // Init terrain — must be after OpenGL context ready
    terrain.init();
    // Sky gradient shader
    skyProgram = new QOpenGLShaderProgram(this);

    skyProgram->addShaderFromSourceCode(
        QOpenGLShader::Vertex, R"(
#version 330 core
layout(location=0) in vec2 pos;
out vec2 uv;
void main() {
    uv = pos * 0.5 + 0.5;
    gl_Position = vec4(pos, 0.999, 1.0);
}
)");

    skyProgram->addShaderFromSourceCode(
        QOpenGLShader::Fragment, R"(
#version 330 core
in vec2 uv;
out vec4 FragColor;
void main()
{
    // Top = deep blue, Bottom = horizon haze
    vec3 top    = vec3(0.05, 0.08, 0.15);
    vec3 horizon= vec3(0.18, 0.22, 0.30);
    vec3 col = mix(horizon, top, uv.y);
    FragColor = vec4(col, 1.0);
}
)");
    skyProgram->link();
    // Setup VAO attributes
    // Init terrain — must be after OpenGL context ready
    qDebug() << "GL Version:" << (char*)glGetString(GL_VERSION);

    float range[2] = {0, 0};
    glGetFloatv(GL_POINT_SIZE_RANGE, range);
    qDebug() << "Max point size:" << range[1];
    terrain.setupAttributes(program);
    riskMarkers.init();
    aiRiskMarkers.init();
    waterLayer.init();

    roadNetwork = new RoadNetwork(this);
    roadNetwork->init();


    buildingMesh = new BuildingMesh(this);
    buildingMesh->init();
    connect(buildingMesh, &BuildingMesh::buildingsReady,
            this, [this]() {
                makeCurrent();
                buildingMesh->buildGeometry(
                    terrain.demGrid,
                    geoMinLat, geoMaxLat,
                    geoMinLon, geoMaxLon);
                doneCurrent();
                update();
            });



    connect(roadNetwork, &RoadNetwork::roadsReady,
            this, [this]() {
                makeCurrent();
                roadNetwork->buildGeometry(
                    terrain.demGrid,
                    geoMinLat, geoMaxLat,
                    geoMinLon, geoMaxLon , terrain.minHeight , terrain.maxHeight);
                doneCurrent();
                update();
            });
    timer.start();
}

void MapCanvas3D::setDEM(const std::vector<std::vector<float>>& dem)
{
      makeCurrent();
    terrain.build(dem);
          doneCurrent();
    update();
}

void MapCanvas3D::resizeGL(int w, int h)
{
    glViewport(0, 0, w, h);
}
void MapCanvas3D::paintGL()
{
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    drawSkyGradient();
    if (terrain.vertexCount == 0 || !program) return;

    program->bind();

    QMatrix4x4 proj;
    proj.perspective(45.0f, float(width())/float(height()),
                     0.1f, 10000.0f);
    QMatrix4x4 model;
    model.setToIdentity();

    program->setUniformValue("projection", proj);
    program->setUniformValue("view",       camera.viewMatrix());
    program->setUniformValue("model",      model);
    program->setUniformValue("lightDir",
                             QVector3D(0.5f, 0.8f, 0.3f).normalized());
    program->setUniformValue("minHeight",  terrain.minHeight);
    program->setUniformValue("maxHeight",  terrain.maxHeight);

    // Satellite
    if (satellite->isReady()) {
        satellite->bind(0);
        program->setUniformValue("satelliteTexture", 0);
        program->setUniformValue("hasSatellite", true);
    } else {
        program->setUniformValue("hasSatellite", false);
    }

  program->setUniformValue("hasFlood", false);
    terrain.draw();
    program->release();

    if (showWater && waterLayer.hasWater()) {
        float t = timer.elapsed() / 1000.0f;
        waterLayer.draw(proj, camera.viewMatrix(), t);
    }
    if (satellite->isReady()) satellite->release();
    // if (terrain.hasFlood())   terrain.releaseFloodTexture();

    program->release();

    // Draw markers ON TOP
    float t = timer.elapsed() / 1000.0f;
    riskMarkers.draw(proj, camera.viewMatrix(), t);
    if (!aiCurrentMarkers.empty())
        aiRiskMarkers.draw(proj, camera.viewMatrix(), t);


    if (showRoads && roadNetwork && roadNetwork->hasRoads())
        roadNetwork->draw(proj, camera.viewMatrix());



    if (showBuildings && buildingMesh && buildingMesh->hasBuildings())
        buildingMesh->draw(proj, camera.viewMatrix());


    // Animate
    QTimer::singleShot(16, this,
                       QOverload<>::of(&QOpenGLWidget::update));
}
/* === Input — delegate to camera === */
void MapCanvas3D::mousePressEvent(QMouseEvent* e)
{
    camera.mousePressEvent(e);

    if (e->button() == Qt::LeftButton) {
        bool hit = false;
        QMatrix4x4 proj;
        proj.perspective(45.0f, float(width())/float(height()), 0.1f, 10000.0f);
        QMatrix4x4 mvp = proj * camera.viewMatrix();

        for (const auto& m : currentMarkers) {
            QVector4D clip = mvp * QVector4D(m.worldPos, 1.0f);
            if (clip.w() <= 0) continue;
            float sx = (clip.x()/clip.w() * 0.5f + 0.5f) * width();
            float sy = (1.0f-(clip.y()/clip.w()*0.5f+0.5f))*height();
            float dx = sx - e->pos().x();
            float dy = sy - e->pos().y();
            if (sqrt(dx*dx + dy*dy) < 25.0f) {
                activePopup.screenPos = QPoint(sx, sy);
                activePopup.row       = m.row;
                activePopup.col       = m.col;
                activePopup.depth     = m.depth;
                activePopup.riskLevel = m.riskLevel;
                activePopup.visible   = true;
                hit = true;
                emit markerClicked(m.row, m.col, m.depth, m.riskLevel);
                break;
            }
        }

        if (!hit) {
            for (const auto& m : aiCurrentMarkers) {
                QVector4D clip = mvp * QVector4D(m.worldPos, 1.0f);
                if (clip.w() <= 0) continue;
                float sx = (clip.x()/clip.w() * 0.5f + 0.5f) * width();
                float sy = (1.0f-(clip.y()/clip.w()*0.5f+0.5f))*height();
                float dx = sx - e->pos().x();
                float dy = sy - e->pos().y();
                qDebug() << "AI marker screen:" << sx << sy
                         << "click:" << e->pos().x() << e->pos().y()
                         << "dist:" << sqrt(dx*dx+dy*dy);
                if (sqrt(dx*dx + dy*dy) < 25.0f) {
                    qDebug() << "AI MARKER HIT — emitting regionId:" << m.regionId;
                    activePopup.visible = false;
                    hit = true;
                    emit aiMarkerClicked(m.regionId);
                    break;
                }
                if (sqrt(dx*dx + dy*dy) < 25.0f) {
                    activePopup.visible = false;
                    hit = true;
                    emit aiMarkerClicked(m.regionId);
                    break;
                }
            }
        }

        if (!hit) activePopup.visible = false;
        update();
    }

    if (e->button() == Qt::RightButton) {
        activePopup.visible = false;
        update();
    }
}
void MapCanvas3D::mouseMoveEvent(QMouseEvent* e)
{
    camera.mouseMoveEvent(e, [this]{ update(); });
}

void MapCanvas3D::wheelEvent(QWheelEvent* e)
{
    camera.wheelEvent(e, [this]{ update(); });
}

void MapCanvas3D::keyPressEvent(QKeyEvent* e)
{
    camera.keyPressEvent(e, [this]{ update(); });
}
void MapCanvas3D::loadSatelliteTile(double lat, double lon, int zoom)
{
    satellite->fetchTile(lat, lon, zoom);
}
void MapCanvas3D::loadSatelliteTiles(double minLat, double maxLat,
                                     double minLon, double maxLon,
                                     int zoom)
{
    satellite->fetchTiles(minLat, maxLat, minLon, maxLon, zoom);
}




void MapCanvas3D::setFlood(
    const std::vector<std::vector<float>>& flood)
{
    makeCurrent();
    terrain.setFlood(flood);

    waterLayer.setFlood(
        flood,
        terrain.demGrid,
        terrain.minHeight,
        terrain.heightScale,
        100.0f / std::max(terrain.demRows, terrain.demCols)
        );

    doneCurrent();
    update();
}











void MapCanvas3D::drawSkyGradient()
{
    static float verts[] = {
        -1,-1,  1,-1,  1,1,
        -1,-1,  1, 1, -1,1
    };

    glDisable(GL_DEPTH_TEST);
    skyProgram->bind();

    GLuint vbo;
    glGenBuffers(1, &vbo);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, sizeof(verts),
                 verts, GL_STREAM_DRAW);

    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 2, GL_FLOAT,
                          GL_FALSE, 0, nullptr);

    glDrawArrays(GL_TRIANGLES, 0, 6);

    glDisableVertexAttribArray(0);
    glBindBuffer(GL_ARRAY_BUFFER, 0);
    glDeleteBuffers(1, &vbo);

    skyProgram->release();
    glEnable(GL_DEPTH_TEST);
}
void MapCanvas3D::paintEvent(QPaintEvent* e)
{
    QOpenGLWidget::paintEvent(e);

    if (!activePopup.visible) return;

    QPainter painter(this);
    painter.setRenderHint(QPainter::Antialiasing);

    // Popup dimensions
    int pw = 200;
    int ph = 110;
    int px = activePopup.screenPos.x() - pw/2;
    int py = activePopup.screenPos.y() - ph - 30;

    // Keep popup inside widget
    px = qBound(5, px, width()  - pw - 5);
    py = qBound(5, py, height() - ph - 5);

    // Risk color
    QColor riskColor;
    QString riskText;
    switch (activePopup.riskLevel) {
    case 2:
        riskColor = QColor(220, 50,  50);
        riskText  = "HIGH RISK";
        break;
    case 1:
        riskColor = QColor(255, 160, 0);
        riskText  = "MEDIUM RISK";
        break;
    default:
        riskColor = QColor(50,  200, 50);
        riskText  = "LOW RISK";
        break;
    }


    painter.setBrush(QColor(0, 0, 0, 60));
    painter.setPen(Qt::NoPen);
    painter.drawRoundedRect(px+4, py+4, pw, ph, 10, 10);


    QLinearGradient bg(px, py, px, py+ph);
    bg.setColorAt(0, QColor(25, 30, 40, 230));
    bg.setColorAt(1, QColor(15, 18, 25, 230));
    painter.setBrush(bg);
    painter.setPen(QPen(riskColor, 1.5));
    painter.drawRoundedRect(px, py, pw, ph, 10, 10);


    painter.setBrush(riskColor);
    painter.setPen(Qt::NoPen);
    painter.drawRoundedRect(px, py, pw, 28, 10, 10);
    painter.drawRect(px, py+14, pw, 14);


    painter.setPen(Qt::white);
    painter.setFont(QFont("Arial", 9, QFont::Bold));
    painter.drawText(px+10, py+19, riskText);


    painter.setFont(QFont("Arial", 8));
    painter.setPen(QColor(200,200,200));
    painter.drawText(px+pw-20, py+19, "✕");


    painter.setFont(QFont("Arial", 8));
    painter.setPen(QColor(180, 190, 200));
    painter.drawText(px+10, py+45, "Row:");
    painter.drawText(px+10, py+62, "Col:");
    painter.drawText(px+10, py+79, "Flood Depth:");
    painter.drawText(px+10, py+96, "Cell:");

    painter.setPen(Qt::white);
    painter.setFont(QFont("Arial", 8, QFont::Bold));
    painter.drawText(px+90, py+45,
                     QString::number(activePopup.row));
    painter.drawText(px+90, py+62,
                     QString::number(activePopup.col));
    painter.drawText(px+90, py+79,
                     QString::number(activePopup.depth, 'f', 2) + " m");
    painter.drawText(px+90, py+96,
                     QString("(%1, %2)")
                         .arg(activePopup.row)
                         .arg(activePopup.col));

    QPolygon arrow;
    int ax = activePopup.screenPos.x();
    int ay = py + ph;
    arrow << QPoint(ax-8, ay)
          << QPoint(ax+8, ay)
          << QPoint(ax,   ay+12);
    painter.setBrush(QColor(15, 18, 25, 230));
    painter.setPen(QPen(riskColor, 1.5));
    painter.drawPolygon(arrow);

    painter.end();
}
void MapCanvas3D::fetchRoads(double minLat, double maxLat,
                             double minLon, double maxLon)
{
    geoMinLat = minLat; geoMaxLat = maxLat;
    geoMinLon = minLon; geoMaxLon = maxLon;
    if (roadNetwork)
        roadNetwork->fetchRoads(minLat, maxLat, minLon, maxLon);
}

void MapCanvas3D::setRoadsVisible(bool v)
{
    showRoads = v;
    update();
}


void MapCanvas3D::fetchBuildings(double minLat, double maxLat,
                                 double minLon, double maxLon)
{
    if (buildingMesh)
        buildingMesh->fetchBuildings(minLat, maxLat,
                                     minLon, maxLon);
}

void MapCanvas3D::setBuildingsVisible(bool v)
{
    showBuildings = v;
    update();
}



void MapCanvas3D::setSWEFrame(
    const std::vector<std::vector<float>>& frame)
{
    makeCurrent();
    terrain.setFlood(frame);

    waterLayer.setFlood(
        frame,
        terrain.demGrid,
        terrain.minHeight,
        terrain.heightScale,
        100.0f / std::max(terrain.demRows, terrain.demCols)
        );

    doneCurrent();
    update();
}



void MapCanvas3D::setAIRiskMarkers(const std::vector<RiskMarker>& markers)
{
    makeCurrent();
    aiRiskMarkers.setMarkers(markers);
    aiCurrentMarkers = markers;
    doneCurrent();
    update();
}
