#include <QApplication>
#include "WelcomeWindow.h"
#include "mainwindow.h"

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    app.setApplicationName("Nerolith");
    app.setOrganizationName("Nerolith Technologies");

    WelcomeWindow* welcome = new WelcomeWindow();
    welcome->resize(1456, 816);
    welcome->show();

    MainWindow* mainWin = nullptr;

    QObject::connect(welcome, &WelcomeWindow::newProjectRequested,
                     [&]() {
                         qDebug() << "NEW PROJECT SIGNAL RECEIVED";
                         mainWin = new MainWindow();
                         mainWin->resize(1456, 816);
                         mainWin->show();
                         welcome->close();
                     });

    QObject::connect(welcome, &WelcomeWindow::openProjectRequested,
                     [&]() {
                         qDebug() << "OPEN PROJECT SIGNAL RECEIVED";
                         mainWin = new MainWindow();
                         mainWin->resize(1456, 816);
                         mainWin->show();
                         welcome->close();
                     });

    return app.exec();
}
