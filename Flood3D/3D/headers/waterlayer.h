#pragma once
#include <QOpenGLFunctions>
#include <QOpenGLBuffer>
#include <QOpenGLVertexArrayObject>
#include <QOpenGLShaderProgram>
#include <QOpenGLTexture>
#include <QMatrix4x4>
#include <vector>

class WaterLayer : protected QOpenGLFunctions
{
public:
    WaterLayer();
    ~WaterLayer();

    void init();

    // Call after simulation — builds water mesh from flood grid
    void setFlood(
        const std::vector<std::vector<float>>& flood,
        const std::vector<std::vector<float>>& dem,
        float demMinHeight,
        float heightScale,
        float horizontalScale
        );

    void draw(
        const QMatrix4x4& proj,
        const QMatrix4x4& view,
        float time               // seconds — for wave animation
        );

    bool hasWater() const { return vertexCount > 0; }
    void clear();

private:
    QOpenGLVertexArrayObject vao;
    QOpenGLBuffer            vbo;
    QOpenGLShaderProgram*    program = nullptr;
    int                      vertexCount = 0;

    void buildShader();
};
