#include "intro_window.h"
#include "ui_intro_window.h"
#include<QApplication>
#include"mainwindow.h"
intro_window::intro_window(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::intro_window)
{
    ui->setupUi(this);
}

intro_window::~intro_window()
{
    delete ui;
}

void intro_window::on_exitButton_clicked()
{
    QApplication::quit();
}
void intro_window::on_startButton_clicked()
{
    MainWindow *main = new MainWindow();
    main->show();

    this->close();
}
