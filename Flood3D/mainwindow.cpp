#include "mainwindow.h"
#include <gdal_priv.h>
#include <cpl_conv.h>
#include <vector>
#include <QJsonDocument>
#include <QJsonObject>
#include <chrono>
#include <QJsonArray>
#include <QApplication>
#include <QIcon>
#include <QTextStream>
#include "./ui_mainwindow.h"
#include <QFileDialog>
#include <QFile>
#include <QtConcurrent>
#include <QFutureWatcher>
#include <limits>
#include "dialog.h"
#include "rainfall_dialog.h"
#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QNetworkReply>
#include <QDateTime>
#include <QCryptographicHash>
#include <QMessageAuthenticationCode>
#include <QFile>
#include "satelliteloop.h"
#include <QInputDialog>
#include"mapcanvas2d.h"
using FrameVec = std::vector<std::vector<std::vector<float>>>;
#include"intro_window.h"


MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , ui(new Ui::MainWindow)
{

    ui->setupUi(this);
    ui->watershedCheckbox->setChecked(false);
    connect(ui->contourCheckbox,
            &QCheckBox::toggled,
            this, [this](bool checked) {
                mapCanvas->setContourLines(checked);
            });





    satLoop = new SatelliteLoop(&engine, this);
    connect(satLoop,
            &SatelliteLoop::logMessage,
            this,
            [this](const QString& msg)
            {
                log(msg);
            });




    // SWE timeline
    sweTimer = new QTimer(this);
    sweTimer->setInterval(200); // 5 fps playback

    connect(sweTimer, &QTimer::timeout, this, [this]() {
        if (sweFrames.empty()) { sweTimer->stop(); return; }
        int next = sweCurrentFrame + 1;
        if (next >= (int)sweFrames.size()) {
            sweTimer->stop();
            sweRunning = false;
            ui->swePlayBtn->setText("▶ Play");
            return;
        }
        onSWEFrame(next);
    });

    connect(ui->swePlayBtn, &QPushButton::clicked,
            this, [this]() {
                if (sweFrames.empty()) {
                    runSWEAnimation();
                    return;
                }
                if (!sweRunning) {
                    sweRunning = true;
                    ui->swePlayBtn->setText("▶▶ Playing");
                    sweTimer->start();
                }
            });

    connect(ui->swePauseBtn, &QPushButton::clicked,
            this, [this]() {
                sweTimer->stop();
                sweRunning = false;
                ui->swePlayBtn->setText("▶ Play");
            });

    connect(ui->sweResetBtn, &QPushButton::clicked,
            this, [this]() {
                sweTimer->stop();
                sweRunning = false;
                sweCurrentFrame = 0;
                ui->swePlayBtn->setText("▶ Play");
                ui->sweSlider->setValue(0);
                ui->sweTimeLabel->setText("T = 0.0 s");
                if (!sweFrames.empty()) onSWEFrame(0);
                if (!floodGrid.empty()) {
                    mapCanvas3D->setFlood(floodGrid);
                    mapCanvas->setFlood(floodGrid);
                }
            });

    connect(ui->sweSlider, &QSlider::valueChanged,
            this, [this](int val) {
                if (sweFrames.empty()) return;
                int frameIdx = (val * (sweFrames.size()-1)) / 1000;
                frameIdx = std::max(0,
                                    std::min((int)sweFrames.size()-1, frameIdx));
                onSWEFrame(frameIdx);
            });



    connect(ui->cascadeReportBtn, &QAction::triggered,
            this, &MainWindow::onCascadeReportClicked);


    connect(ui->surrogateAnalysisBtn, &QAction::triggered,
            this, &MainWindow::onSurrogateAnalysisClicked);






    connect(ui->satelliteSyncBtn,
            &QAction::triggered,
            this,
            &MainWindow::runSatelliteSync);

    connect(ui->twiCheckbox,
            &QCheckBox::toggled,
            this, [this](bool checked) {
                mapCanvas->setTWIVisible(checked);
            });


    connect(ui->watershedCheckbox,
            &QCheckBox::toggled,
            this, [this](bool checked) {
                mapCanvas->setWatershedVisible(checked);
            });

    connect(ui->actionFlood_Area, &QAction::triggered,
            this, &MainWindow::computeFloodArea);


    connect(ui->vectorRoadsCheckbox,
            &QCheckBox::toggled,
            this, [this](bool checked) {
                mapCanvas3D->setRoadsVisible(checked);
            });







    connect(ui->runButton, &QAction::triggered,
            this, &MainWindow::runSimulation);
    netManager = new QNetworkAccessManager(this);


    connect(ui->buildingsCheckbox,
            &QCheckBox::toggled,
            this, [this](bool checked) {
                mapCanvas3D->setBuildingsVisible(checked);
            });



    // uploadToAzure("D:/test.txt");
    mapCanvas = new MapCanvas2D(this);
    mapCanvas3D  = new MapCanvas3D(this);




    connect(mapCanvas3D, &MapCanvas3D::aiMarkerClicked,
            this, [this](const QString& regionId) {
                fetchAgentDetail(regionId);
            });



    QVBoxLayout* layout = new QVBoxLayout(ui->map2DWidget);
    layout->setContentsMargins(0,0,0,0);
    layout->addWidget(mapCanvas);
    connect(mapCanvas,
            &MapCanvas2D::cellClicked,
            this,
            &MainWindow::onCellClicked);
    QVBoxLayout* layout3D = new QVBoxLayout(ui->map3DWidget);
    layout3D->setContentsMargins(0, 0, 0, 0);
    layout3D->addWidget(mapCanvas3D);
mapCanvas->setFrameShape(QFrame::NoFrame);

    bool ok = engine.init();




    floodAI = new FloodAISender(this);




bool aiConnected =
    floodAI->connectToAI(
        "http://127.0.0.1:8000/ingest/tick");

if (aiConnected)
    log("FLOOD-AI connected on port 5050");
else
    log("FLOOD-AI not connected — start FLOOD-AI server first");




    if (!ok) {
        // log(" FloodEngine DLL init failed");
    }

}

MainWindow::~MainWindow()
{

    delete ui;

}

