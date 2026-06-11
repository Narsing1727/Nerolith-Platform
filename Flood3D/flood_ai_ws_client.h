#pragma once
#include <QObject>
#include <QWebSocket>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QTimer>
#include <vector>

struct AgentRisk {
    QString regionId;
    QString riskLevel;
    double  floodMaxM;
    int     riskInt;
};

class FloodAIWSClient : public QObject
{
    Q_OBJECT
public:
    explicit FloodAIWSClient(QObject* parent = nullptr)
        : QObject(parent)
    {
        socket = new QWebSocket(QString(), QWebSocketProtocol::VersionLatest, this);

        connect(socket, &QWebSocket::connected,
                this, [this]() {
                    emit logMessage("FLOOD-AI WebSocket connected");
                });

        connect(socket, &QWebSocket::disconnected,
                this, [this]() {
                    emit logMessage("FLOOD-AI WebSocket disconnected — retrying...");
                    QTimer::singleShot(3000, this, &FloodAIWSClient::connectToServer);
                });

        connect(socket, &QWebSocket::textMessageReceived,
                this, &FloodAIWSClient::onMessage);
    }

    void connectToServer(const QString& url = "ws://127.0.0.1:8000/ws") {
        wsUrl = url;
        socket->open(QUrl(wsUrl));
    }

signals:
    void agentRisksUpdated(const std::vector<AgentRisk>& risks);
    void logMessage(const QString& msg);

private slots:
    void connectToServer() {
        socket->open(QUrl(wsUrl));
    }

    void onMessage(const QString& raw) {
        QJsonDocument doc = QJsonDocument::fromJson(raw.toUtf8());
        if (!doc.isObject()) return;

        QJsonObject obj = doc.object();
        QString type = obj["type"].toString();

        if (type != "tick") return;

        QJsonObject regionRisks = obj["region_risks"].toObject();
        QJsonArray  alerts      = obj["alerts"].toArray();

        std::vector<AgentRisk> risks;

        for (const QString& regionId : regionRisks.keys()) {
            QString level = regionRisks[regionId].toString();

            int riskInt = 0;
            if (level == "medium")   riskInt = 1;
            else if (level == "high" || level == "critical") riskInt = 2;

            risks.push_back({regionId, level, 0.0, riskInt});
        }

        if (!risks.empty())
            emit agentRisksUpdated(risks);

        if (!alerts.isEmpty())
            emit logMessage(
                QString("FLOOD-AI: %1 alert(s) fired this tick")
                    .arg(alerts.size()));
    }

private:
    QWebSocket* socket;
    QString     wsUrl;
};
