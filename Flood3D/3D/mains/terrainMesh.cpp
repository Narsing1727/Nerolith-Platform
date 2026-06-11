#include "terrainMesh.h"
#include <QDebug>
#include <QtMath>
#include <algorithm>
#include <cmath>
#include <QOpenGLShaderProgram>
#include <QOpenGLTexture>
TerrainMesh::TerrainMesh() {}

TerrainMesh::~TerrainMesh()
{
    vbo.destroy();
    vao.destroy();
}

void TerrainMesh::init()
{
    initializeOpenGLFunctions();

    vao.create();
    vao.bind();

    vbo.create();
    vbo.bind();
    vbo.setUsagePattern(QOpenGLBuffer::StaticDraw);

    vbo.release();
    vao.release();
}

void TerrainMesh::build(const std::vector<std::vector<float>>& dem)
{
    if (dem.empty() || dem[0].empty()) {
        qWarning() << "Empty DEM";
        return;
    }

    demGrid = dem;
    demRows = demGrid.size();
    demCols = demGrid[0].size();

    minHeight = 1e9f;
    maxHeight = -1e9f;

    for (const auto& row : demGrid)
        for (float h : row)
            if (std::isfinite(h)) {
                minHeight = std::min(minHeight, h);
                maxHeight = std::max(maxHeight, h);
            }

    for (auto& row : demGrid)
        for (float& h : row)
            if (!std::isfinite(h)) h = minHeight;

    qDebug() << "DEM loaded:" << demCols << "x" << demRows;
    qDebug() << "Height range:" << minHeight << "-" << maxHeight;

    smoothDEM(15);
    generateMesh();
}

void TerrainMesh::draw()
{
    if (vertexCount == 0) return;
    vao.bind();
    glDrawArrays(GL_TRIANGLES, 0, vertexCount);
    vao.release();
}

void TerrainMesh::smoothDEM(int iterations)
{
    for (int iter = 0; iter < iterations; ++iter) {
        std::vector<std::vector<float>> smoothed = demGrid;
        for (int z = 1; z < demRows - 1; ++z)
            for (int x = 1; x < demCols - 1; ++x)
                smoothed[z][x] = (
                                     demGrid[z][x] +
                                     demGrid[z-1][x] + demGrid[z+1][x] +
                                     demGrid[z][x-1] + demGrid[z][x+1]
                                     ) / 5.0f;
        demGrid = smoothed;
    }
}

QVector3D TerrainMesh::calculateNormal(int x, int z)
{
    float heightL = (x > 0)          ? demGrid[z][x-1] : demGrid[z][x];
    float heightR = (x < demCols-1)  ? demGrid[z][x+1] : demGrid[z][x];
    float heightD = (z > 0)          ? demGrid[z-1][x] : demGrid[z][x];
    float heightU = (z < demRows-1)  ? demGrid[z+1][x] : demGrid[z][x];

    QVector3D normal(heightL - heightR, 2.0f, heightD - heightU);
    return normal.normalized();
}