void MainWindow::log(const QString& msg)
{
    QString colored = msg;

    if (msg.contains("❌"))
        colored = "<span style='color:red;'>" + msg + "</span>";
    else if (msg.contains("⚠"))
        colored = "<span style='color:orange;'>" + msg + "</span>";
    else if (msg.contains("AI"))
        colored = "<span style='color:#b84cff;'>" + msg + "</span>";
    else if (msg.contains("DEM"))
        colored = "<span style='color:#00bcd4;'>" + msg + "</span>";
    else if (msg.contains("Rain"))
        colored = "<span style='color:#4caf50;'>" + msg + "</span>";
    else
        colored = "<span style='color:white;'>" + msg + "</span>";

    ui->consoleTextEdit->appendHtml(colored);
}
void MainWindow::on_loadDemAction_triggered()
{
    QString filepath = QFileDialog :: getOpenFileName(
        this,
        "Load DEM CSV",
        "",
        "CSV Files(*.csv)"
        );
    if(filepath.isEmpty()){
          return;
}

    QFile file(filepath);
if(!file.open(QIODevice::ReadOnly | QIODevice :: Text)){
        ui->consoleTextEdit->appendPlainText("DEM file open failed");
    return;
}
QTextStream in(&file);
int rows =0;
int cols =0;
double minElev = std::numeric_limits<double>::max();
double maxElev = std::numeric_limits<double>::lowest();
demGrid.clear();
while (!in.atEnd()) {
    QString line = in.readLine().trimmed();
    if (line.isEmpty()) continue;

    QStringList values = line.split(",", Qt::SkipEmptyParts);
    std::vector<float>row;
    if (rows == 0)
        cols = values.size();

    for (const QString& v : values) {
        double elev = v.toDouble();
        row.push_back(v.toFloat());
        minElev = std::min(minElev, elev);
        maxElev = std::max(maxElev, elev);

    }
    demGrid.push_back(row);
    rows++;
}
demRows = demGrid.size();
demCols = demGrid[0].size();
file.close();
log(" DEM Loaded");
ui->layersListWidget->addItem("DEM (CSV)");
// log("Rows: " + QString::number(rows));
// log("Cols: " + QString::number(cols));
// log("Min Elev: " + QString::number(minElev));
// log("Max Elev: " + QString::number(maxElev));
if(showDEM){
    mapCanvas->setDEM(demGrid);
    mapCanvas3D->setDEM(demGrid);

}

}
void MainWindow::saveGridAsCSV(
    const QString& csvPath,
    const std::vector<std::vector<float>>& grid)
{
    QFile file(csvPath);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Text)) {
        // log(" CSV save failed");
        return;
    }

    QTextStream out(&file);

    for (const auto& row : grid) {
        for (int j = 0; j < row.size(); j++) {
            out << row[j];
            if (j != row.size() - 1)
                out << ",";
        }
        out << "\n";
    }

    file.close();
    // log(" CSV saved: " + csvPath);
}



void MainWindow::on_generateDemAction_triggered()
{
    Dialog dlg(this);

    connect(&dlg, &Dialog::generateRequested,
            this, &MainWindow::startDemGeneration);

    dlg.exec();
}
void MainWindow::loadGeoTiff(const QString& tifPath)
{
    GDALAllRegister();

    GDALDataset* ds = (GDALDataset*)GDALOpen(
        tifPath.toStdString().c_str(),
        GA_ReadOnly
        );

    if (!ds) {
        // log(" GDAL failed to open GeoTIFF");
        return;
    }

    int width  = ds->GetRasterXSize();
    int height = ds->GetRasterYSize();

    GDALRasterBand* band = ds->GetRasterBand(1);

    std::vector<float> buffer(width * height);
    band->RasterIO(
        GF_Read,
        0, 0,
        width, height,
        buffer.data(),
        width, height,
        GDT_Float32,
        0, 0
        );

    demGrid.clear();
    demGrid.resize(height, std::vector<float>(width));

    float minE = 1e9, maxE = -1e9;

    for (int i = 0; i < height; i++) {
        for (int j = 0; j < width; j++) {
            float e = buffer[i * width + j];
            demGrid[i][j] = e;
            minE = std::min(minE, e);
            maxE = std::max(maxE, e);
        }
    }

    GDALClose(ds);

    // log("GDAL GeoTIFF Loaded");
    log("Rows: " + QString::number(height));
    log("Cols: " + QString::number(width));
    log("Min Elev: " + QString::number(minE));
    log("Max Elev: " + QString::number(maxE));


    demMinElev = minE;
    demMaxElev = maxE;




    ui->layersListWidget->addItem("DEM (GDAL)");
    if (!engine.isReady()) {
        log("❌ Engine not ready, DEM not sent");
        return;
    }

    engine.loadDEM(demGrid);
    engine.setCellSize(30.0);
    qDebug() << "Engine DEM loaded, rows=" << demGrid.size() << "cols=" << demGrid[0].size();
    engine.setDuration(avgRainfall > 0 ? avgRainfall / 10.0 : 1.0);
    mapCanvas->setDEM(demGrid);
    mapCanvas3D->setDEM(demGrid);
    double centerLat = (GminLat + GmaxLat) / 2.0;
    double centerLon = (GminLon + GmaxLon) / 2.0;
    mapCanvas3D->loadSatelliteTiles(GminLat, GmaxLat,
                                    GminLon, GmaxLon, 17);
    mapCanvas->fetchSatelliteTiles(GminLat, GmaxLat,
                                   GminLon, GmaxLon, 16);
    mapCanvas3D->fetchRoads(GminLat, GmaxLat, GminLon, GmaxLon);

    mapCanvas3D->fetchBuildings(GminLat, GmaxLat, GminLon, GmaxLon);
qDebug() << "Cache path:" << QFileInfo("roads_cache.json").absoluteFilePath();
    mapCanvas->computeWatershed();
    log("satelite called");
    ui->DEM_CHECKBOX->setChecked(true);
    demReady = true;
}

void MainWindow::startDemGeneration(double minLat, double maxLat,
                                    double minLon, double maxLon)
{
    QString saveDir = QFileDialog::getExistingDirectory(this , "Select folder to save DEM");
    if(saveDir.isEmpty()) return;
    QString tifPath = saveDir + "/dem.tif";
    QString url =
        "https://portal.opentopography.org/API/globaldem?"
        "demtype=COP30"
        "&south=" + QString::number(minLat) +
        "&north=" + QString::number(maxLat) +
        "&west="  + QString::number(minLon) +
        "&east="  + QString::number(maxLon) +
        "&outputFormat=GTiff"
        "&API_Key=3a099296641fbf4a0cfdc1a990d08f3c";
    log("Dowloading DEM (GeoTiff)");
    GminLat = minLat;
    GmaxLat = maxLat;
    GminLon = minLon;
    GmaxLon = maxLon;
    QNetworkReply* reply =
        netManager->get(QNetworkRequest(QUrl(url)));

    connect(reply, &QNetworkReply::finished, this, [=]() {

        if (reply->error() != QNetworkReply::NoError) {
            ui->consoleTextEdit->appendPlainText(
                " Download failed: " + reply->errorString());
            reply->deleteLater();
            return;
        }

        QFile file(tifPath);
        if (!file.open(QIODevice::WriteOnly)) {
            ui->consoleTextEdit->appendPlainText("❌ Cannot save file");
            reply->deleteLater();
            return;
        }

        file.write(reply->readAll());
        file.close();

        ui->consoleTextEdit->appendPlainText(
            " GeoTIFF saved at: " + tifPath);

        loadGeoTiff(tifPath);

        QString csvPath = saveDir + "/dem.csv";
        saveGridAsCSV(csvPath, demGrid);


        // -------- CREATE SESSION FOLDER --------
        QString dateFolder =
            QDate::currentDate().toString("yyyy-MM-dd");

        QString sessionFolder =
            "session_" +
            QDateTime::currentDateTime().toString("HHmmss");

        currentSessionPrefix =
            "runs/" + dateFolder + "/" + sessionFolder + "/";

        // -------- UPLOAD DEM --------
        uploadToAzure(csvPath, currentSessionPrefix + "dem.csv");

        // log("DEM uploaded to Azure: " + currentSessionPrefix);
        if(showDEM){

            mapCanvas->setDEM(demGrid);
        mapCanvas3D->setDEM(demGrid);
        }

        reply->deleteLater();
    });
}
void MainWindow :: on_loadFloodAction_triggered()
{
    if (demGrid.empty()) {
        log(" Load DEM before loading flood data");
        return;
    }

    QString filepath = QFileDialog::getOpenFileName(
        this,
        "Load Flood CSV",
        "",
        "CSV Files (*.csv)"
        );

    if (filepath.isEmpty())
        return;

    QFile file(filepath);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) {
        log(" Flood CSV open failed");
        return;
    }

    QTextStream in(&file);

    floodGrid.clear();
    int rows = 0;
    int cols = demGrid[0].size();

    while (!in.atEnd()) {
        QString line = in.readLine().trimmed();
        if (line.isEmpty()) continue;

        QStringList values = line.split(",", Qt::SkipEmptyParts);
        std::vector<float> row;

        if (values.size() != cols) {
            log(" Flood CSV column mismatch with DEM");
            return;
        }

        for (const QString& v : values)
            row.push_back(v.toFloat());

        floodGrid.push_back(row);
        rows++;
    }

    file.close();

    if (rows != demGrid.size()) {
        log(" Flood CSV row mismatch with DEM");
        floodGrid.clear();
        return;
    }

    log("Flood CSV Loaded");
    mapCanvas->setFlood(floodGrid);
}

