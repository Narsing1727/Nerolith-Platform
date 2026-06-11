#pragma once
#include <QVector3D>
#include <QPoint>
#include <QMatrix4x4>

class QMouseEvent;
class QWheelEvent;
class QKeyEvent;

class CameraController
{
public:
    CameraController();

    void mousePressEvent(QMouseEvent* e);
    void mouseMoveEvent(QMouseEvent* e, std::function<void()> updateFunc);
    void wheelEvent(QWheelEvent* e, std::function<void()> updateFunc);
    void keyPressEvent(QKeyEvent* e, std::function<void()> updateFunc);

    QMatrix4x4 viewMatrix() const;

    float yaw      = -90.0f;
    float pitch    = -30.0f;
    float distance = 200.0f;
    QVector3D targetOffset{0, 0, 0};

private:
    QPoint lastMousePos;
};