void TerrainMesh::generateMesh()
{
    std::vector<Vertex> vertices;
    vertices.reserve((demRows-1) * (demCols-1) * 6);

    float heightRange = maxHeight - minHeight;
    if (heightRange < 0.001f) heightRange = 1.0f;
    float heightScale;
    if (heightRange < 20.0f) {
        heightScale = 1.5f;   // was 0.3
    } else if (heightRange < 50.0f) {
        heightScale = 1.2f;   // was 0.5
    } else if (heightRange < 200.0f) {
        heightScale = 0.8f;   // was 0.8
    } else if (heightRange < 500.0f) {
        heightScale = 0.4f;
    } else {
        heightScale = 0.2f;
    }
    this->heightScale = heightScale;
    float horizontalScale = 100.0f / std::max(demRows, demCols);
    float minY = 1e9f, maxY = -1e9f;

    for (int z = 0; z < demRows-1; ++z) {
        for (int x = 0; x < demCols-1; ++x) {
            float h00 = (demGrid[z][x]   - minHeight) * heightScale;
            float h10 = (demGrid[z][x+1] - minHeight) * heightScale;
            float h01 = (demGrid[z+1][x] - minHeight) * heightScale;
            float h11 = (demGrid[z+1][x+1] - minHeight) * heightScale;

            minY = std::min({minY, h00, h10, h01, h11});
            maxY = std::max({maxY, h00, h10, h01, h11});

            float fx0 = (x   - demCols/2.0f) * horizontalScale;
            float fx1 = (x+1 - demCols/2.0f) * horizontalScale;
            float fz0 = (z   - demRows/2.0f) * horizontalScale;
            float fz1 = (z+1 - demRows/2.0f) * horizontalScale;

            QVector3D p00(fx0, h00, fz0);
            QVector3D p10(fx1, h10, fz0);
            QVector3D p01(fx0, h01, fz1);
            QVector3D p11(fx1, h11, fz1);

            QVector3D n00 = calculateNormal(x,   z);
            QVector3D n10 = calculateNormal(x+1, z);
            QVector3D n01 = calculateNormal(x,   z+1);
            QVector3D n11 = calculateNormal(x+1, z+1);

            QVector2D uv00(float(x)   / demCols, float(z)   / demRows);
            QVector2D uv10(float(x+1) / demCols, float(z)   / demRows);
            QVector2D uv01(float(x)   / demCols, float(z+1) / demRows);
            QVector2D uv11(float(x+1) / demCols, float(z+1) / demRows);

            vertices.push_back({p00, n00, uv00});
            vertices.push_back({p10, n10, uv10});
            vertices.push_back({p01, n01, uv01});

            vertices.push_back({p10, n10, uv10});
            vertices.push_back({p11, n11, uv11});
            vertices.push_back({p01, n01, uv01});
        }
    }
generateSkirts(vertices, horizontalScale, heightScale);
    vertexCount = vertices.size();
    minHeight = minY;
    maxHeight = maxY;

    qDebug() << "Mesh generated:" << vertexCount << "vertices";

    vao.bind();
    vbo.bind();
    vbo.allocate(vertices.data(), vertexCount * sizeof(Vertex));
    vbo.release();
    vao.release();
}
void TerrainMesh::setupAttributes(QOpenGLShaderProgram* program)
{
    vao.bind();
    vbo.bind();
    program->bind();

    program->enableAttributeArray(0);
    program->setAttributeBuffer(0, GL_FLOAT, offsetof(Vertex, pos), 3, sizeof(Vertex));

    program->enableAttributeArray(1);
    program->setAttributeBuffer(1, GL_FLOAT, offsetof(Vertex, normal), 3, sizeof(Vertex));

    program->enableAttributeArray(2);
    program->setAttributeBuffer(2, GL_FLOAT, offsetof(Vertex, uv), 2, sizeof(Vertex));

    program->release();
    vbo.release();
    vao.release();
}
void TerrainMesh::generateSkirts(std::vector<Vertex>& vertices,
                                 float horizontalScale,
                                 float heightScale)
{
    float skirtBottom = -10.0f; // How deep the walls go

    QVector3D skirtNormal;

    skirtNormal = QVector3D(0, 0, -1);
    for (int x = 0; x < demCols - 1; ++x) {
        float h0 = (demGrid[0][x]   - minHeight) * heightScale;
        float h1 = (demGrid[0][x+1] - minHeight) * heightScale;

        float fx0 = (x   - demCols/2.0f) * horizontalScale;
        float fx1 = (x+1 - demCols/2.0f) * horizontalScale;
        float fz  = (0   - demRows/2.0f) * horizontalScale;

        QVector2D uv0(float(x)   / demCols, 0.0f);
        QVector2D uv1(float(x+1) / demCols, 0.0f);

        QVector3D tl(fx0, h0,          fz);
        QVector3D tr(fx1, h1,          fz);
        QVector3D bl(fx0, skirtBottom, fz);
        QVector3D br(fx1, skirtBottom, fz);

        vertices.push_back({tl, skirtNormal, uv0});
        vertices.push_back({tr, skirtNormal, uv1});
        vertices.push_back({bl, skirtNormal, uv0});

        vertices.push_back({tr, skirtNormal, uv1});
        vertices.push_back({br, skirtNormal, uv1});
        vertices.push_back({bl, skirtNormal, uv0});
    }

    skirtNormal = QVector3D(0, 0, 1);
    for (int x = 0; x < demCols - 1; ++x) {
        int z = demRows - 1;
        float h0 = (demGrid[z][x]   - minHeight) * heightScale;
        float h1 = (demGrid[z][x+1] - minHeight) * heightScale;

        float fx0 = (x   - demCols/2.0f) * horizontalScale;
        float fx1 = (x+1 - demCols/2.0f) * horizontalScale;
        float fz  = (z   - demRows/2.0f) * horizontalScale;

        QVector2D uv0(float(x)   / demCols, 1.0f);
        QVector2D uv1(float(x+1) / demCols, 1.0f);

        QVector3D tl(fx0, h0,          fz);
        QVector3D tr(fx1, h1,          fz);
        QVector3D bl(fx0, skirtBottom, fz);
        QVector3D br(fx1, skirtBottom, fz);

        vertices.push_back({tr, skirtNormal, uv1});
        vertices.push_back({tl, skirtNormal, uv0});
        vertices.push_back({bl, skirtNormal, uv0});

        vertices.push_back({tr, skirtNormal, uv1});
        vertices.push_back({bl, skirtNormal, uv0});
        vertices.push_back({br, skirtNormal, uv1});
    }

    // ── LEFT edge (x = 0) ──
    skirtNormal = QVector3D(-1, 0, 0);
    for (int z = 0; z < demRows - 1; ++z) {
        float h0 = (demGrid[z][0]   - minHeight) * heightScale;
        float h1 = (demGrid[z+1][0] - minHeight) * heightScale;

        float fx  = (0   - demCols/2.0f) * horizontalScale;
        float fz0 = (z   - demRows/2.0f) * horizontalScale;
        float fz1 = (z+1 - demRows/2.0f) * horizontalScale;

        QVector2D uv0(0.0f, float(z)   / demRows);
        QVector2D uv1(0.0f, float(z+1) / demRows);

        QVector3D tl(fx, h0,          fz0);
        QVector3D tr(fx, h1,          fz1);
        QVector3D bl(fx, skirtBottom, fz0);
        QVector3D br(fx, skirtBottom, fz1);

        vertices.push_back({tr, skirtNormal, uv1});
        vertices.push_back({tl, skirtNormal, uv0});
        vertices.push_back({bl, skirtNormal, uv0});

        vertices.push_back({tr, skirtNormal, uv1});
        vertices.push_back({bl, skirtNormal, uv0});
        vertices.push_back({br, skirtNormal, uv1});
    }

    // ── RIGHT edge (x = demCols-1) ──
    skirtNormal = QVector3D(1, 0, 0);
    for (int z = 0; z < demRows - 1; ++z) {
        int x = demCols - 1;
        float h0 = (demGrid[z][x]   - minHeight) * heightScale;
        float h1 = (demGrid[z+1][x] - minHeight) * heightScale;

        float fx  = (x   - demCols/2.0f) * horizontalScale;
        float fz0 = (z   - demRows/2.0f) * horizontalScale;
        float fz1 = (z+1 - demRows/2.0f) * horizontalScale;

        QVector2D uv0(1.0f, float(z)   / demRows);
        QVector2D uv1(1.0f, float(z+1) / demRows);

        QVector3D tl(fx, h0,          fz0);
        QVector3D tr(fx, h1,          fz1);
        QVector3D bl(fx, skirtBottom, fz0);
        QVector3D br(fx, skirtBottom, fz1);

        vertices.push_back({tl, skirtNormal, uv0});
        vertices.push_back({tr, skirtNormal, uv1});
        vertices.push_back({bl, skirtNormal, uv0});

        vertices.push_back({tr, skirtNormal, uv1});
        vertices.push_back({br, skirtNormal, uv1});
        vertices.push_back({bl, skirtNormal, uv0});
    }

    // ── BOTTOM face ──
    skirtNormal = QVector3D(0, -1, 0);
    float fx0 = (0        - demCols/2.0f) * horizontalScale;
    float fx1 = (demCols  - demCols/2.0f) * horizontalScale;
    float fz0 = (0        - demRows/2.0f) * horizontalScale;
    float fz1 = (demRows  - demRows/2.0f) * horizontalScale;

    QVector3D bl(fx0, skirtBottom, fz0);
    QVector3D br(fx1, skirtBottom, fz0);
    QVector3D tl(fx0, skirtBottom, fz1);
    QVector3D tr(fx1, skirtBottom, fz1);

    vertices.push_back({bl, skirtNormal, QVector2D(0,0)});
    vertices.push_back({br, skirtNormal, QVector2D(1,0)});
    vertices.push_back({tl, skirtNormal, QVector2D(0,1)});

    vertices.push_back({br, skirtNormal, QVector2D(1,0)});
    vertices.push_back({tr, skirtNormal, QVector2D(1,1)});
    vertices.push_back({tl, skirtNormal, QVector2D(0,1)});
}