void MainWindow::on_DEM_CHECKBOX_checkStateChanged(Qt::CheckState state)
{
    bool show = (state == Qt::Checked);

    if (show && !demGrid.empty()) {
        mapCanvas->setDEM(demGrid);
        mapCanvas3D->setDEM(demGrid);
    } else {
        mapCanvas->clearDEM();
        // 3D me abhi clear nahi, bas redraw mat kar
    }
}

void MainWindow::on_actionFetchRain_triggered() {
    if (!demReady) {
        log("⚠ Generate DEM first");
        return;
    }

    rainFall_Dialog dlg(this);
    connect(&dlg, &rainFall_Dialog::rainSelected,
            this, &MainWindow::onRainSelected);
    dlg.exec();
}

void MainWindow::onRainSelected(QDateTime start, QDateTime end)
{
    rainStart = start;
    rainEnd   = end;
    rainReady = true;
    // log("Rainfall time selected:");
    // log(start.toString(Qt::ISODate) + " → " +
    //     end.toString(Qt::ISODate));

    fetchRainfallFromAPI();

    //  Climate API abhi nahi
    //  Avg rainfall abhi nahi
}
void MainWindow::fetchRainfallFromAPI()
{
    // Center of DEM bbox
    double lat = (GminLat + GmaxLat) / 2.0;
    double lon = (GminLon + GmaxLon) / 2.0;

    QString startDate = rainStart.date().toString("yyyy-MM-dd");
    QString endDate   = rainEnd.date().toString("yyyy-MM-dd");

    QString url = QString(
                      "https://meteostat.p.rapidapi.com/point/daily?"
                      "lat=%1&lon=%2&start=%3&end=%4"
                      ).arg(lat)
                      .arg(lon)
                      .arg(startDate)
                      .arg(endDate);


    // log("Fetching rainfall from Meteostat (RapidAPI)...");
    // log(url);

    QNetworkRequest request{QUrl(url)};
    QString rapidKey = qEnvironmentVariable("RAPIDAPI_KEY");

    request.setRawHeader(
        "X-RapidAPI-Key",
        rapidKey.toUtf8());
    request.setRawHeader("X-RapidAPI-Host", "meteostat.p.rapidapi.com");

    QNetworkReply* reply = netManager->get(request);

    connect(reply, &QNetworkReply::finished, this, [=]() {
        handleRainfallReply(reply);
    });

}
void MainWindow::handleRainfallReply(QNetworkReply* reply)
{
    if (reply->error() != QNetworkReply::NoError) {
        log("❌ Rainfall API failed: " + reply->errorString());
        reply->deleteLater();
        return;
    }

    QByteArray response = reply->readAll();

    // log("RAW RESPONSE:");
    // log(QString(response));
    reply->deleteLater();

    QJsonDocument doc = QJsonDocument::fromJson(response);
    if (!doc.isObject()) {
        log("❌ Invalid JSON from Meteostat API");
        return;
    }

    QJsonObject root = doc.object();
    QJsonArray data = root["data"].toArray();

    if (data.isEmpty()) {
        log("❌ No rainfall data received");
        return;
    }

    double sum = 0.0;
    int count = 0;

    for (const auto& v : data) {
        QJsonObject obj = v.toObject();

        // Meteostat monthly precipitation (mm)
        if (obj.contains("prcp") && !obj["prcp"].isNull()) {
            sum += obj["prcp"].toDouble();
            count++;
        }
    }

    if (count == 0) {
        log("❌ Rainfall values missing in API response");
        return;
    }
// log(response);
    avgRainfall = sum / count;   // mm per month (average)
    rainReady = true;

    log(QString("✅ Avg Monthly Rainfall = %1 mm")
            .arg(avgRainfall));
    // avgRainfall *= 30;
    // floodGrid = engine.predictFlood(avgRainfall);

    // QString outDir = QFileDialog::getExistingDirectory(
    //     this, "Select folder to save flood output");

    // if (outDir.isEmpty()) return;

    // QString floodCsv = outDir + "/flood_depth.csv";
    // QString metaJson = outDir + "/metadata.json";

    // saveGridAsCSV(floodCsv, floodGrid);
    // saveFloodMetadata(metaJson, avgRainfall, floodGrid);

    // // ---- ANALYTICS ----
    // double maxF = 0.0;
    // for (const auto& r : floodGrid)
    //     for (float v : r)
    //         maxF = std::max(maxF, (double)v);

    // log("Max Flood Depth = " + QString::number(maxF));

    // // ---- VISUALIZE ----
    // mapCanvas->setFlood(floodGrid);
    // ui->FLOOD_CHECKBOX->setChecked(true);
    double avg1 = avgRainfall;
    avgRainfall *= 30;
    // log(QString("Final Rainfall Used = %1 mm").arg(avgRainfall));
    ui->rainfallLabel->setText(
        "🌧 Avg Rainfall: " + QString::number(avg1, 'f', 2) + " mm");
    ui->avgrainfall->setText(
        "Total Used: " + QString::number(avgRainfall, 'f', 2) + " mm");

}
void MainWindow::on_FLOOD_CHECKBOX_checkStateChanged(Qt::CheckState state)
{
    bool show = (state == Qt::Checked);

    if (show && !floodGrid.empty()) {
        mapCanvas->setFlood(floodGrid);
    } else {
        mapCanvas->clearFlood();   // ye function add karenge
    }

    mapCanvas->update();
}
void MainWindow::saveFloodMetadata(
    const QString& jsonPath,
    double rainfall,
    const std::vector<std::vector<float>>& floodGrid)
{
    int rows = floodGrid.size();
    int cols = rows ? floodGrid[0].size() : 0;

    double maxFlood = 0.0;
    int low = 0, medium = 0, high = 0;


    for (const auto& r : floodGrid) {
        for (float v : r) {
            maxFlood = std::max(maxFlood, (double)v);
        }
    }
    if (maxFlood <= 0.0) maxFlood = 1.0;

    for (const auto& r : floodGrid) {
        for (float v : r) {
            double norm = v / maxFlood;   // 0 → 1

            if (norm < 0.3)
                low++;
            else if (norm < 0.6)
                medium++;
            else
                high++;
        }
    }

    QJsonObject meta;
    meta["rainfall_mm"] = rainfall;
    meta["rows"] = rows;
    meta["cols"] = cols;
    meta["max_flood_depth"] = maxFlood;

    meta["severity_low_cells"] = low;
    meta["severity_medium_cells"] = medium;
    meta["severity_high_cells"] = high;

    meta["timestamp"] =
        QDateTime::currentDateTime().toString(Qt::ISODate);

    QJsonDocument doc(meta);

    QFile file(jsonPath);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Text)) {
        log("❌ Metadata save failed");
        return;
    }

    file.write(doc.toJson(QJsonDocument::Indented));
    file.close();

    log("✅ Metadata saved: " + jsonPath);
}void MainWindow::runSimulation()


