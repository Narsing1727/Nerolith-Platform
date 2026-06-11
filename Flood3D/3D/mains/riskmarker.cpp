#include "riskmarker.h"
#include <QDebug>
#include <QtMath>

RiskMarkerRenderer::RiskMarkerRenderer() {}

RiskMarkerRenderer::~RiskMarkerRenderer()
{
    vbo.destroy();
    vao.destroy();
    delete program;
}

void RiskMarkerRenderer::init()
{
    initializeOpenGLFunctions();
    program = new QOpenGLShaderProgram();

    // Billboard vertex shader
    const char* vert = R"(
#version 330 core
layout(location=0) in vec3 worldPos;
layout(location=1) in vec4 color;
layout(location=2) in vec2 offset;

out vec4 fragColor;
out vec2 fragUV;

uniform mat4 projection;
uniform mat4 view;
uniform float time;
uniform float billboardSize;

void main()
{
    fragColor = color;
    fragUV    = offset * 0.5 + 0.5;

    // Pulse scale
    float pulse = 1.0 + 0.12 * sin(time * 3.0);

    // Billboard: extract camera right/up from view matrix
    vec3 camRight = vec3(view[0][0], view[1][0], view[2][0]);
    vec3 camUp    = vec3(view[0][1], view[1][1], view[2][1]);

    vec3 billboardPos = worldPos
        + camRight * offset.x * billboardSize * pulse
        + camUp    * offset.y * billboardSize * pulse;

    gl_Position = projection * view * vec4(billboardPos, 1.0);
}
)";

    // Billboard fragment shader — pin shape
    const char* frag = R"(
#version 330 core
in vec4 fragColor;
in vec2 fragUV;
out vec4 FragColor;

uniform float time;

void main()
{
    vec2 uv = fragUV * 2.0 - 1.0; // -1 to 1

    // PIN SHAPE:
    // Top circle + bottom point
    float circle = length(uv - vec2(0.0, 0.3));
    float inCircle = 1.0 - smoothstep(0.55, 0.65, circle);

    // Triangle point at bottom
    float tip = 1.0 - smoothstep(0.0, 0.08,
        abs(uv.x) - (0.55 * (-uv.y - 0.3) * 0.6));
    float inTip = tip * step(-0.35, -uv.y) *
                  step(uv.y, -0.0);

    float shape = max(inCircle, inTip);
    if (shape < 0.1) discard;

    // Pulse brightness
    float pulse = 0.85 + 0.15 * sin(time * 3.0);

    // Inner glow
    float innerGlow = 1.0 - smoothstep(0.2, 0.5, circle);
    vec3 glowColor  = fragColor.rgb + vec3(0.3) * innerGlow;

    // White highlight
    vec2 highlight = uv - vec2(-0.15, 0.5);
    float spec = 1.0 - smoothstep(0.0, 0.25,
                                   length(highlight));
    glowColor += vec3(spec * 0.4);

    // Outline
    float outline = smoothstep(0.55, 0.65, circle) *
                    smoothstep(0.70, 0.60, circle);

    vec3 finalColor = mix(glowColor,
                          vec3(0.1), outline) * pulse;

    FragColor = vec4(finalColor, shape);
}
)";

    if (!program->addShaderFromSourceCode(
            QOpenGLShader::Vertex, vert))
        qCritical() << "Billboard vert:" << program->log();

    if (!program->addShaderFromSourceCode(
            QOpenGLShader::Fragment, frag))
        qCritical() << "Billboard frag:" << program->log();

    if (!program->link())
        qCritical() << "Billboard link:" << program->log();

    vao.create();
    vbo.create();
    vbo.setUsagePattern(QOpenGLBuffer::DynamicDraw);
}

void RiskMarkerRenderer::setMarkers(
    const std::vector<RiskMarker>& m)
{
    markers = m;
    buildGeometry();
}

void RiskMarkerRenderer::buildGeometry()
{
    struct Vert {
        QVector3D worldPos;
        QVector4D color;
        QVector2D offset;
    };

    std::vector<Vert> verts;

    // Billboard corners (2 triangles = quad)
    QVector2D corners[6] = {
        {-1,-1}, { 1,-1}, { 1, 1},
        {-1,-1}, { 1, 1}, {-1, 1}
    };

    for (const auto& m : markers) {

        QVector4D col;
        switch (m.riskLevel) {
        case 2: col = QVector4D(0.95f, 0.15f, 0.15f, 1.0f); break;
        case 1: col = QVector4D(1.00f, 0.60f, 0.00f, 1.0f); break;
        default:col = QVector4D(0.10f, 0.85f, 0.20f, 1.0f); break;
        }

        for (const auto& c : corners)
            verts.push_back({m.worldPos, col, c});
    }

    vertexCount = verts.size();
    if (vertexCount == 0) return;

    vao.bind();
    vbo.bind();
    vbo.allocate(verts.data(), vertexCount * sizeof(Vert));

    program->bind();

    // worldPos
    program->enableAttributeArray(0);
    program->setAttributeBuffer(0, GL_FLOAT,
                                offsetof(Vert, worldPos), 3, sizeof(Vert));

    // color
    program->enableAttributeArray(1);
    program->setAttributeBuffer(1, GL_FLOAT,
                                offsetof(Vert, color), 4, sizeof(Vert));

    // offset
    program->enableAttributeArray(2);
    program->setAttributeBuffer(2, GL_FLOAT,
                                offsetof(Vert, offset), 2, sizeof(Vert));

    program->release();
    vbo.release();
    vao.release();
}

void RiskMarkerRenderer::draw(
    const QMatrix4x4& proj,
    const QMatrix4x4& view,
    float time)
{
    if (vertexCount == 0) return;

    glDisable(GL_DEPTH_TEST);
    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glDepthMask(GL_FALSE);

    program->bind();
    program->setUniformValue("projection",    proj);
    program->setUniformValue("view",          view);
    program->setUniformValue("time",          time);
    program->setUniformValue("billboardSize", 2.0f);

    vao.bind();
    glDrawArrays(GL_TRIANGLES, 0, vertexCount);
    vao.release();

    program->release();

    glDepthMask(GL_TRUE);
    glDisable(GL_BLEND);
    glEnable(GL_DEPTH_TEST);
}
