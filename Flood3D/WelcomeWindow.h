#pragma once
#include <QMainWindow>
#include <QQuickWidget>
#include <QQuickItem>
#include <QVBoxLayout>
#include <QQmlEngine>
#include <QDebug>
#include <QTimer>
class WelcomeWindow : public QMainWindow {
    Q_OBJECT
public:
    explicit WelcomeWindow(QWidget* parent = nullptr)
        : QMainWindow(parent)
    {
        QWidget* central = new QWidget(this);
        setCentralWidget(central);

        QVBoxLayout* layout = new QVBoxLayout(central);
        layout->setContentsMargins(0, 0, 0, 0);
        layout->setSpacing(0);

        m_qml = new QQuickWidget(central);
        m_qml->setResizeMode(QQuickWidget::SizeRootObjectToView);
        m_qml->engine()->addImportPath("E:/Qt/6.11.0/msvc2022_64/qml");
        m_qml->setSource(QUrl("qrc:/WelcomeScreen.qml"));
        m_qml->setSource(QUrl("qrc:/WelcomeScreen.qml"));

        // Force status check after event loop starts
        QTimer::singleShot(500, this, [this]() {
            qDebug() << "Timer fired, status:" << m_qml->status();
            QQuickItem* root = m_qml->rootObject();
            qDebug() << "root:" << root;
            if (root) {
                connect(root, SIGNAL(newProjectRequested()),
                        this, SIGNAL(newProjectRequested()));
                connect(root, SIGNAL(openProjectRequested()),
                        this, SIGNAL(openProjectRequested()));
                qDebug() << "Signals connected";
            }
        });
        m_qml->setSizePolicy(QSizePolicy::Expanding, QSizePolicy::Expanding);
        layout->addWidget(m_qml);

        connect(m_qml, &QQuickWidget::statusChanged,
                this, [this](QQuickWidget::Status status) {
                    qDebug() << "QML status:" << status;
                    if (status == QQuickWidget::Ready) {
                        QQuickItem* root = m_qml->rootObject();
                        qDebug() << "root:" << root;
                        if (root) {
                            bool ok1 = connect(root, SIGNAL(newProjectRequested()),
                                               this, SIGNAL(newProjectRequested()));
                            bool ok2 = connect(root, SIGNAL(openProjectRequested()),
                                               this, SIGNAL(openProjectRequested()));
                            qDebug() << "ok1:" << ok1 << "ok2:" << ok2;
                        }
                    }
                    if (status == QQuickWidget::Error) {
                        qDebug() << "QML errors:" << m_qml->errors();
                    }
                });
    }

    ~WelcomeWindow() {}

signals:
    void newProjectRequested();
    void openProjectRequested();

private:
    QQuickWidget* m_qml = nullptr;
};