{




    if (!demReady) {
        log("Load DEM first");
        return;
    }

    if (!rainReady) {
        log("Fetch rainfall first");
        return;
    }
   engine.setDuration(avgRainfall / 10.0);
    log("Running simulation...");
    statusBar()->showMessage("Running simulation...");



    auto simStartTime = std::chrono::high_resolution_clock::now();

    auto future = QtConcurrent::run([=]() {
        return engine.predictFloodBlended(avgRainfall, 0.7);
    });
    auto* watcher =
        new QFutureWatcher<std::vector<std::vector<float>>>(this);

    connect(watcher,
            &QFutureWatcher<std::vector<std::vector<float>>>::finished,
            this,
            [=]() {

                floodGrid = watcher->result();

                auto simEndTime = std::chrono::high_resolution_clock::now();
                lastSimulationMs = std::chrono::duration<double, std::milli>(
                                       simEndTime - simStartTime).count();
                log(QString("⚡ Physics simulation time: %1 ms")
                        .arg(lastSimulationMs, 0, 'f', 1));
                satLoop->setFloodGrid(floodGrid);
                auto twi = engine.getTWI();
                qDebug() << "TWI size:" << twi.size();
                if (!twi.empty())
                    mapCanvas->setTWI(twi);
                mapCanvas->setFlood(floodGrid);
                mapCanvas3D->setFlood(floodGrid);

                qDebug() << "RUN SIMULATION FINISHED";

                qDebug() << "TWI size:" << twi.size();
                ui->FLOOD_CHECKBOX->setChecked(true);

                QString dateFolder =
                    QDate::currentDate().toString("yyyy-MM-dd");

                QString sessionFolder =
                    "session_" +
                    QDateTime::currentDateTime().toString("HHmmss");

                QString basePrefix =
                    "runs/" + dateFolder + "/" + sessionFolder + "/";

                QString tempDir = QDir::tempPath();

                QString floodCsv =
                    tempDir + "/flood_depth.csv";

                QString metaJson =
                    tempDir + "/metadata.json";

                saveGridAsCSV(floodCsv, floodGrid);
                saveFloodMetadata(metaJson, avgRainfall, floodGrid);
                double maxFlood = 0.0;
                int low = 0, medium = 0, high = 0;

                for (const auto& r : floodGrid)
                {
                    for (float v : r)
                    {
                        maxFlood = std::max(maxFlood, (double)v);
                    }
                }

                if (maxFlood <= 0) maxFlood = 1;

                for (const auto& r : floodGrid)
                {
                    for (float v : r)
                    {
                        double norm = v / maxFlood;

                        if (norm < 0.3)
                            low++;
                        else if (norm < 0.6)
                            medium++;
                        else
                            high++;
                    }
                }
                generateAIAlert(avgRainfall, maxFlood, low, medium, high);
                generateImpactReport(
                    avgRainfall,
                    maxFlood,
                    low,
                    medium,
                    high);
                QString mapPath =
                    QDir::tempPath() + "/risk_map.png";


                ui->layersListWidget->addItem("");

                QListWidgetItem *statsTitle = new QListWidgetItem("Simulation Stats");
                statsTitle->setForeground(QColor(200,200,200));
                statsTitle->setFlags(Qt::NoItemFlags);
                ui->layersListWidget->addItem(statsTitle);

                ui->layersListWidget->addItem(
                    "Rainfall Used: " + QString::number(avgRainfall, 'f', 2) + " mm");

                ui->layersListWidget->addItem(
                    "Max Flood Depth: " + QString::number(maxFlood, 'f', 3) + " m");

                ui->layersListWidget->addItem(
                    "High Risk Cells: " + QString::number(high));

                ui->layersListWidget->addItem(
                    "Medium Risk Cells: " + QString::number(medium));

                ui->layersListWidget->addItem(
                    "Low Risk Cells: " + QString::number(low));
                if (mapCanvas->saveRiskMap(mapPath))
                {
                    log("Risk map exported to azure");

                    uploadToAzure(
                        mapPath,
                        currentSessionPrefix + "risk_map.png");
                }
                else
                {
                    log("Risk map export failed");
                }
                // log("Files saved locally (temp)");

                if (currentSessionPrefix.isEmpty()) {
                    log("Session not initialized (Generate DEM first)");
                    return;
                }

                uploadToAzure(floodCsv,
                              currentSessionPrefix + "flood_depth.csv");

                uploadToAzure(metaJson,
                              currentSessionPrefix + "metadata.json");

                QString tempDir1 = QDir::tempPath();

                QString mapImage =
                    tempDir1 + "/risk_map.png";

                QPixmap pix = mapCanvas->grab();

                pix.save(mapImage);
                uploadToAzure(
                    mapImage,
                    currentSessionPrefix + "risk_map.png");
                // log("Risk map image saved");
                statusBar()->showMessage(
                    "Simulation Completed & Uploaded");

                watcher->deleteLater();
            });

    QListWidgetItem *low = new QListWidgetItem("■ Low Risk");
    low->setForeground(QColor(0,120,255));

    QListWidgetItem *medium = new QListWidgetItem("■ Medium Risk");
    medium->setForeground(QColor(255,165,0));

    QListWidgetItem *high = new QListWidgetItem("■ High Risk");
    high->setForeground(QColor(255,0,0));

    QListWidgetItem *title = new QListWidgetItem("Risk Legend");
    title->setForeground(QColor(200,200,200));
    title->setFlags(Qt::NoItemFlags);
    ui->layersListWidget->addItem(title);
    ui->layersListWidget->addItem(low);
    ui->layersListWidget->addItem(medium);
    ui->layersListWidget->addItem(high);
    watcher->setFuture(future);
}
void MainWindow::uploadToAzure(
    const QString &filePath,
    const QString &blobPath)
{
    QFile file(filePath);
    if (!file.open(QIODevice::ReadOnly))
    {
        qDebug() << "File open failed";
        return;
    }

    QByteArray fileData = file.readAll();
    file.close();

    QString sasContainerUrl =
        qEnvironmentVariable("AZURE_BLOB_SAS");
    int index = sasContainerUrl.indexOf('?');
    QString baseUrl = sasContainerUrl.left(index);
    QString sasToken = sasContainerUrl.mid(index);

    QString fullUrl = baseUrl + "/" + blobPath + sasToken;

    // qDebug() << "Uploading to:" << fullUrl;
QNetworkRequest request(QUrl::fromUserInput(fullUrl));
    request.setHeader(QNetworkRequest::ContentLengthHeader, fileData.size());
    request.setRawHeader("x-ms-blob-type", "BlockBlob");

    QNetworkReply *reply = netManager->put(request, fileData);

    connect(reply, &QNetworkReply::finished, this, [reply]() {
        if (reply->error() == QNetworkReply::NoError)
            qDebug() << "Upload successful!";
        else
            // qDebug() << "Upload failed:" << reply->errorString();

        reply->deleteLater();
    });
}
void MainWindow::generateAIAlert(
    double rainfall,
    double maxFlood,
    int low,
    int medium,
    int high)
{
    QString prompt =
        "You are a disaster management AI.\n"
        "Generate a short flood warning.\n\n"
        "Rainfall: " + QString::number(rainfall) + " mm\n"
                                      "Max Flood Depth: " + QString::number(maxFlood) + " m\n"
                                      "Low Severity Cells: " + QString::number(low) + "\n"
                                 "Medium Severity Cells: " + QString::number(medium) + "\n"
                                    "High Severity Cells: " + QString::number(high) + "\n\n"
                                  "Output format:\n"
                                  "⚠️ Flood Alert: <risk level>\n"
                                  "Water depth: <value>\n"
                                  "Recommended action: <short advice>";

    QUrl url("https://api.groq.com/openai/v1/chat/completions");

    QNetworkRequest request(url);

    request.setHeader(
        QNetworkRequest::ContentTypeHeader,
        "application/json");

    QString apiKey = qEnvironmentVariable("GROQ_API_KEY");

    request.setRawHeader(
        "Authorization",
        ("Bearer " + apiKey).toUtf8());

    QJsonObject message;
    message["role"] = "user";
    message["content"] = prompt;

    QJsonArray messages;
    messages.append(message);

    QJsonObject body;
    body["model"] = "llama-3.1-8b-instant";
    body["messages"] = messages;
    body["temperature"] = 0.3;

    QJsonDocument doc(body);
    QByteArray data = doc.toJson();

    QNetworkReply* reply = netManager->post(request, data);

    connect(reply, &QNetworkReply::finished,
            this, [=]() {
                handleAIReply(reply);
            });

    // log("AI alert generation started...");
}
void MainWindow::handleAIReply(QNetworkReply* reply)
{
    if (reply->error() != QNetworkReply::NoError)
    {
        log("AI API failed: " + reply->errorString());
        reply->deleteLater();
        return;
    }

    QByteArray response = reply->readAll();
    reply->deleteLater();

    QJsonDocument doc = QJsonDocument::fromJson(response);

    if (!doc.isObject())
    {
        log("Invalid AI JSON response");
        return;
    }

    QJsonObject root = doc.object();
    QJsonArray choices = root["choices"].toArray();

    if (choices.isEmpty())
    {
        log("AI returned empty response");
        return;
    }

    QJsonObject msg =
        choices[0].toObject()["message"].toObject();

    QString alertText = msg["content"].toString();

    log(" AI Flood Alert Generated:");
    QString alertBox =
        "<div style='border-left:4px solid #ff9800;"
        "background:#1e1e1e;padding:6px;margin:6px 0;'>"
        "<b style='color:#ff9800;'>⚠ AI FLOOD ALERT</b><br>" +
        alertText +
        "</div>";

    ui->consoleTextEdit->appendHtml(alertBox);

    QString alertPath =
        QDir::tempPath() + "/flood_alert.txt";

    QFile file(alertPath);

    if (file.open(QIODevice::WriteOnly | QIODevice::Text))
    {
        QTextStream out(&file);
        out << alertText;
        file.close();

        log("AI Alert and impact saved to azure storage");
    }

    uploadToAzure(
        alertPath,
        currentSessionPrefix + "flood_alert.txt");
}
void MainWindow::generateImpactReport(
    double rainfall,
    double maxFlood,
    int low,
    int medium,
    int high)
{
    QString prompt =
        "You are a flood simulation analyst for a research prototype.\n"
        "The data comes from a small DEM grid simulation, not a real city.\n"
        "Do NOT assume real world population or billions of damage.\n"
        "Only analyze the grid severity levels.\n\n"
        "Simulation data:\n"
        "Total accumulated rainfall of the area: " + QString::number(rainfall) + " mm\n"
                                      "Max simulated flood depth: " + QString::number(maxFlood/1000.0) + " m\n"
                                               "Low severity cells: " + QString::number(low) + "\n"
                                 "Medium severity cells: " + QString::number(medium) + "\n"
                                    "High severity cells: " + QString::number(high) + "\n\n"
                                  "Grid size: " + QString::number(demRows) + " x " + QString::number(demCols) + "\n"
                                  "Write a in detail technical impact summary including:\n"
                                  "- Flood severity distribution\n"
                                  "- Possible infrastructure stress\n"
                                  "- Suggested mitigation actions\n"
                                  "Do NOT invent population numbers or economic losses.\n"
                                  ;

    QUrl url("https://api.groq.com/openai/v1/chat/completions");

    QNetworkRequest request(url);

    request.setHeader(
        QNetworkRequest::ContentTypeHeader,
        "application/json");
    QString apiKey = qEnvironmentVariable("GROQ_API_KEY");

    request.setRawHeader(
        "Authorization",
        ("Bearer " + apiKey).toUtf8());

    QJsonObject message;
    message["role"] = "user";
    message["content"] = prompt;

    QJsonArray messages;
    messages.append(message);

    QJsonObject body;
    body["model"] = "llama-3.1-8b-instant";
    body["messages"] = messages;

    QJsonDocument doc(body);

    QNetworkReply* reply =
        netManager->post(request, doc.toJson());

    connect(reply,
            &QNetworkReply::finished,
            this,
            [=]()
            {
                QByteArray response = reply->readAll();
                reply->deleteLater();

                QJsonDocument doc =
                    QJsonDocument::fromJson(response);

                QJsonObject root = doc.object();
                QJsonArray choices =
                    root["choices"].toArray();

                QString text =
                    choices[0]
                        .toObject()["message"]
                        .toObject()["content"]
                        .toString();

                log("Impact report saved on azure");

                QString path =
                    QDir::tempPath() +
                    "/impact_report.txt";

                QFile file(path);

                if (file.open(QIODevice::WriteOnly))
                {
                    QTextStream out(&file);
                    out << text;
                    file.close();
                }

                uploadToAzure(
                    path,
                    currentSessionPrefix +
                        "impact_report.txt");
            });
}
void MainWindow::onCellClicked(int row, int col)
{
    if (demGrid.empty()) return;

    float elev = demGrid[row][col];
    float flood = 0;

    if (!floodGrid.empty())
        flood = floodGrid[row][col];

    QString msg =
        "<div style='background:#1e1e1e;"
        "border-left:4px solid #00bcd4;"
        "padding:6px;margin:4px 0;'>"
        "<b style='color:#00e5ff;'>CELL INFO</b><br>"
        "<span style='color:#bbbbbb;'>Row:</span> "
        "<span style='color:white;'>" + QString::number(row) + "</span><br>"
                                 "<span style='color:#bbbbbb;'>Col:</span> "
                                 "<span style='color:white;'>" + QString::number(col) + "</span><br>"
                                 "<span style='color:#bbbbbb;'>Elevation:</span> "
                                 "<span style='color:#4caf50;'>" + QString::number(elev) + " m</span><br>"
                                  "<span style='color:#bbbbbb;'>Flood Depth:</span> "
                                  "<span style='color:#ff9800;'>" + QString::number(flood, 'f', 6) + " m</span>"
                                            "</div>";

    ui->consoleTextEdit->appendHtml(msg);
}
void MainWindow::computeFloodArea()
{
    if (floodGrid.empty()) {
        log("⚠ Run simulation first");
        return;
    }

    if (GminLat == GmaxLat || GminLon == GmaxLon) {
        log("⚠ Generate DEM from coordinates first");
        return;
    }

    int rows = floodGrid.size();
    int cols = floodGrid[0].size();

    double latCenter = (GminLat + GmaxLat) / 2.0;
    double cellH = (GmaxLat - GminLat) / rows * 110540.0;
    double cellW = (GmaxLon - GminLon) / cols * 111320.0
                   * cos(qDegreesToRadians(latCenter));
    double cellArea = cellH * cellW;

    int floodedCells = 0;
    int totalCells = rows * cols;

    for (const auto& r : floodGrid)
        for (float v : r)
            if (v > 0) floodedCells++;

    double floodedAreaKm2 = floodedCells * cellArea / 1000000.0;
    double totalAreaKm2   = totalCells   * cellArea / 1000000.0;
    double floodPercent   = (double)floodedCells / totalCells * 100.0;

    log(QString("📐 Total Area: %1 km²").arg(totalAreaKm2, 0, 'f', 3));
    log(QString("🌊 Flooded Area: %1 km²").arg(floodedAreaKm2, 0, 'f', 3));
    log(QString("📊 Flood Coverage: %1%").arg(floodPercent, 0, 'f', 1));
}









