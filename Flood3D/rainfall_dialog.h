#ifndef RAINFALL_DIALOG_H
#define RAINFALL_DIALOG_H

#include <QDialog>

namespace Ui {
class rainFall_Dialog;
}

class rainFall_Dialog : public QDialog
{
    Q_OBJECT

public:
    explicit rainFall_Dialog(QWidget *parent = nullptr);
    ~rainFall_Dialog();
signals:
    void rainSelected(QDateTime start, QDateTime end);
private slots:
    void on_buttonBox_accepted();
private:
    Ui::rainFall_Dialog *ui;
};

#endif // RAINFALL_DIALOG_H
