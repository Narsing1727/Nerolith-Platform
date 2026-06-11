#pragma once

#include <QObject>

#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QNetworkReply>

#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>

#include <QString>
#include <QDebug>

#include <vector>

class FloodAISender : public QObject
{
    Q_OBJECT

public:

    explicit FloodAISender(QObject* parent = nullptr)
        : QObject(parent)
    {
    }

    bool connectToAI(const QString& url)
    {
        endpoint = url;

        qDebug() << "FLOOD-AI endpoint:" << endpoint;

        return true;
    }

    bool isConnected() const
    {
        return !endpoint.isEmpty();
    }

    void sendTick(
        int timestep,
        double elapsedSeconds,
        const std::vector<std::vector<double>>& floodGrid,
        double rainfall,
        double cellSize
        )
    {
        if (endpoint.isEmpty())
        {
            qDebug() << "AI endpoint empty";
            return;
        }

        int rows = floodGrid.size();
        int cols = rows > 0 ? floodGrid[0].size() : 0;

        double maxDepth = 0.0;
        int floodedCells = 0;

        QJsonArray floodData;

        for (const auto& row : floodGrid)
        {
            QJsonArray rowArr;

            for (double v : row)
            {
                rowArr.append(v);

                if (v > maxDepth)
                    maxDepth = v;

                if (v > 0)
                    floodedCells++;
            }

            floodData.append(rowArr);
        }

        QJsonObject floodSnap;

        floodSnap["timestep"]           = timestep;
        floodSnap["rows"]               = rows;
        floodSnap["cols"]               = cols;
        floodSnap["cell_size_m"]        = cellSize;
        floodSnap["data"]               = floodData;
        floodSnap["max_depth_m"]        = maxDepth;
        floodSnap["flooded_cell_count"] = floodedCells;

        QJsonObject payload;

        payload["timestep"]        = timestep;
        payload["elapsed_seconds"] = elapsedSeconds;
        payload["flood"]           = floodSnap;
        payload["rainfall_mm"]     = rainfall;

        QByteArray json =
            QJsonDocument(payload)
                .toJson(QJsonDocument::Compact);

        QNetworkRequest req{QUrl(endpoint)};

        req.setHeader(
            QNetworkRequest::ContentTypeHeader,
            "application/json");

        // THREAD SAFE MANAGER
        QNetworkAccessManager* manager =
            new QNetworkAccessManager();

        QNetworkReply* reply =
            manager->post(req, json);

        connect(reply,
                &QNetworkReply::finished,
                [reply, manager]()
                {
                    QByteArray response =
                        reply->readAll();

                    qDebug() << "AI TICK SENT";
                    qDebug() << "AI RESPONSE:" << response;

                    reply->deleteLater();
                    manager->deleteLater();
                });

        connect(reply,
                &QNetworkReply::errorOccurred,
                [reply](QNetworkReply::NetworkError error)
                {
                    qDebug() << "AI NETWORK ERROR:"
                             << error;

                    qDebug() << "ERROR STRING:"
                             << reply->errorString();
                });
    }

private:

    QString endpoint;
};