void MainWindow::runSWEAnimation()
{
    if (!demReady || !rainReady) {
        log("Load DEM and fetch rainfall first");
        return;
    }

    log("Running SWE animation...");
    ui->swePlayBtn->setEnabled(false);
    sweFrames.clear();
    mapCanvas->clearTWI();
    sweCurrentFrame = 0;
    ui->sweSlider->setValue(0);
    ui->sweTimeLabel->setText("T = 0.0 s");

    double totalSeconds = ui->sweDurationSpin->value();
    engine.setSWEDuration(totalSeconds);
    engine.setRainfall(avgRainfall);
    engine.setCellSize(30.0);
    engine.setManningN(0.035);



    auto future = QtConcurrent::run([=]() {
        std::vector<std::vector<std::vector<float>>> frames;
        double stepSize = totalSeconds / 20.0;
        sweTickIndex = 0;

        for (int step = 1; step <= 20; step++) {
            double stepRainfall = avgRainfall * (step / 20.0);
            engine.setDuration(step * 0.5);
            auto frame = engine.predictFloodBlended(stepRainfall, 0.0);
            frames.push_back(frame);

            // Convert float grid to double for sender

        }
        return frames;
    });

    auto* watcher = new QFutureWatcher<FrameVec>(this);
    connect(watcher,
            &QFutureWatcher<FrameVec>::finished,
            this, [=]() {
                sweFrames = watcher->result();
                watcher->deleteLater();

                if (sweFrames.empty()) {
                    log("SWE: no frames generated");
                    ui->swePlayBtn->setEnabled(true);
                    return;
                }

                ui->sweSlider->setMaximum(sweFrames.size() - 1);
                ui->sweFrameLabel->setText(
                    "Frame: 0 / " +
                    QString::number(sweFrames.size() - 1));

                log("SWE: " + QString::number(sweFrames.size()) +
                    " frames ready");
                ui->swePlayBtn->setEnabled(true);

                // Show first frame immediately
                onSWEFrame(0);
            });

    watcher->setFuture(future);
}

