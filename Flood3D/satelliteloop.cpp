#include "satelliteloop.h"
#include "floodengineclient.h"

#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonValue>
#include <QDebug>
#include <QDir>


#include <gdal.h>
#include <gdal_priv.h>
#include <ogr_spatialref.h>

SatelliteLoop::SatelliteLoop(FloodEngineClient* engine, QObject* parent)
    : QObject(parent), m_engine(engine)
{
    GDALAllRegister();
}


bool SatelliteLoop::exportSimGrid(const QString& outPath)
{
    qDebug() << "EXPORT 1";

    if (!m_engine) {
        qDebug() << "Engine null";
        return false;
    }

    if (!m_engine->isReady()) {
        qDebug() << "Engine not ready";
        return false;
    }

    qDebug() << "EXPORT 2";

  auto grid = this->m_latestGrid;

    if (grid.empty()) {
        qDebug() << "Flood grid empty";
        return false;
    }

    int rows = grid.size();
    int cols = grid[0].size();

    qDebug() << "Grid rows:" << rows;
    qDebug() << "Grid cols:" << cols;

    if (rows <= 0 || cols <= 0) {
        qDebug() << "Invalid grid dimensions";
        return false;
    }

    qDebug() << "EXPORT 3";

    std::vector<float> flat;
    flat.resize(rows * cols);

    for (int i = 0; i < rows; i++)
    {
        if (grid[i].size() != cols) {
            qDebug() << "Row size mismatch at row:" << i;
            return false;
        }

        for (int j = 0; j < cols; j++)
        {
            flat[i * cols + j] = grid[i][j];
        }
    }

    qDebug() << "EXPORT 4";

    GDALDriver* driver =
        GetGDALDriverManager()->GetDriverByName("GTiff");

    if (!driver) {
        qDebug() << "GTiff driver null";
        return false;
    }

    qDebug() << "EXPORT 5";

    GDALDataset* ds = driver->Create(
        outPath.toStdString().c_str(),
        cols,
        rows,
        1,
        GDT_Float32,
        nullptr
        );

    if (!ds) {
        qDebug() << "Dataset creation failed";
        return false;
    }

    qDebug() << "EXPORT 6";

    GDALRasterBand* band = ds->GetRasterBand(1);

    if (!band) {
        qDebug() << "Band null";
        GDALClose(ds);
        return false;
    }

    qDebug() << "EXPORT 7";

    CPLErr err = band->RasterIO(
        GF_Write,
        0,
        0,
        cols,
        rows,
        flat.data(),
        cols,
        rows,
        GDT_Float32,
        0,
        0
        );

    if (err != CE_None) {
        qDebug() << "RasterIO failed";
        GDALClose(ds);
        return false;
    }

    qDebug() << "EXPORT 8";

    GDALClose(ds);

    qDebug() << "EXPORT DONE";

    return true;
}
// ─────────────────────────────────────────────────────────
// STEP 2 — Python script run karo QProcess se
// ─────────────────────────────────────────────────────────
void SatelliteLoop::runSync(const QString& obsTiffPath)
{
    qDebug() << "SAT 1: runSync started";

    if (m_busy) {
        qDebug() << "SAT ERROR: already busy";
        emit logMessage("[SatLoop] Already syncing, please wait");
        return;
    }

    if (!m_engine) {
        qDebug() << "SAT ERROR: engine nullptr";
        emit syncFailed("Engine pointer is null");
        return;
    }

    if (!m_engine->isReady()) {
        qDebug() << "SAT ERROR: engine not ready";
        emit syncFailed(
            "Engine not ready — load DEM and run simulation first");
        return;
    }

    if (obsTiffPath.isEmpty()) {
        qDebug() << "SAT ERROR: observed TIFF empty";
        emit syncFailed("Observed TIFF path empty");
        return;
    }

    m_busy = true;

    emit syncStarted();
    emit logMessage("[SatLoop] Satellite sync started...");

    QString workDir =
        m_workDir.isEmpty()
            ? QDir::currentPath()
            : m_workDir;

    qDebug() << "Working dir:" << workDir;

    m_simTiff = workDir + "/sat_sim_export.tif";
    m_divTiff = workDir + "/sat_divergence.tif";

    qDebug() << "Sim TIFF:" << m_simTiff;
    qDebug() << "Div TIFF:" << m_divTiff;

    // ---------------------------------------------------
    // STEP 1 — Export simulation raster
    // ---------------------------------------------------

    qDebug() << "SAT 2: exporting sim TIFF";

    bool ok = false;

    try
    {
        ok = exportSimGrid(m_simTiff);
    }
    catch (...)
    {
        qDebug() << "SAT CRASH: exportSimGrid exception";
        ok = false;
    }

    if (!ok)
    {
        qDebug() << "SAT EXPORT FAILED";

        m_busy = false;

        emit syncFailed("Failed to export simulation grid");
        return;
    }

    qDebug() << "SAT 3: export finished";

    // ---------------------------------------------------
    // STEP 2 — Launch Python divergence engine
    // ---------------------------------------------------

    qDebug() << "SAT 4: launching python";

    m_process = new QProcess(this);

    connect(m_process,
            QOverload<int, QProcess::ExitStatus>::of(
                &QProcess::finished),
            this,
            &SatelliteLoop::onProcessFinished);

    connect(m_process,
            &QProcess::errorOccurred,
            this,
            &SatelliteLoop::onProcessError);

    QStringList args = {
        m_scriptPath,
        m_simTiff,
        obsTiffPath,
        m_divTiff,
        QString::number(m_manningN),
        QString::number(m_Ks)
    };

    qDebug() << "Python path:" << m_pythonPath;
    qDebug() << "Script path:" << m_scriptPath;
    qDebug() << "Observed TIFF:" << obsTiffPath;

    qDebug() << "Arguments:";
    qDebug() << args;

    emit logMessage("[SatLoop] Running divergence engine...");
    emit logMessage(
        "[SatLoop] CMD: " +
        m_pythonPath + " " + args.join(" "));

    try
    {
        m_process->start(m_pythonPath, args);

        qDebug() << "SAT 5: process started";
    }
    catch (...)
    {
        qDebug() << "SAT CRASH: QProcess start exception";

        m_busy = false;

        emit syncFailed("Failed to start Python process");
        return;
    }
}
// ─────────────────────────────────────────────────────────
// STEP 3 — Python output parse karo
// ─────────────────────────────────────────────────────────
void SatelliteLoop::onProcessFinished(int exitCode, QProcess::ExitStatus status)
{
    QByteArray raw = m_process->readAllStandardOutput();
    QByteArray err = m_process->readAllStandardError();

    m_process->deleteLater();
    m_process = nullptr;
    m_busy    = false;

    if (!err.isEmpty())
        emit logMessage("[SatLoop] Python stderr: " + QString(err));

    if (exitCode != 0 || status != QProcess::NormalExit) {
        emit syncFailed("Python script failed — exit code: "
                        + QString::number(exitCode));
        return;
    }

    // Parse JSON
    m_result = parseJson(raw);

    if (!m_result.ok) {
        emit syncFailed("Failed to parse divergence engine output");
        return;
    }

    emit logMessage(QString("[SatLoop] Divergence: %1%")
                        .arg(m_result.max_divergence * 100.0, 0, 'f', 1));

    // Step 4 — Recalibration agar zaroorat hai
    if (m_result.needs_recalibration) {
        emit logMessage(QString("[SatLoop] Recalibrating — cause: %1")
                            .arg(m_result.cause));
        emit logMessage(QString("[SatLoop] New Manning n: %1")
                            .arg(m_result.new_manning_n));

        // Seedha DLL mein daal do
        m_engine->setManningN(m_result.new_manning_n);
        m_engine->setSoilParams(m_result.new_soil_Ks, 11.0, 0.3);

        // Manning n update karo local copy bhi
        m_manningN = m_result.new_manning_n;
        m_Ks       = m_result.new_soil_Ks;

        emit logMessage("[SatLoop] Parameters updated — rerun simulation");
    } else {
        emit logMessage("[SatLoop] Simulation within threshold — no recalibration needed");
    }

    emit syncFinished(m_result);
}

