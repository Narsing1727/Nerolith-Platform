#pragma once
#include <QVector3D>
#include <QOpenGLBuffer>
#include <QOpenGLVertexArrayObject>
#include <QOpenGLFunctions>
#include <vector>
#include <QOpenGLShaderProgram>
#include<QOpenGLTexture>
class TerrainMesh : protected QOpenGLFunctions
{
public:
    struct Vertex {
        QVector3D pos;
        QVector3D normal;
          QVector2D uv;
    };

    TerrainMesh();
    ~TerrainMesh();
     std::vector<std::vector<float>> demGrid;
    void init();  // Call after OpenGL context ready
    void build(const std::vector<std::vector<float>>& dem);
    void draw();

    int demRows = 0;
    int demCols = 0;
    float heightScale = 1.5f;
    float minHeight = 0.0f;
    float maxHeight = 0.0f;
    int vertexCount = 0;
     void setupAttributes(QOpenGLShaderProgram* program);
    void setFlood(const std::vector<std::vector<float>>& flood);
    void bindFloodTexture(int unit = 1);
    void releaseFloodTexture();
    bool hasFlood() const { return floodTexture != nullptr; }

private:
    void smoothDEM(int iterations);
    QVector3D calculateNormal(int x, int z);
    void generateMesh();
 QOpenGLTexture* floodTexture = nullptr;

    void generateSkirts(std::vector<Vertex>& vertices,
                        float horizontalScale,
                        float heightScale);
    QOpenGLBuffer vbo{QOpenGLBuffer::VertexBuffer};
    QOpenGLVertexArrayObject vao;
};
