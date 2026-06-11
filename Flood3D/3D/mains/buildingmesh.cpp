#include "buildingmesh.h"
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QNetworkRequest>
#include <QFile>
#include <QDebug>
#include <cmath>
#include <algorithm>

BuildingMesh::BuildingMesh(QObject* parent) : QObject(parent)
{
    network = new QNetworkAccessManager(this);
    connect(network, &QNetworkAccessManager::finished,
            this,    &BuildingMesh::onReply);
}

BuildingMesh::~BuildingMesh()
{
    vbo.destroy();
    vao.destroy();
    delete program;
}

void BuildingMesh::init()
{
    initializeOpenGLFunctions();

    const char* vert = R"(
#version 330 core
layout(location=0) in vec3 pos;
layout(location=1) in vec3 color;
layout(location=2) in vec3 normal;
out vec3 vColor;
out vec3 vNormal;
uniform mat4 projection;
uniform mat4 view;
uniform vec3 lightDir;
void main() {
    vColor  = color;
    vNormal = normal;
    gl_Position = projection * view * vec4(pos, 1.0);
}
)";

    const char* frag = R"(
#version 330 core
in vec3 vColor;
in vec3 vNormal;
out vec4 FragColor;
uniform vec3 lightDir;
void main() {
    float diff = max(dot(normalize(vNormal),
                         normalize(lightDir)), 0.2);
    FragColor = vec4(vColor * diff, 0.85);
}
)";

    program = new QOpenGLShaderProgram();
    program->addShaderFromSourceCode(QOpenGLShader::Vertex,   vert);
    program->addShaderFromSourceCode(QOpenGLShader::Fragment, frag);
    program->link();

    vao.create();
    vbo.create();
    vbo.setUsagePattern(QOpenGLBuffer::DynamicDraw);
}

void BuildingMesh::fetchBuildings(double minLat, double maxLat,
                                  double minLon, double maxLon)
{
    storedMinLat = minLat; storedMaxLat = maxLat;
    storedMinLon = minLon; storedMaxLon = maxLon;

    // Load from cache if available
    QFile cache("buildings_cache.json");
    if (cache.open(QIODevice::ReadOnly)) {
        qDebug() << "Loading buildings from cache...";
        QByteArray data = cache.readAll();
        cache.close();
        parseBuildings(data);
        emit buildingsReady();
        return;
    }

    QString query = QString(
                        "[out:json][timeout:25];"
                        "way[\"building\"](%1,%2,%3,%4);"
                        "(._;>;);"
                        "out body;")
                        .arg(minLat).arg(minLon)
                        .arg(maxLat).arg(maxLon);

    QUrl qurl("https://overpass-api.de/api/interpreter");
    QNetworkRequest req(qurl);
    req.setHeader(QNetworkRequest::ContentTypeHeader,
                  "application/x-www-form-urlencoded");

    QByteArray postData = "data=" + QUrl::toPercentEncoding(query);
    network->post(req, postData);
    qDebug() << "Fetching buildings from Overpass API...";
}

void BuildingMesh::onReply(QNetworkReply* reply)
{
    if (reply->error() != QNetworkReply::NoError) {
        qDebug() << "Building fetch failed:" << reply->errorString();
        reply->deleteLater();
        return;
    }

    QByteArray data = reply->readAll();
    reply->deleteLater();

    QFile cache("buildings_cache.json");
    if (cache.open(QIODevice::WriteOnly))
        cache.write(data);
    cache.close();

    parseBuildings(data);
    emit buildingsReady();
}

void BuildingMesh::parseBuildings(const QByteArray& data)
{
    QJsonDocument doc = QJsonDocument::fromJson(data);
    QJsonArray elements = doc.object()["elements"].toArray();

    // Collect nodes
    QMap<qint64, QPair<double,double>> nodes;
    for (auto e : elements) {
        QJsonObject obj = e.toObject();
        if (obj["type"].toString() == "node") {
            qint64 id = obj["id"].toVariant().toLongLong();
            nodes[id] = {obj["lat"].toDouble(),
                         obj["lon"].toDouble()};
        }
    }

    buildings.clear();
    for (auto e : elements) {
        QJsonObject obj = e.toObject();
        if (obj["type"].toString() != "way") continue;

        QJsonObject tags = obj["tags"].toObject();
        if (!tags.contains("building")) continue;

        Building b;

        // Height from tags or default
        if (tags.contains("height"))
            b.height = tags["height"].toString().toFloat();
        else if (tags.contains("building:levels"))
            b.height = tags["building:levels"].toString().toFloat() * 3.0f;
        else
            b.height = 6.0f; // default 2 floors

        b.height = std::max(3.0f, std::min(b.height, 50.0f));

        for (auto nid : obj["nodes"].toArray()) {
            qint64 id = nid.toVariant().toLongLong();
            if (nodes.contains(id))
                b.footprint.push_back(
                    QVector3D(nodes[id].first,
                              nodes[id].second, 0));
        }

        if (b.footprint.size() >= 3)
            buildings.push_back(b);
    }

    qDebug() << "Buildings parsed:" << buildings.size();
}