void SatelliteLoop::onProcessError(QProcess::ProcessError error)
{
    qDebug() << "SAT ERROR TRIGGERED";
    qDebug() << "Process error code:" << error;

    if (m_process)
    {
        qDebug() << "STDOUT:";
        qDebug() << m_process->readAllStandardOutput();

        qDebug() << "STDERR:";
        qDebug() << m_process->readAllStandardError();
    }

    m_busy = false;

    if (m_process)
    {
        m_process->deleteLater();
        m_process = nullptr;
    }

    QString msg;

    switch (error) {
    case QProcess::FailedToStart:
        msg = "Python not found — check python path";
        break;

    case QProcess::Crashed:
        msg = "Python script crashed";
        break;

    default:
        msg = "QProcess error: " + QString::number(error);
    }

    qDebug() << "Final error msg:" << msg;

    emit syncFailed(msg);
}
// ─────────────────────────────────────────────────────────
// JSON Parser
// ─────────────────────────────────────────────────────────
SatelliteResult SatelliteLoop::parseJson(const QByteArray& raw)
{
    SatelliteResult res;

    // Raw mein sirf JSON part nikalo
    // (Python warnings ignore karo upar se)
    int jsonStart = raw.indexOf('{');
    if (jsonStart < 0) return res;

    QByteArray jsonOnly = raw.mid(jsonStart);

    QJsonParseError parseErr;
    QJsonDocument doc = QJsonDocument::fromJson(jsonOnly, &parseErr);

    if (parseErr.error != QJsonParseError::NoError) {
        qDebug() << "[SatLoop] JSON parse error:" << parseErr.errorString();
        return res;
    }

    QJsonObject root = doc.object();

    if (root["status"].toString() != "ok") return res;

    QJsonObject stats = root["stats"].toObject();

    res.ok                  = true;
    res.max_divergence      = stats["max_divergence"].toDouble();
    res.under_predict_pct   = stats["under_predict_pct"].toDouble();
    res.over_predict_pct    = stats["over_predict_pct"].toDouble();
    res.correct_pct         = stats["correct_pct"].toDouble();
    res.total_cells         = stats["total_cells"].toInt();
    res.needs_recalibration = root["needs_recalibration"].toBool();
    res.cause               = root["cause"].toString();
    res.divergence_tiff     = root["divergence_tiff"].toString();

    QJsonObject params      = root["recalib_params"].toObject();
    res.new_manning_n       = params["manning_n"].toDouble(m_manningN);
    res.new_soil_Ks         = params["soil_Ks"].toDouble(m_Ks);

    return res;
}


void SatelliteLoop::setFloodGrid(
    const std::vector<std::vector<float>>& g)
{
    this->m_latestGrid = g;
}
