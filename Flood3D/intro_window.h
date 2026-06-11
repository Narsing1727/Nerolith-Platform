#ifndef INTRO_WINDOW_H
#define INTRO_WINDOW_H

#include <QMainWindow>

namespace Ui {
class intro_window;
}

class intro_window : public QMainWindow
{
    Q_OBJECT

public:
    explicit intro_window(QWidget *parent = nullptr);
    ~intro_window();


private:
    Ui::intro_window *ui;
private slots:
       void on_exitButton_clicked();
      void on_startButton_clicked();
};

#endif // INTRO_WINDOW_H
