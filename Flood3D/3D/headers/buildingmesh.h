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

struct Building {
    std::vector<QVector3D> footprint; // lat/lon points
    float height = 6.0f;             // metres, default 2 floors
};

class BuildingMesh : public QObject, protected QOpenGLFunctions
{
    Q_OBJECT
public:
    explicit BuildingMesh(QObject* parent = nullptr);
    ~BuildingMesh();

    void init();
    void fetchBuildings(double minLat, double maxLat,
                        double minLon, double maxLon);
    void buildGeometry(
        const std::vector<std::vector<float>>& dem,
        double minLat, double maxLat,
        double minLon, double maxLon);
    void draw(const QMatrix4x4& proj,
              const QMatrix4x4& view);
    bool hasBuildings() const { return vertexCount > 0; }

signals:
    void buildingsReady();

private slots:
    void onReply(QNetworkReply* reply);

private:
    QNetworkAccessManager* network  = nullptr;
    QOpenGLShaderProgram*  program  = nullptr;
    QOpenGLVertexArrayObject vao;
    QOpenGLBuffer            vbo;
    int vertexCount = 0;

    std::vector<Building> buildings;

    double storedMinLat, storedMaxLat;
    double storedMinLon, storedMaxLon;

    void parseBuildings(const QByteArray& data);
};
