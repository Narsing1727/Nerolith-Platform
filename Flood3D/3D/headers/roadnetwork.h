#pragma once
#include <QOpenGLFunctions>
#include <QOpenGLBuffer>
#include <QOpenGLVertexArrayObject>
#include <QOpenGLShaderProgram>
#include <QVector3D>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <vector>
#include <QObject>

struct Road {
    std::vector<QVector3D> points;
    int type; // 0=minor 1=major 2=highway
};

class RoadNetwork : public QObject, protected QOpenGLFunctions
{
    Q_OBJECT
public:
    explicit RoadNetwork(QObject* parent = nullptr);
    ~RoadNetwork();

    void init();
    void fetchRoads(double minLat, double maxLat,
                    double minLon, double maxLon);
    void buildGeometry(
        const std::vector<std::vector<float>>& dem,
        double minLat, double maxLat,
        double minLon, double maxLon ,  float demMinH, float demMaxH);
    void draw(const QMatrix4x4& proj,
              const QMatrix4x4& view);
    bool hasRoads() const { return vertexCount > 0; }

signals:
    void roadsReady();

private slots:
    void onReply(QNetworkReply* reply);

private:
    QNetworkAccessManager* network = nullptr;
    QOpenGLShaderProgram*  program = nullptr;
    QOpenGLVertexArrayObject vao;
    QOpenGLBuffer            vbo;
    int vertexCount = 0;

    std::vector<Road> roads;

    // stored for buildGeometry after fetch
    double storedMinLat, storedMaxLat;
    double storedMinLon, storedMaxLon;

    void parseRoads(const QByteArray& data);
};
