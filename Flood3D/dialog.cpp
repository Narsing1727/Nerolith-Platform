#include "dialog.h"
#include "ui_dialog.h"

Dialog::Dialog(QWidget *parent)
    : QDialog(parent)
    , ui(new Ui::Dialog)
{
    ui->setupUi(this);
}

Dialog::~Dialog()
{
    delete ui;
}
void Dialog :: on_generateBtn_clicked(){
    emit generateRequested(
        ui->minLatSpin->value(),
        ui->maxLatSpin->value(),
        ui->minLonSpin->value(),
        ui->maxLonSpin->value()
        );
    accept();
}
void Dialog::on_cancelBtn_clicked()
{
    reject();
}