void BuildingMesh::buildGeometry(
    const std::vector<std::vector<float>>& dem,
    double minLat, double maxLat,
    double minLon, double maxLon)
{
    if (buildings.empty() || dem.empty()) return;

    int demRows = dem.size();
    int demCols = dem[0].size();

    float minH = 1e9, maxH = -1e9;
    for (auto& r : dem) for (float v : r) {
            minH = std::min(minH, v);
            maxH = std::max(maxH, v);
        }
    float hRange = maxH - minH;
    if (hRange < 0.001f) hRange = 1.0f;

    float heightScale;
    if      (hRange < 20.0f)  heightScale = 1.5f;
    else if (hRange < 50.0f)  heightScale = 1.2f;
    else if (hRange < 200.0f) heightScale = 0.8f;
    else if (hRange < 500.0f) heightScale = 0.4f;
    else                      heightScale = 0.2f;

    float horizontalScale = 100.0f / std::max(demRows, demCols);

    // Building height in world units
    // 1 metre real = heightScale world units
    float buildingScale = heightScale * 0.5f;

    auto toWorld = [&](double lat, double lon,
                       float extraY = 0.0f) -> QVector3D {
        float col = (lon - minLon) / (maxLon - minLon) * (demCols-1);
        float row = (1.0f - (lat - minLat) /
                                (maxLat - minLat)) * (demRows-1);

        col = std::max(0.0f, std::min((float)(demCols-1), col));
        row = std::max(0.0f, std::min((float)(demRows-1), row));

        int gi = std::max(0, std::min(demRows-1, (int)row));
        int gj = std::max(0, std::min(demCols-1, (int)col));

        // Bilinear interpolation
        float fr = row - gi;
        float fc = col - gj;
        int gi2 = std::min(gi+1, demRows-1);
        int gj2 = std::min(gj+1, demCols-1);
        float rawH = dem[gi][gj]   * (1-fr)*(1-fc)
                     + dem[gi][gj2]  * (1-fr)*fc
                     + dem[gi2][gj]  * fr*(1-fc)
                     + dem[gi2][gj2] * fr*fc;

        float h = (rawH - minH) * heightScale;

        float wx = (col - demCols/2.0f) * horizontalScale;
        float wz = (demRows/2.0f - row) * horizontalScale;

        return QVector3D(wx, h + 0.5f + extraY, wz);
    };

    struct Vert {
        QVector3D pos;
        QVector3D color;
        QVector3D normal;
    };

    std::vector<Vert> verts;

    QVector3D roofColor (0.85f, 0.82f, 0.78f);
    QVector3D wallColor (0.75f, 0.72f, 0.68f);
    QVector3D darkWall  (0.60f, 0.58f, 0.54f);

    for (const auto& b : buildings) {
        int n = b.footprint.size();
        if (n < 3) continue;

        float bh = b.height * buildingScale;

        // Build wall quads for each edge
        for (int i = 0; i < n - 1; i++) {
            double lat0 = b.footprint[i].x();
            double lon0 = b.footprint[i].y();
            double lat1 = b.footprint[i+1].x();
            double lon1 = b.footprint[i+1].y();

            QVector3D bl = toWorld(lat0, lon0, 0);
            QVector3D br = toWorld(lat1, lon1, 0);
            QVector3D tl = toWorld(lat0, lon0, bh);
            QVector3D tr = toWorld(lat1, lon1, bh);

            // Wall normal
            QVector3D edge = br - bl;
            QVector3D up   = QVector3D(0, 1, 0);
            QVector3D norm = QVector3D::crossProduct(edge, up).normalized();

            // Shade side walls differently
            QVector3D wc = (i % 2 == 0) ? wallColor : darkWall;

            // Two triangles per wall face
            verts.push_back({bl, wc, norm});
            verts.push_back({br, wc, norm});
            verts.push_back({tl, wc, norm});

            verts.push_back({br, wc, norm});
            verts.push_back({tr, wc, norm});
            verts.push_back({tl, wc, norm});
        }

        // Roof — simple fan triangulation from centroid
        QVector3D centroid(0,0,0);
        for (int i = 0; i < n-1; i++) {
            centroid += toWorld(b.footprint[i].x(),
                                b.footprint[i].y(), bh);
        }
        centroid /= (n-1);

        QVector3D roofNorm(0, 1, 0);
        for (int i = 0; i < n-1; i++) {
            QVector3D a = toWorld(b.footprint[i].x(),
                                  b.footprint[i].y(), bh);
            QVector3D c = toWorld(b.footprint[(i+1)%(n-1)].x(),
                                  b.footprint[(i+1)%(n-1)].y(), bh);
            verts.push_back({centroid, roofColor, roofNorm});
            verts.push_back({a,        roofColor, roofNorm});
            verts.push_back({c,        roofColor, roofNorm});
        }
    }

    vertexCount = verts.size();
    if (vertexCount == 0) return;

    vao.bind();
    vbo.bind();
    vbo.allocate(verts.data(), vertexCount * sizeof(Vert));

    program->bind();
    program->enableAttributeArray(0);
    program->setAttributeBuffer(0, GL_FLOAT,
                                offsetof(Vert, pos),    3, sizeof(Vert));
    program->enableAttributeArray(1);
    program->setAttributeBuffer(1, GL_FLOAT,
                                offsetof(Vert, color),  3, sizeof(Vert));
    program->enableAttributeArray(2);
    program->setAttributeBuffer(2, GL_FLOAT,
                                offsetof(Vert, normal), 3, sizeof(Vert));
    program->release();

    vbo.release();
    vao.release();

    qDebug() << "Building geometry built:"
             << buildings.size() << "buildings,"
             << vertexCount << "vertices";
}

void BuildingMesh::draw(const QMatrix4x4& proj,
                        const QMatrix4x4& view)
{
    if (vertexCount == 0 || !program) return;

    glEnable(GL_DEPTH_TEST);
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

    program->bind();
    program->setUniformValue("projection", proj);
    program->setUniformValue("view",       view);
    program->setUniformValue("lightDir",
                             QVector3D(0.5f, 0.8f, 0.3f));

    vao.bind();
    glDrawArrays(GL_TRIANGLES, 0, vertexCount);
    vao.release();

    program->release();
    glDisable(GL_BLEND);
}
