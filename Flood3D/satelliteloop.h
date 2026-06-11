#pragma once

#include <QObject>
#include <QProcess>
#include <QString>
#include <vector>

// Forward declare — FloodEngineClient include nahi karna yahan
class FloodEngineClient;

struct SatelliteResult
{
    bool   ok                 = false;
    double max_divergence     = 0.0;
    double under_predict_pct  = 0.0;
    double over_predict_pct   = 0.0;
    double correct_pct        = 0.0;
    int    total_cells        = 0;
    bool   needs_recalibration= false;
    QString cause             = "";
    double new_manning_n      = 0.035;
    double new_soil_Ks        = 10.0;
    QString divergence_tiff   = "";
};

class SatelliteLoop : public QObject
{
    Q_OBJECT

public:
    void setFloodGrid(
        const std::vector<std::vector<float>>& g);
    explicit SatelliteLoop(FloodEngineClient* engine, QObject* parent = nullptr);

    // Main call — ye button click pe chalega
    void runSync(const QString& obsTiffPath);

    // Current sim grid ko GeoTIFF mein export karta hai
    bool exportSimGrid(const QString& outPath);

    // Getters
    SatelliteResult lastResult() const { return m_result; }
    bool            isBusy()    const { return m_busy; }

    // Params — Qt side se set karo
    void setCurrentManningN (double n)  { m_manningN = n; }
    void setCurrentKs       (double ks) { m_Ks = ks;      }
    void setPythonPath      (const QString& p) { m_pythonPath = p; }
    void setScriptPath      (const QString& p) { m_scriptPath = p; }
    void setWorkDir         (const QString& p) { m_workDir = p;    }

signals:
    void syncStarted   ();
    void syncFinished  (SatelliteResult result);
    void syncFailed    (QString reason);
    void logMessage    (QString msg);

private slots:
    void onProcessFinished(int exitCode, QProcess::ExitStatus status);
    void onProcessError   (QProcess::ProcessError error);

private:
     std::vector<std::vector<float>> m_latestGrid;
    SatelliteResult parseJson(const QByteArray& raw);

    FloodEngineClient* m_engine     = nullptr;
    QProcess*          m_process    = nullptr;
    SatelliteResult    m_result;
    bool               m_busy       = false;

    // Params
    double  m_manningN   = 0.035;
    double  m_Ks         = 10.0;

    // Paths
    QString m_pythonPath = "C:/Users/Lenovo/AppData/Local/Programs/Python/Python312/python.exe";
    QString m_scriptPath = "D:/Documents/Flood3D/satellite/divergence_engine.py";
    QString m_workDir    = "";
    QString m_simTiff    = "";
    QString m_divTiff    = "";
};