void TerrainMesh::setFlood(
    const std::vector<std::vector<float>>& flood)
{
    if (flood.empty() || flood[0].empty()) return;

    int rows = flood.size();
    int cols = flood[0].size();

    float maxFlood = 0.0f;
    for (const auto& row : flood)
        for (float v : row)
            maxFlood = std::max(maxFlood, v);

    if (maxFlood < 0.001f) {
        qDebug() << "No flood data";
        return;
    }

    QImage img(cols, rows, QImage::Format_RGBA8888);
    img.fill(Qt::transparent);

    for (int y = 0; y < rows; y++) {
        for (int x = 0; x < cols; x++) {
            float depth = flood[y][x];
            if (depth < 0.001f) {
                img.setPixel(x, y, qRgba(0,0,0,0));
            } else {
                float norm = depth / maxFlood;
                int r = int(norm * 255);

                img.setPixel(x, y, qRgba(r, 0, 0, 200));
            }
        }
    }

    delete floodTexture;
    floodTexture = new QOpenGLTexture(img.mirrored());
    floodTexture->setMinificationFilter(
        QOpenGLTexture::Linear);
    floodTexture->setMagnificationFilter(
        QOpenGLTexture::Linear);
    floodTexture->setWrapMode(
        QOpenGLTexture::ClampToEdge);

    qDebug() << "Heatmap texture uploaded:"
             << cols << "x" << rows
             << "maxFlood:" << maxFlood;
}

void TerrainMesh::bindFloodTexture(int unit)
{
    if (floodTexture)
        floodTexture->bind(unit);
}

void TerrainMesh::releaseFloodTexture()
{
    if (floodTexture)
        floodTexture->release();
}
