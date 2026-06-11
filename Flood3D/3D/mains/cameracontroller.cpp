#include "cameracontroller.h"
#include <QMouseEvent>
#include <QWheelEvent>
#include <QKeyEvent>
#include <QtMath>
#include <QDebug>

CameraController::CameraController() {}

void CameraController::mousePressEvent(QMouseEvent* e)
{
    lastMousePos = e->pos();
}

void CameraController::mouseMoveEvent(QMouseEvent* e, std::function<void()> updateFunc)
{
    QPoint delta = e->pos() - lastMousePos;
    lastMousePos = e->pos();

    if (e->buttons() & Qt::LeftButton) {
        yaw   += delta.x() * 0.3f;
        pitch += delta.y() * 0.3f;
        pitch = qBound(-89.0f, pitch, 89.0f);
        updateFunc();
    }
    else if (e->buttons() & Qt::RightButton) {
        float panSpeed = distance * 0.002f;
        QVector3D right(qCos(qDegreesToRadians(yaw)), 0, qSin(qDegreesToRadians(yaw)));
        QVector3D up(0, 1, 0);
        targetOffset -= right * delta.x() * panSpeed;
        targetOffset += up   * delta.y() * panSpeed;
        updateFunc();
    }
}

void CameraController::wheelEvent(QWheelEvent* e, std::function<void()> updateFunc)
{
    distance -= e->angleDelta().y() * 0.1f;
    distance = qBound(10.0f, distance, 2000.0f);
    updateFunc();
}

void CameraController::keyPressEvent(QKeyEvent* e, std::function<void()> updateFunc)
{
    if (e->key() == Qt::Key_R) {
        yaw          = -90.0f;
        pitch        = -30.0f;
        distance     = 200.0f;
        targetOffset = QVector3D(0, 0, 0);
        qDebug() << "Camera reset";
        updateFunc();
    }
}

QMatrix4x4 CameraController::viewMatrix() const
{
    float yawRad   = qDegreesToRadians(yaw);
    float pitchRad = qDegreesToRadians(pitch);

    QVector3D camPos(
        distance * qCos(pitchRad) * qCos(yawRad),
        distance * qSin(pitchRad),
        distance * qCos(pitchRad) * qSin(yawRad)
        );

    QMatrix4x4 view;
    view.lookAt(camPos + targetOffset, targetOffset, QVector3D(0,1,0));
    return view;
}