void MainWindow::onSWEFrame(int frameIndex)
{
    if (sweFrames.empty()) return;
    if (frameIndex < 0 ||
        frameIndex >= (int)sweFrames.size()) return;

    sweCurrentFrame = frameIndex;

    auto& frame = sweFrames[frameIndex];


    if (floodAI && floodAI->isConnected()) {

        std::vector<std::vector<double>> dblFrame;

        for (const auto& row : frame) {

            std::vector<double> dRow;

            for (float v : row)
                dRow.push_back((double)v);

            dblFrame.push_back(dRow);
        }

        floodAI->sendTick(
            frameIndex,
            frameIndex * 0.5,
            dblFrame,
            avgRainfall,
            30.0
            );
    }



    mapCanvas3D->setSWEFrame(frame);
    mapCanvas->clearTWI();
    mapCanvas->setFlood(frame);
    mapCanvas->update();
    QApplication::processEvents(); // force immediate repaint

    double totalSecs = ui->sweDurationSpin->value();
    double elapsed   = totalSecs *
                     (frameIndex + 1.0) / sweFrames.size();

    ui->sweSlider->blockSignals(true);
    ui->sweSlider->setValue(
        (frameIndex * 1000) / (sweFrames.size() - 1));
    ui->sweSlider->blockSignals(false);

    ui->sweTimeLabel->setText(
        "T = " + QString::number(elapsed, 'f', 1) + " s");

    ui->sweFrameLabel->setText(
        "Frame: " + QString::number(frameIndex) +
        " / " + QString::number(sweFrames.size() - 1));

    // Max depth this frame
    float maxD = 0;
    for (auto& r : frame)
        for (float v : r)
            maxD = std::max(maxD, v);

    ui->sweMaxDepthLabel->setText(
        "Max depth: " +
        QString::number(maxD, 'f', 3) + " m");



    if (frameIndex == (int)sweFrames.size() - 1) {
        QTimer::singleShot(500, this, &MainWindow::fetchLatestSnapshotAndUpdate);
    }
}


void MainWindow::runSatelliteSync()
{
    QString obsPath =
        QFileDialog::getOpenFileName(
            this,
            "Select Observed Flood TIFF",
            "",
            "GeoTIFF (*.tif *.tiff)"
            );

    if (obsPath.isEmpty())
        return;

    log("Starting satellite synchronization...");

    try
    {
        satLoop->runSync(obsPath);
    }
    catch (...)
    {
        log("❌ Satellite sync crashed");
    }
}






void MainWindow::updateAIRiskMarkers()
{
    if (demGrid.empty() || latestAgentRisks.empty()) return;

    int rows = demGrid.size();
    int cols = demGrid[0].size();
    int nSplits = 6;
    int rowStep = rows / nSplits;
    int colStep = cols / nSplits;

    // Get all region agents from API to match IDs to grid positions
    // For now use same 6x6 grid layout as clusterer
    std::vector<RiskMarker> markers;
    int idx = 0;

    for (int i = 0; i < nSplits && idx < (int)latestAgentRisks.size(); i++) {
        for (int j = 0; j < nSplits && idx < (int)latestAgentRisks.size(); j++) {

            int centRow = i * rowStep + rowStep / 2;
            int centCol = j * colStep + colStep / 2;

            centRow = std::min(centRow, rows - 1);
            centCol = std::min(centCol, cols - 1);

            float elev = demGrid[centRow][centCol];


            float horizontalScale = 100.0f / std::max(rows, cols);
            float x = (centCol - cols / 2.0f) * horizontalScale;
            float z = (centRow - rows / 2.0f) * horizontalScale;
            float y = (elev - 256.0f) * 0.5f + 8.0f;

            const AgentRisk& risk = latestAgentRisks[idx];

            RiskMarker marker;
            marker.worldPos  = QVector3D(x, y, z);
            marker.row       = centRow;
            marker.col       = centCol;
            marker.depth     = 0.0f;
            marker.riskLevel = risk.riskInt;
            marker.regionId = risk.regionId;
            switch (risk.riskInt) {
            case 2:
                marker.color = QVector4D(1.0f, 0.0f, 0.5f, 1.0f);
                break;
            case 1:
                marker.color = QVector4D(0.0f, 0.8f, 1.0f, 1.0f);
                break;
            default:
                marker.color = QVector4D(0.6f, 0.0f, 1.0f, 1.0f);
                break;
            }

            markers.push_back(marker);
            idx++;
        }
    }

    mapCanvas3D->setAIRiskMarkers(markers);

    log(QString("AI: updated %1 region risk markers").arg(markers.size()));
}




