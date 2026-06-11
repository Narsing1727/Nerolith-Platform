#include "waterlayer.h"
#include <QDebug>
#include <cmath>

// ── WATER VERTEX SHADER ──────────────────────────────────────────────────────
static const char* WATER_VERT = R"(
#version 330 core
layout(location = 0) in vec3  position;   // world position
layout(location = 1) in float depth;      // flood depth (metres)

out float fragDepth;
out vec3  fragWorldPos;
out vec2  fragUV;

uniform mat4  projection;
uniform mat4  view;
uniform mat4  model;
uniform float time;

void main()
{
    fragDepth    = depth;
    fragWorldPos = position;
    fragUV       = position.xz * 0.08;   // tiling for wave normal

    // Gentle wave displacement — only on surface, scaled by depth
    float wave = sin(position.x * 1.8 + time * 1.4)
               * cos(position.z * 1.5 + time * 1.1)
               * 0.04 * min(depth, 1.0);

    vec3 displaced = position + vec3(0.0, wave, 0.0);

    gl_Position = projection * view * model * vec4(displaced, 1.0);
}
)";

// ── WATER FRAGMENT SHADER ─────────────────────────────────────────────────────
static const char* WATER_FRAG = R"(
#version 330 core

in float fragDepth;
in vec3  fragWorldPos;
in vec2  fragUV;

out vec4 FragColor;

uniform float time;
uniform vec3  lightDir;

void main()
{
    // Depth-based water color
    // 0-0.3m  → clear light blue
    // 0.3-1m  → medium blue
    // 1-2m    → deep blue
    // 2m+     → dark navy

    vec3 shallow = vec3(0.40, 0.75, 0.90);   // light blue
    vec3 medium  = vec3(0.15, 0.50, 0.80);   // blue
    vec3 deep    = vec3(0.05, 0.25, 0.60);   // deep blue
    vec3 vdeep   = vec3(0.02, 0.10, 0.35);   // dark navy

    vec3 waterColor;
    float d = fragDepth;

    if (d < 0.3)
        waterColor = mix(shallow, medium, d / 0.3);
    else if (d < 1.0)
        waterColor = mix(medium, deep, (d - 0.3) / 0.7);
    else if (d < 2.0)
        waterColor = mix(deep, vdeep, (d - 1.0) / 1.0);
    else
        waterColor = vdeep;

    // Wave normal (fake normal map from sine)
    float nx = sin(fragUV.x * 6.28 + time * 1.2) * 0.3;
    float nz = cos(fragUV.y * 6.28 + time * 0.9) * 0.3;
    vec3 waveNormal = normalize(vec3(nx, 1.0, nz));

    // Diffuse lighting on water surface
    vec3 L       = normalize(lightDir);
    float diffuse = max(dot(waveNormal, L), 0.0) * 0.4;

    // Specular reflection — water is shiny
    vec3  viewDir = normalize(-fragWorldPos);
    vec3  halfDir = normalize(L + viewDir);
    float spec    = pow(max(dot(waveNormal, halfDir), 0.0), 64.0) * 0.6;

    vec3 lit = waterColor * (0.6 + diffuse) + vec3(spec);

    // Fresnel — edges more transparent, center more opaque
    float fresnel  = pow(1.0 - max(dot(waveNormal, viewDir), 0.0), 2.0);
    float alpha    = 0.55 + fresnel * 0.25 + min(d * 0.15, 0.20);
    alpha          = clamp(alpha, 0.45, 0.85);

    // Shimmer
    float shimmer  = sin(fragWorldPos.x * 3.0 + time * 2.5)
                   * cos(fragWorldPos.z * 2.5 + time * 2.0) * 0.04;
    lit += vec3(shimmer);

    FragColor = vec4(lit, alpha);
}
)";


WaterLayer::WaterLayer() {}

WaterLayer::~WaterLayer()
{
    vbo.destroy();
    vao.destroy();
    delete program;
}

void WaterLayer::init()
{
    initializeOpenGLFunctions();
    buildShader();

    vao.create();
    vao.bind();

    vbo.create();
    vbo.bind();
    vbo.setUsagePattern(QOpenGLBuffer::DynamicDraw);

    vbo.release();
    vao.release();
}

