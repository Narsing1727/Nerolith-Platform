#pragma once
#include <QObject>
#include <QOpenGLFunctions>
#include <QOpenGLBuffer>
#include <QOpenGLVertexArrayObject>
#include <QOpenGLShaderProgram>
#include <QVector3D>
#include <QVector4D>
#include <QMatrix4x4>
#include <vector>

struct RiskMarker {
    QVector3D worldPos;
    QVector4D color;
    float     depth;
    int       row, col;
    int       riskLevel;
     QString   regionId;
};

class RiskMarkerRenderer : protected QOpenGLFunctions
{
public:
    RiskMarkerRenderer();
    ~RiskMarkerRenderer();

    void init();
    void setMarkers(const std::vector<RiskMarker>& markers);
    void draw(const QMatrix4x4& proj,
              const QMatrix4x4& view,
              float time);

private:
    void buildGeometry();

    std::vector<RiskMarker> markers;
    QOpenGLBuffer            vbo{QOpenGLBuffer::VertexBuffer};
    QOpenGLVertexArrayObject vao;
    QOpenGLShaderProgram*    program = nullptr;
    int                      vertexCount = 0;
};