void MainWindow::fetchLatestSnapshotAndUpdate()
{
    QNetworkRequest req{QUrl("http://127.0.0.1:8000/ingest/latest")};
    QNetworkReply* reply = netManager->get(req);

    connect(reply, &QNetworkReply::finished, this, [=]() {
        if (reply->error() != QNetworkReply::NoError) {
            reply->deleteLater();
            return;
        }

        QJsonObject resp = QJsonDocument::fromJson(reply->readAll()).object();
        reply->deleteLater();

        QJsonObject regionRisks = resp["region_risks"].toObject();
        if (regionRisks.isEmpty()) return;

        std::vector<AgentRisk> risks;
        for (const QString& id : regionRisks.keys()) {
            QString level = regionRisks[id].toString();
            int riskInt = 0;
            if (level == "medium") riskInt = 1;
            else if (level == "high" || level == "critical") riskInt = 2;
            risks.push_back({id, level, 0.0, riskInt});
        }

        latestAgentRisks = risks;
        updateAIRiskMarkers();
    });
}



void MainWindow::fetchAgentDetail(const QString& regionId)
{
    QNetworkRequest req{
        QUrl("http://127.0.0.1:8000/agents/" + regionId)
    };
    QNetworkReply* reply = netManager->get(req);

    connect(reply, &QNetworkReply::finished, this, [=]() {
        if (reply->error() != QNetworkReply::NoError) {
            reply->deleteLater();
            return;
        }

        QJsonObject data = QJsonDocument::fromJson(
                               reply->readAll()).object();
        reply->deleteLater();

        QString peakRisk  = data["peak_risk"].toString();
        QString trend     = data["flood_trend"].toString();

        QJsonArray recent = data["recent_observations"].toArray();
        double maxDepth = 0.0;
        double meanDepth = 0.0;

        if (!recent.isEmpty()) {
            QJsonObject latest = recent.last().toObject();
            QJsonObject floodStats = latest["flood_stats"].toObject();
            maxDepth  = floodStats["max"].toDouble();
            meanDepth = floodStats["mean"].toDouble();
        }

        QString msg =
            "<div style='border-left:4px solid #b84cff;"
            "background:#1e1e1e;padding:6px;margin:6px 0;'>"
            "<b style='color:#b84cff;'>AI AGENT REPORT</b><br>"
            "<span style='color:#aaa;'>Region:</span> "
            "<span style='color:white;'>" + regionId.left(8) + "...</span><br>"
                                 "<span style='color:#aaa;'>Peak Risk:</span> "
                                 "<span style='color:#ff9800;'>" + peakRisk.toUpper() + "</span><br>"
                                   "<span style='color:#aaa;'>Trend:</span> "
                                   "<span style='color:white;'>" + trend + "</span><br>"
                      "<span style='color:#aaa;'>Max Depth:</span> "
                      "<span style='color:#4caf50;'>" + QString::number(maxDepth, 'f', 3) + " m</span><br>"
                                                  "<span style='color:#aaa;'>Mean Depth:</span> "
                                                  "<span style='color:#4caf50;'>" + QString::number(meanDepth, 'f', 3) + " m</span>"
                                                   "</div>";

        log(msg);
    });
}







void MainWindow::onCascadeReportClicked()
{
    if (floodGrid.empty() && sweFrames.empty()) {
        log("Run simulation first before generating cascade report or the SWE simulation");
        return;
    }


    std::vector<std::vector<float>> lastFrame;
    if (!sweFrames.empty()) {
        lastFrame = sweFrames.back();
    } else {
        lastFrame = floodGrid;
    }

    int rows = lastFrame.size();
    int cols = rows > 0 ? lastFrame[0].size() : 0;

    float maxDepth = 0.0f;
    for (auto& r : lastFrame)
        for (float v : r)
            maxDepth = std::max(maxDepth, v);


    float elevRange = demMaxElev - demMinElev;
    float diagDist  = std::sqrt(rows*rows + cols*cols) * 30.0f;
    float slopeAngle = std::atan(elevRange / diagDist) * 180.0f / M_PI;

    // Saturation proxy — flooded cell ratio from last frame
    int floodedCells = 0;
    int totalCells   = rows * cols;
    for (auto& r : lastFrame)
        for (float v : r)
            if (v > 0.05f) floodedCells++;

    float saturation = (float)floodedCells / totalCells;



    float maxLocalSlope = 0.0f;
    for (int i = 0; i < (int)demGrid.size() - 1; i++) {
        for (int j = 0; j < (int)demGrid[0].size() - 1; j++) {
            float dz_row = std::abs(demGrid[i+1][j] - demGrid[i][j]);
            float dz_col = std::abs(demGrid[i][j+1] - demGrid[i][j]);
            float localSlope = std::atan(std::max(dz_row, dz_col) / 30.0f)
                               * 180.0f / M_PI;
            maxLocalSlope = std::max(maxLocalSlope, localSlope);
        }
    }



    QJsonObject simState;
    simState["soil_saturation"]         = saturation;
    simState["slope_angle_deg"]         = maxLocalSlope;
    simState["slope_area_m2"]           = (double)(rows * cols * 30 * 30);
    simState["rainfall_mm"]             = avgRainfall;
    simState["channel_width_m"]         = 20.0;
    simState["channel_depth_m"]         = maxDepth * 2.0;
    simState["upstream_flow_m3s"]       = maxDepth * avgRainfall * 0.5;
    simState["lake_rise_rate_m_per_hr"] = maxDepth / ui->sweDurationSpin->value() * 3600.0;
    simState["manning_n"]               = 0.035;
    simState["channel_slope"]           = elevRange / diagDist;

    // Region from lat/lon bounds already loaded
    QString regionId = QString("%1_%2")
                           .arg(GminLat, 0, 'f', 4)
                           .arg(GminLon, 0, 'f', 4);

    QJsonObject body;
    body["sim_state"]  = simState;
    body["region_id"]  = regionId;
    body["timestep"]   = (int)sweFrames.size() - 1;


    QNetworkRequest req{QUrl("http://127.0.0.1:8000/cascade/analyze")};
    req.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");

    QNetworkReply* reply = netManager->post(
        req, QJsonDocument(body).toJson());

    connect(reply, &QNetworkReply::finished, this, [=]() {
        if (reply->error() != QNetworkReply::NoError) {
            log("Cascade API error: " + reply->errorString());
            reply->deleteLater();
            return;
        }

        QByteArray data = reply->readAll();
        reply->deleteLater();

        QString savePath = QFileDialog::getSaveFileName(
            this, "Save Cascade Report", "cascade_report.pdf",
            "PDF Files (*.pdf)");

        if (savePath.isEmpty()) return;

        // Save JSON temporarily then call Python generator
        QString jsonPath = savePath + ".tmp.json";
        QFile f(jsonPath);
        if (f.open(QIODevice::WriteOnly)) {
            f.write(data);
            f.close();
        }

        QProcess* proc = new QProcess(this);
        proc->start("python", {
                                  "C:/Users/Lenovo/Desktop/Nerolith Cortex/FLOOD-AI/pdf.py",
                                  jsonPath,
                                  savePath
                              });

        connect(proc, QOverload<int,QProcess::ExitStatus>
                ::of(&QProcess::finished),
                this, [=](int code, QProcess::ExitStatus) {
                    QFile::remove(jsonPath);
                    if (code == 0)
                        log("Cascade report saved: " + savePath);
                    else
                        log("PDF generation failed.");
                    proc->deleteLater();
                });
    });
}