void WaterLayer::buildShader()
{
    program = new QOpenGLShaderProgram();

    if (!program->addShaderFromSourceCode(
            QOpenGLShader::Vertex, WATER_VERT))
        qCritical() << "Water vert error:" << program->log();

    if (!program->addShaderFromSourceCode(
            QOpenGLShader::Fragment, WATER_FRAG))
        qCritical() << "Water frag error:" << program->log();

    if (!program->link())
        qCritical() << "Water link error:" << program->log();
}

void WaterLayer::setFlood(
    const std::vector<std::vector<float>>& flood,
    const std::vector<std::vector<float>>& dem,
    float demMinHeight,
    float heightScale,
    float horizontalScale)
{
    // Each vertex: vec3 position + float depth = 4 floats
    struct WaterVert {
        float x, y, z;
        float depth;
    };

    std::vector<WaterVert> verts;
    verts.reserve(flood.size() * flood[0].size() * 6);

    int rows = flood.size();
    int cols = flood[0].size();

    float maxFlood = 0.0f;
    for (const auto& r : flood)
        for (float v : r)
            maxFlood = std::max(maxFlood, v);

    if (maxFlood < 0.001f) {
        vertexCount = 0;
        return;
    }

    float waterOffset = 0.3f;  // lift water slightly above terrain

    for (int z = 0; z < rows - 1; z++) {
        for (int x = 0; x < cols - 1; x++) {

            float d00 = flood[z][x];
            float d10 = flood[z][x+1];
            float d01 = flood[z+1][x];
            float d11 = flood[z+1][x+1];

            // Only render quad if at least one corner has water
            float maxCell = std::max({d00, d10, d01, d11});
            if (maxCell < 0.01f) continue;

            // Terrain heights at each corner
            auto terrainY = [&](int row, int col) -> float {
                float h = (dem[row][col] - demMinHeight) * heightScale;
                return h;
            };



            float fx0 = (x   - cols / 2.0f) * horizontalScale;
            float fx1 = (x+1 - cols / 2.0f) * horizontalScale;
            float fz0 = (z   - rows / 2.0f) * horizontalScale;
            float fz1 = (z+1 - rows / 2.0f) * horizontalScale;

            // Water surface sits at terrain height + flood depth
            // (simplified: use terrain height + small offset for flat water look)
            float y00 = terrainY(z,   x)   + 0.1f;
            float y10 = terrainY(z,   x+1) + 0.1f;
            float y01 = terrainY(z+1, x)   + 0.1f;
            float y11 = terrainY(z+1, x+1) + 0.1f;

            // Triangle 1
            verts.push_back({fx0, y00, fz0, d00});
            verts.push_back({fx1, y10, fz0, d10});
            verts.push_back({fx0, y01, fz1, d01});

            // Triangle 2
            verts.push_back({fx1, y10, fz0, d10});
            verts.push_back({fx1, y11, fz1, d11});
            verts.push_back({fx0, y01, fz1, d01});
        }
    }

    vertexCount = verts.size();
    if (vertexCount == 0) return;

    vao.bind();
    vbo.bind();
    vbo.allocate(verts.data(), vertexCount * sizeof(WaterVert));

    program->bind();

    // position — location 0
    program->enableAttributeArray(0);
    program->setAttributeBuffer(0, GL_FLOAT,
                                0 * sizeof(float), 3, sizeof(WaterVert));

    // depth — location 1
    program->enableAttributeArray(1);
    program->setAttributeBuffer(1, GL_FLOAT,
                                3 * sizeof(float), 1, sizeof(WaterVert));

    program->release();
    vbo.release();
    vao.release();

    qDebug() << "WaterLayer built:" << vertexCount
             << "verts | maxFlood:" << maxFlood;
}

void WaterLayer::draw(
    const QMatrix4x4& proj,
    const QMatrix4x4& view,
    float time)
{
    if (vertexCount == 0 || !program) return;

    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glDepthMask(GL_FALSE);       // don't write to depth — water is transparent

    program->bind();

    QMatrix4x4 model;
    model.setToIdentity();

    program->setUniformValue("projection", proj);
    program->setUniformValue("view",       view);
    program->setUniformValue("model",      model);
    program->setUniformValue("time",       time);
    program->setUniformValue("lightDir",
                             QVector3D(0.5f, 0.8f, 0.3f).normalized());

    vao.bind();
    glDrawArrays(GL_TRIANGLES, 0, vertexCount);
    vao.release();

    program->release();

    glDepthMask(GL_TRUE);
    glDisable(GL_BLEND);
}

void WaterLayer::clear()
{
    vertexCount = 0;
}
