#ifndef DIALOG_H
#define DIALOG_H

#include <QDialog>

namespace Ui {
class Dialog;
}

class Dialog : public QDialog
{
    Q_OBJECT

public:
    explicit Dialog(QWidget *parent = nullptr);
    ~Dialog();

private:
    Ui::Dialog *ui;
private slots:
    void on_generateBtn_clicked();
    void on_cancelBtn_clicked();
signals:
    void generateRequested(double minLat , double maxLat , double minLon , double maxLon);
};

#endif // DIALOG_H
