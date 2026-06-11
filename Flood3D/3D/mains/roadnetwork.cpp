#include "roadnetwork.h"
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QNetworkRequest>
#include <QDebug>
#include<QFile>
#include <cmath>
#include <algorithm>

RoadNetwork::RoadNetwork(QObject* parent) : QObject(parent)
{
    network = new QNetworkAccessManager(this);
    connect(network, &QNetworkAccessManager::finished,
            this,    &RoadNetwork::onReply);
}

RoadNetwork::~RoadNetwork()
{
    vbo.destroy();
    vao.destroy();
    delete program;
}

void RoadNetwork::init()
{
    initializeOpenGLFunctions();

    const char* vert = R"(
#version 330 core
layout(location=0) in vec3 pos;
layout(location=1) in vec3 color;
out vec3 vColor;
uniform mat4 projection;
uniform mat4 view;
void main() {
    vColor = color;
    gl_Position = projection * view * vec4(pos, 1.0);
}
)";

    const char* frag = R"(
#version 330 core
in vec3 vColor;
out vec4 FragColor;
void main() {
    FragColor = vec4(vColor, 1.0);
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

void RoadNetwork::fetchRoads(double minLat, double maxLat,
                             double minLon, double maxLon)
{
    storedMinLat = minLat; storedMaxLat = maxLat;
    storedMinLon = minLon; storedMaxLon = maxLon;


    QFile cache("roads_cache.json");
    if (cache.open(QIODevice::ReadOnly)) {
        qDebug() << "Loading roads from cache...";
        QByteArray data = cache.readAll();
        cache.close();
        parseRoads(data);
        emit roadsReady();
        return;
    }


    // Overpass API query — fetch roads in bbox
    QString query = QString(
                        "[out:json][timeout:25];"
                        "way[\"highway\"](%1,%2,%3,%4);"
                        "(._;>;);"
                        "out body;")
                        .arg(minLat).arg(minLon)
                        .arg(maxLat).arg(maxLon);

    QString url = "https://overpass-api.de/api/interpreter";

    QUrl qurl(url);
    QNetworkRequest req(qurl);
    req.setHeader(QNetworkRequest::ContentTypeHeader,
                  "application/x-www-form-urlencoded");
    QByteArray postData = "data=" + QUrl::toPercentEncoding(query);
    network->post(req, postData);
    qDebug() << "Fetching roads from Overpass API...";
}

void RoadNetwork::onReply(QNetworkReply* reply)
{
    if (reply->error() != QNetworkReply::NoError) {
        qDebug() << "Road fetch failed:" << reply->errorString();
        reply->deleteLater();
        return;
    }
    QByteArray data = reply->readAll();
    reply->deleteLater();

    QFile cache("roads_cache.json");
    if (cache.open(QIODevice::WriteOnly))
        cache.write(data);
    cache.close();

    parseRoads(data);
    emit roadsReady();
}


void RoadNetwork::buildGeometry(
    const std::vector<std::vector<float>>& dem,
    double minLat, double maxLat,
    double minLon, double maxLon  , float demMinH, float demMaxH)
{
    if (roads.empty() || dem.empty()) return;

    int demRows = dem.size();
    int demCols = dem[0].size();

    float minH = 1e9, maxH = -1e9;
    for (auto& r : dem) for (float v : r) {
            minH = std::min(minH, v);
            maxH = std::max(maxH, v);
        }
    float hRange = maxH - minH;
    if (hRange < 1.0f) hRange = 1.0f;

    float heightScale;
    if      (hRange < 20.0f)  heightScale = 1.5f;
    else if (hRange < 50.0f)  heightScale = 1.2f;
    else if (hRange < 200.0f) heightScale = 0.8f;
    else if (hRange < 500.0f) heightScale = 0.4f;
    else                      heightScale = 0.2f;

    float horizontalScale = 100.0f / std::max(demRows, demCols);

    struct Vert { QVector3D pos; QVector3D color; };
    std::vector<Vert> verts;

    for (const auto& road : roads) {
        // Road color by type
        QVector3D color;
        switch (road.type) {
        case 2: color = QVector3D(1.0f, 0.9f, 0.2f); break; // highway yellow
        case 1: color = QVector3D(1.0f, 1.0f, 1.0f); break; // major white
        default:color = QVector3D(0.7f, 0.7f, 0.7f); break; // minor gray
        }

        for (int k = 0; k + 1 < (int)road.points.size(); k++) {

            auto toWorld = [&](QVector3D p) -> QVector3D {
                double lat = p.x();
                double lon = p.y();

                float col = (lon - minLon) / (maxLon - minLon) * (demCols - 1);
                float row = (1.0f - (lat - minLat) / (maxLat - minLat)) * (demRows - 1);

                // Clamp
                col = std::max(0.0f, std::min((float)(demCols-1), col));
                row = std::max(0.0f, std::min((float)(demRows-1), row));

                int gi = (int)row;
                int gj = (int)col;
                gi = std::max(0, std::min(demRows-1, gi));
                gj = std::max(0, std::min(demCols-1, gj));

                // Bilinear interpolation
                float fr = row - gi;
                float fc = col - gj;
                int gi2 = std::min(gi+1, demRows-1);
                int gj2 = std::min(gj+1, demCols-1);
                float h00 = dem[gi][gj];
                float h10 = dem[gi][gj2];
                float h01 = dem[gi2][gj];
                float h11 = dem[gi2][gj2];
                float rawH = h00*(1-fr)*(1-fc) + h10*(1-fr)*fc
                             + h01*fr*(1-fc)    + h11*fr*fc;
                float h = (rawH - minH) * heightScale;






                float wx = (col - demCols/2.0f) * horizontalScale;
                float wz = (demRows/2.0f - row) * horizontalScale;

                return QVector3D(wx, h + 0.5f, wz);
            };

            QVector3D a = toWorld(road.points[k]);
            QVector3D b = toWorld(road.points[k+1]);


            if (k == 0 && &road == &roads[0]) {
                qDebug() << "First road point A:" << a;
                qDebug() << "First road point B:" << b;
                qDebug() << "demRows:" << demRows << "demCols:" << demCols;
                qDebug() << "horizontalScale:" << horizontalScale;
                qDebug() << "minLat:" << minLat << "maxLat:" << maxLat;
                qDebug() << "minLon:" << minLon << "maxLon:" << maxLon;
            }
            verts.push_back({a, color});
            verts.push_back({b, color});
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
                                offsetof(Vert, pos), 3, sizeof(Vert));
    program->enableAttributeArray(1);
    program->setAttributeBuffer(1, GL_FLOAT,
                                offsetof(Vert, color), 3, sizeof(Vert));
    program->release();

    vbo.release();
    vao.release();

    qDebug() << "Road geometry built:" << vertexCount / 2
             << "segments";
}

void RoadNetwork::draw(const QMatrix4x4& proj,
                       const QMatrix4x4& view)
{
    if (vertexCount == 0 || !program) return;

    glDisable(GL_DEPTH_TEST);
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

    program->bind();
    program->setUniformValue("projection", proj);
    program->setUniformValue("view",       view);

    vao.bind();
    glDrawArrays(GL_LINES, 0, vertexCount);
    vao.release();

    program->release();

    glEnable(GL_DEPTH_TEST);
    glDisable(GL_BLEND);
}


void RoadNetwork::parseRoads(const QByteArray& data)
{
    QJsonDocument doc = QJsonDocument::fromJson(data);
    QJsonArray elements = doc.object()["elements"].toArray();

    QMap<qint64, QPair<double,double>> nodes;
    for (auto e : elements) {
        QJsonObject obj = e.toObject();
        if (obj["type"].toString() == "node") {
            qint64 id = obj["id"].toVariant().toLongLong();
            nodes[id] = {obj["lat"].toDouble(),
                         obj["lon"].toDouble()};
        }
    }

    roads.clear();
    for (auto e : elements) {
        QJsonObject obj = e.toObject();
        if (obj["type"].toString() != "way") continue;
        QString hw = obj["tags"].toObject()["highway"].toString();
        if (hw.isEmpty()) continue;

        int type = 0;
        if (hw == "motorway" || hw == "trunk" || hw == "primary")
            type = 2;
        else if (hw == "secondary" || hw == "tertiary")
            type = 1;

        Road road;
        road.type = type;
        for (auto nid : obj["nodes"].toArray()) {
            qint64 id = nid.toVariant().toLongLong();
            if (nodes.contains(id))
                road.points.push_back(
                    QVector3D(nodes[id].first,
                              nodes[id].second, 0));
        }
        if (road.points.size() >= 2)
            roads.push_back(road);
    }
    qDebug() << "Roads parsed:" << roads.size();
}


