#include "rainfall_dialog.h"
#include "ui_rainfall_dialog.h"

rainFall_Dialog::rainFall_Dialog(QWidget *parent)
    : QDialog(parent)
    , ui(new Ui::rainFall_Dialog)
{
    ui->setupUi(this);
}

rainFall_Dialog::~rainFall_Dialog()
{
    delete ui;
}
void rainFall_Dialog::on_buttonBox_accepted(){
    emit rainSelected(
        ui->startTimeEdit->dateTime(),
        ui->endTimeEdit->dateTime()
        );
}
