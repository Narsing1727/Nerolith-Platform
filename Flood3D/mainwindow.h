#ifndef MAINWINDOW_H
#define MAINWINDOW_H
#include "floodengineclient.h"
#include <QMainWindow>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QNetworkRequest>
#include "mapcanvas2d.h"
#include "mapcanvas3d.h"
#include <QDateTime>
#include<QTimer>
#include"satelliteloop.h"
#include"flood_ai_sender.h"

QT_BEGIN_NAMESPACE
namespace Ui {
class MainWindow;
}
QT_END_NAMESPACE

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

    struct AgentRisk {
        QString regionId;
        QString riskLevel;
        double  floodMaxM;
        int     riskInt;
    };
    void fetchAgentDetail(const QString& regionId);


private:
    Ui::MainWindow *ui;

   double lastSimulationMs = 0.0;

    void fetchLatestSnapshotAndUpdate();
    std::vector<AgentRisk> latestAgentRisks;

    FloodAISender* floodAI = nullptr;
    int sweTickIndex = 0;

    float demMinElev = 0.0f;
    float demMaxElev = 0.0f;

    // SWE animation
    std::vector<std::vector<std::vector<float>>> sweFrames;
    int  sweCurrentFrame = 0;
    bool sweRunning      = false;
    QTimer* sweTimer     = nullptr;
    void onCascadeReportClicked();
    void onSurrogateAnalysisClicked();
    void runSWEAnimation();
    void onSWEFrame(int frameIndex);
    void updateAIRiskMarkers();






       void log(const QString& msg);
    std::vector<std::vector<float>>demGrid;
       int demRows =0;
    int demCols =0;
           QNetworkAccessManager* netManager;
    void loadGeoTiff(const QString& tifPath);

           void saveGridAsCSV(
               const QString& csvPath,
        const std::vector<std::vector<float>>& grid);
    MapCanvas2D* mapCanvas;
           std::vector<std::vector<float>> floodGrid;
    void saveFloodMetadata(
        const QString& jsonPath,
        double rainfall,
        const std::vector<std::vector<float>>& floodGrid);
    bool showDEM = false;
           bool demReady = false;
           //rain state
           bool rainReady = false;
           QDateTime rainStart;
           QDateTime rainEnd;
           double avgRainfall = 0.0;
           double GminLat;
            double GmaxLat;
            double GminLon;
             double GmaxLon;
            QString currentSessionPrefix;
            //Rainfall api
             void fetchRainfallFromAPI();
             void handleRainfallReply(QNetworkReply* reply);
             FloodEngineClient engine;
             // 3d logic
             MapCanvas3D* mapCanvas3D = nullptr;

SatelliteLoop* satLoop = nullptr;


private slots:
    void computeFloodArea();
    void onCellClicked(int row, int col);
    void on_loadDemAction_triggered();
    void on_generateDemAction_triggered();
    void on_loadFloodAction_triggered();
    // void on_DEM_CHECKBOX_checkStateChanged();
    void startDemGeneration(double minLat, double maxLat,
                            double minLon, double maxLon);
    void on_DEM_CHECKBOX_checkStateChanged(Qt::CheckState state);

    void onRainSelected(QDateTime start, QDateTime end);
    void on_actionFetchRain_triggered();
 void on_FLOOD_CHECKBOX_checkStateChanged(Qt::CheckState state);
        void runSimulation();
 void uploadToAzure(const QString& filePath , const QString &blobPath);
        void generateAIAlert(
            double rainfall,
            double maxFlood,
            int low,
            int medium,
            int high);
 void runSatelliteSync();
void handleAIReply(QNetworkReply* reply);
        void generateImpactReport(
            double rainfall,
            double maxFlood,
            int low,
            int medium,
            int high);
// enum LogSection
// {
//     DEM,
//     RAIN,
//     SIM,
//     AI,
//     SYSTEM
// };
};
#endif // MAINWINDOW_H