void MainWindow::onSurrogateAnalysisClicked()
{
    if (!demReady) {
        log("⚠ Generate DEM first");
        return;
    }

    if (floodGrid.empty()) {
        log("⚠ Run simulation first before Surrogate Analysis");
        return;
    }

    bool ok;
    int nScenarios = QInputDialog::getInt(
        this, "NeroSurrogate Batch Analysis",
        "Number of rainfall scenarios to analyze:\n(10mm/hr to 150mm/hr will be swept)",
        100, 10, 500, 10, &ok);
    if (!ok) return;

    log(QString("🤖 Running %1 surrogate scenarios...").arg(nScenarios));
    log(QString("🔍 DEM: %1×%2 | Rainfall range: 10–150 mm/hr")
            .arg(demGrid.size())
            .arg(demGrid.empty() ? 0 : demGrid[0].size()));

    float demMin = demMinElev;
    float demMax = demMaxElev;
    float trainMin = 44.26f;
    float trainMax = 106.23f;

    QJsonArray demArray;
    for (const auto& row : demGrid) {
        QJsonArray rowArr;
        for (float v : row) {
            float scaled = trainMin + (v - demMin) /
                                          (demMax - demMin + 1e-6f) * (trainMax - trainMin);
            rowArr.append((double)scaled);
        }
        demArray.append(rowArr);
    }

    QJsonObject body;
    body["dem"]         = demArray;
    body["n_scenarios"] = nScenarios;
    body["physics_single_ms"] = lastSimulationMs;
    body["rain_min"]    = 10.0;
    body["rain_max"]    = 150.0;
    body["duration_hr"] = 6.0;
    body["dTheta"]      = 0.3;
    body["manning_n"]   = 0.035;
    body["cell_size_m"] = 30.0;

    QNetworkRequest req{QUrl("http://127.0.0.1:8000/surrogate/batch")};
    req.setHeader(QNetworkRequest::ContentTypeHeader, "application/json");
    req.setTransferTimeout(120000);

    QNetworkReply* reply = netManager->post(req, QJsonDocument(body).toJson());

    connect(reply, &QNetworkReply::finished, this, [=]() {
        if (reply->error() != QNetworkReply::NoError) {
            log("❌ Surrogate batch error: " + reply->errorString());
            reply->deleteLater();
            return;
        }

        QByteArray raw = reply->readAll();
        reply->deleteLater();

        QJsonObject resp = QJsonDocument::fromJson(raw).object();

        double totalMs   = resp["total_ms"].toDouble();
        double avgMs     = resp["avg_ms_per_scenario"].toDouble();
        double physSec   = resp["physics_est_total_s"].toDouble();
        double speedup   = resp["speedup_x"].toDouble();
        double maxDepth  = resp["max_depth_overall"].toDouble();
        double critThr   = resp.contains("critical_threshold_mm") && !resp["critical_threshold_mm"].isNull()
                             ? resp["critical_threshold_mm"].toDouble() : -1.0;
        double highThr   = resp.contains("high_threshold_mm") && !resp["high_threshold_mm"].isNull()
                             ? resp["high_threshold_mm"].toDouble() : -1.0;
        int nSc          = resp["n_scenarios"].toInt();

        QString thresholdInfo = "";
        if (critThr > 0)
            thresholdInfo = QString(" | ⚠ CRITICAL at %1 mm/hr").arg(critThr, 0, 'f', 1);
        else if (highThr > 0)
            thresholdInfo = QString(" | HIGH risk at %1 mm/hr").arg(highThr, 0, 'f', 1);

        QString result =
            "<div style='border-left:4px solid #00e5ff;"
            "background:#1e1e1e;padding:8px;margin:6px 0;'>"
            "<b style='color:#00e5ff;'>🤖 NEROSURROGATE BATCH ANALYSIS</b><br>"
            "<span style='color:#aaa;'>Scenarios:</span> "
            "<span style='color:white;'>" + QString::number(nSc) + "</span> | "
                                     "<span style='color:#aaa;'>Surrogate time:</span> "
                                     "<span style='color:#3fb950;'>" + QString::number(totalMs/1000.0, 'f', 1) + "s</span> | "
                                                          "<span style='color:#aaa;'>Physics est:</span> "
                                                          "<span style='color:#f85149;'>" + (physSec > 3600
                   ? QString::number(physSec/3600.0, 'f', 1) + "hrs"
                   : QString::number(physSec, 'f', 0) + "s") + "</span><br>"
              "<span style='color:#aaa;'>Speedup:</span> "
              "<span style='color:#00e5ff;'>" + QString::number(speedup, 'f', 0) + "x faster</span> | "
                                                 "<span style='color:#aaa;'>Per scenario:</span> "
                                                 "<span style='color:#3fb950;'>" + QString::number(avgMs, 'f', 1) + " ms</span><br>"
                                               "<span style='color:#aaa;'>Max depth:</span> "
                                               "<span style='color:#ff9800;'>" + QString::number(maxDepth, 'f', 3) + " m</span>"
            + thresholdInfo +
            "</div>";

        log(result);

        QString savePath = QFileDialog::getSaveFileName(
            this, "Save Surrogate Report", "surrogate_batch_report.pdf",
            "PDF Files (*.pdf)");
        if (savePath.isEmpty()) return;

        QJsonObject reportData = resp;
        reportData["rainfall_mm"]  = avgRainfall;
        reportData["region_lat"]   = (GminLat + GmaxLat) / 2.0;
        reportData["region_lon"]   = (GminLon + GmaxLon) / 2.0;
        reportData["timestamp"]    = QDateTime::currentDateTime().toString(Qt::ISODate);

        QString jsonPath = savePath + ".tmp.json";
        QFile f(jsonPath);
        if (f.open(QIODevice::WriteOnly)) {
            f.write(QJsonDocument(reportData).toJson());
            f.close();
        }

        QProcess* proc = new QProcess(this);
        proc->start("python", {
                                  "C:/Users/Lenovo/Desktop/Nerolith Cortex/FLOOD-AI/surrogate_pdf.py",
                                  jsonPath,
                                  savePath
                              });

        connect(proc, QOverload<int, QProcess::ExitStatus>
                ::of(&QProcess::finished),
                this, [=](int code, QProcess::ExitStatus) {
                    QFile::remove(jsonPath);
                    if (code == 0)
                        log("✅ Surrogate batch report saved: " + savePath);
                    else
                        log("❌ PDF generation failed.");
                    proc->deleteLater();
                });
    });
}
