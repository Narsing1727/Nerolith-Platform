import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    width: 1024
    height: 768
    color: "#2b2d30"

    signal newProjectRequested()
    signal openProjectRequested()

    readonly property color bg:          "#2b2d30"
    readonly property color bgCard:      "#313438"
    readonly property color bgSidebar:   "#1e1f22"
    readonly property color bdColor:     "#3c3f41"
    readonly property color accent:      "#4e9fea"
    readonly property color textPrimary: "#dfe1e5"
    readonly property color textMuted:   "#9da0a8"
    readonly property color textDim:     "#6b6e73"
    readonly property color selectedBg:  "#2e436e"

    property int selectedNav: 0

    RowLayout {
        anchors.fill: parent
        spacing: 0

        // Sidebar Panel
        Rectangle {
            id: sidebar
            Layout.preferredWidth: 220
            Layout.fillHeight: true
            color: root.bgSidebar

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                // Sidebar Header
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 52
                    color: "transparent"

                    Rectangle {
                        width: parent.width
                        height: 1
                        color: root.bdColor
                        anchors.bottom: parent.bottom
                    }

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 16
                        anchors.rightMargin: 16
                        spacing: 8



                        Text {
                            text: "Nerolith"
                            color: root.textPrimary
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                            Layout.alignment: Qt.AlignVCenter
                        }
                    }
                }

                Item { Layout.preferredHeight: 6 }

                // Sidebar Navigation Items
                Repeater {
                    model: [
                        { label: "Home",             icon: "⌂",  idx: 0 },
                        { label: "New Project",      icon: "＋", idx: 1 },
                        { label: "Open Project",     icon: "▤",  idx: 2 },
                        { label: "Recent Projects",  icon: "◷",  idx: 3 },
                        { label: "",                 icon: "",   idx: -1 },
                        { label: "Examples",         icon: "⬡",  idx: 4 },
                        { label: "Tutorials",        icon: "🎓", idx: 5 },
                        { label: "Documentation",    icon: "☰",  idx: 6 },
                        { label: "",                 icon: "",   idx: -1 },
                        { label: "Settings",         icon: "⚙",  idx: 7 },
                        { label: "Extensions",       icon: "⬡",  idx: 8 }
                    ]

                    delegate: Item {
                        Layout.fillWidth: true
                        Layout.preferredHeight: modelData.label === "" ? 10 : 32

                        Rectangle {
                            anchors.fill: parent
                            color: root.selectedNav === modelData.idx && modelData.idx >= 0
                                   ? root.selectedBg : "transparent"

                            Rectangle {
                                width: 3
                                height: parent.height
                                color: root.selectedNav === modelData.idx && modelData.idx >= 0
                                       ? root.accent : "transparent"
                            }

                            RowLayout {
                                anchors.fill: parent
                                anchors.leftMargin: 16
                                anchors.rightMargin: 8
                                spacing: 8
                                visible: modelData.label !== ""



                                Text {
                                    text: modelData.label
                                    color: root.selectedNav === modelData.idx
                                           ? root.textPrimary : root.textMuted
                                    font.pixelSize: 13
                                    Layout.fillWidth: true
                                    Layout.alignment: Qt.AlignVCenter
                                }
                            }

                            MouseArea {
                                anchors.fill: parent
                                enabled: modelData.label !== ""
                                hoverEnabled: true
                                onEntered: parent.color = root.selectedNav === modelData.idx
                                           ? root.selectedBg : "#2a2b2f"
                                onExited: parent.color = root.selectedNav === modelData.idx
                                          ? root.selectedBg : "transparent"
                                onClicked: {
                                    if (modelData.idx >= 0) {
                                        root.selectedNav = modelData.idx
                                        if (modelData.idx === 1) root.newProjectRequested()
                                        if (modelData.idx === 2) root.openProjectRequested()
                                    }
                                }
                            }
                        }
                    }
                }

                Item { Layout.fillHeight: true }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: root.bdColor
                }

                // License Section
                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 52

                    ColumnLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 16
                        anchors.topMargin: 10
                        anchors.bottomMargin: 10
                        spacing: 2

                        RowLayout {
                            spacing: 6
                            Layout.fillWidth: true

                            Text { text: "✓"; color: "#5fad56"; font.pixelSize: 13; font.weight: Font.Bold }
                            Text { text: "License: Professional"; color: root.textMuted; font.pixelSize: 12 }
                        }

                        Text {
                            text: "Manage License"
                            color: root.accent
                            font.pixelSize: 12
                            leftPadding: 20

                            MouseArea {
                                anchors.fill: parent
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {}
                            }
                        }
                    }
                }
            }
        }

        // Main Panel Section
        ColumnLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 0

                // Main Content Column
                ScrollView {
                    id: mainScrollView
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    contentWidth: availableWidth
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    topPadding: 24
                    bottomPadding: 24
                    leftPadding: 44
                    rightPadding: 44

                    ColumnLayout {
                        width: mainScrollView.availableWidth
                        spacing: 0

                        Text {
                            text: "Welcome to Nerolith Flood Sim"
                            color: root.textPrimary
                            font.pixelSize: 22
                            font.weight: Font.DemiBold
                        }

                        Item { Layout.preferredHeight: 4 }

                        Text {
                            text: "Professional flood simulation and analysis for engineers and consultants."
                            color: root.textMuted
                            font.pixelSize: 13
                        }

                        Item { Layout.preferredHeight: 24 }

                        Text {
                            text: "Get Started"
                            color: root.textPrimary
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                        }

                        Item { Layout.preferredHeight: 10 }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 14

                            // "New Project" Card
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 110
                                color: cardNewHover ? "#383b3e" : root.bgCard
                                border.color: cardNewHover ? root.accent : root.bdColor
                                border.width: 1
                                radius: 4

                                property bool cardNewHover: false

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 18
                                    spacing: 14

                                    Rectangle {
                                        Layout.preferredWidth: 36
                                        Layout.preferredHeight: 36
                                        color: "transparent"

                                        Text {
                                            anchors.centerIn: parent
                                            text: "📄"
                                            font.pixelSize: 24
                                        }
                                    }

                                    ColumnLayout {
                                        spacing: 3
                                        Layout.fillWidth: true

                                        Text {
                                            text: "New Project"
                                            color: root.textPrimary
                                            font.pixelSize: 14
                                            font.weight: Font.DemiBold
                                        }

                                        Text {
                                            text: "Create a new flood simulation project from scratch."
                                            color: root.textMuted
                                            font.pixelSize: 12
                                            wrapMode: Text.WordWrap
                                            Layout.fillWidth: true
                                        }
                                    }

                                    Text {
                                        text: "→"
                                        color: root.accent
                                        font.pixelSize: 16
                                        Layout.alignment: Qt.AlignBottom
                                    }
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    hoverEnabled: true
                                    onEntered: parent.cardNewHover = true
                                    onExited: parent.cardNewHover = false
                                    onClicked: root.newProjectRequested()
                                }
                            }

                            // "Open Project" Card
                            Rectangle {
                                Layout.fillWidth: true
                                Layout.preferredHeight: 110
                                color: cardOpenHover ? "#383b3e" : root.bgCard
                                border.color: cardOpenHover ? root.accent : root.bdColor
                                border.width: 1
                                radius: 4

                                property bool cardOpenHover: false

                                RowLayout {
                                    anchors.fill: parent
                                    anchors.margins: 18
                                    spacing: 14

                                    Rectangle {
                                        Layout.preferredWidth: 36
                                        Layout.preferredHeight: 36
                                        color: "transparent"

                                        Text {
                                            anchors.centerIn: parent
                                            text: "📂"
                                            font.pixelSize: 24
                                        }
                                    }

                                    ColumnLayout {
                                        spacing: 3
                                        Layout.fillWidth: true

                                        Text {
                                            text: "Open Project"
                                            color: root.textPrimary
                                            font.pixelSize: 14
                                            font.weight: Font.DemiBold
                                        }

                                        Text {
                                            text: "Open an existing project file."
                                            color: root.textMuted
                                            font.pixelSize: 12
                                        }
                                    }

                                    Text {
                                        text: "→"
                                        color: root.accent
                                        font.pixelSize: 16
                                        Layout.alignment: Qt.AlignBottom
                                    }
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    hoverEnabled: true
                                    onEntered: parent.cardOpenHover = true
                                    onExited: parent.cardOpenHover = false
                                    onClicked: root.openProjectRequested()
                                }
                            }
                        }

                        Item { Layout.preferredHeight: 22 }

                        RowLayout {
                            Layout.fillWidth: true

                            Text {
                                text: "Recent Projects"
                                color: root.textPrimary
                                font.pixelSize: 14
                                font.weight: Font.DemiBold
                            }

                            Item { Layout.fillWidth: true }

                            Text {
                                text: "View All"
                                color: root.accent
                                font.pixelSize: 13
                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                }
                            }
                        }

                        Item { Layout.preferredHeight: 10 }

                        // Recent Projects Table Container
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: recentCol.implicitHeight
                            color: root.bgCard
                            border.color: root.bdColor
                            border.width: 1
                            radius: 4

                            ColumnLayout {
                                id: recentCol
                                anchors.fill: parent
                                spacing: 0

                                Repeater {
                                    model: [
                                        { name: "Riverside_Development.nfp",   path: "C:\\Projects\\Riverside_Development\\Riverside_Development.nfp",   date: "5/22/2024  2:15 PM" },
                                        { name: "Urban_Catchment_Model.nfp",   path: "C:\\Projects\\Urban_Catchment_Model\\Urban_Catchment_Model.nfp",   date: "5/21/2024  10:48 AM" },
                                        { name: "Bridge_Scour_Analysis.nfp",   path: "C:\\Projects\\Bridge_Scour_Analysis\\Bridge_Scour_Analysis.nfp",   date: "5/20/2024  4:32 PM" },
                                        { name: "Coastal_Flood_Risk.nfp",      path: "C:\\Projects\\Coastal_Flood_Risk\\Coastal_Flood_Risk.nfp",          date: "5/19/2024  9:05 AM" },
                                        { name: "Dam_Breach_Study.nfp",        path: "C:\\Projects\\Dam_Breach_Study\\Dam_Breach_Study.nfp",              date: "5/18/2024  3:17 PM" }
                                    ]

                                    delegate: Rectangle {
                                        Layout.fillWidth: true
                                        Layout.preferredHeight: 52
                                        color: rowHover ? "#383b3f" : "transparent"
                                        property bool rowHover: false

                                        Rectangle {
                                            width: parent.width
                                            height: 1
                                            color: root.bdColor
                                            anchors.bottom: parent.bottom
                                            visible: index < 4
                                        }

                                        RowLayout {
                                            anchors.fill: parent
                                            anchors.leftMargin: 14
                                            anchors.rightMargin: 14
                                            spacing: 10

                                            Text {
                                                text: "🗋"
                                                color: root.textDim
                                                font.pixelSize: 14
                                                Layout.alignment: Qt.AlignVCenter
                                            }

                                            ColumnLayout {
                                                spacing: 1
                                                Layout.fillWidth: true
                                                Layout.alignment: Qt.AlignVCenter

                                                Text {
                                                    text: modelData.name
                                                    color: root.textPrimary
                                                    font.pixelSize: 13
                                                    font.family: "Consolas"
                                                    font.weight: Font.Medium
                                                }

                                                Text {
                                                    text: modelData.path
                                                    color: root.textDim
                                                    font.pixelSize: 11
                                                    font.family: "Consolas"
                                                }
                                            }

                                            Text {
                                                text: modelData.date
                                                color: root.textDim
                                                font.pixelSize: 12
                                                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                                            }
                                        }

                                        MouseArea {
                                            anchors.fill: parent
                                            cursorShape: Qt.PointingHandCursor
                                            hoverEnabled: true
                                            onEntered: parent.rowHover = true
                                            onExited: parent.rowHover = false
                                        }
                                    }
                                }
                            }
                        }

                        Item { Layout.preferredHeight: 40 }
                    }
                }

                // Vertical Separator
                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.fillHeight: true
                    color: root.bdColor
                }

                // Right Panel Column (News & Resources)
                ScrollView {
                    id: sideScrollView
                    Layout.preferredWidth: 340
                    Layout.fillHeight: true
                    contentWidth: availableWidth
                    ScrollBar.horizontal.policy: ScrollBar.AlwaysOff
                    topPadding: 24
                    bottomPadding: 24
                    leftPadding: 24
                    rightPadding: 24

                    ColumnLayout {
                        width: sideScrollView.availableWidth
                        spacing: 16

                        // News Panel
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: newsCol.implicitHeight + 28
                            color: root.bgCard
                            border.color: root.bdColor
                            border.width: 1
                            radius: 4

                            ColumnLayout {
                                id: newsCol
                                anchors.fill: parent
                                anchors.margins: 14
                                spacing: 0

                                RowLayout {
                                    Layout.fillWidth: true

                                    Text {
                                        text: "News"
                                        color: root.textPrimary
                                        font.pixelSize: 14
                                        font.weight: Font.DemiBold
                                    }

                                    Item { Layout.fillWidth: true }

                                    Text {
                                        text: "View All"
                                        color: root.accent
                                        font.pixelSize: 12
                                        MouseArea {
                                            anchors.fill: parent
                                            cursorShape: Qt.PointingHandCursor
                                        }
                                    }
                                }

                                Item { Layout.preferredHeight: 10 }

                                Repeater {
                                    model: [
                                        { title: "Nerolith Flood Sim 1.4.0 Released",          date: "5/15/2024", desc: "New 2D hydraulic solver improvements, enhanced mesh tools, and more post-processing capabilities." },
                                        { title: "Training Webinar: 2D Modeling Best Practices", date: "5/10/2024", desc: "Join us for a live webinar on advanced 2D modeling techniques and case study walkthroughs." },
                                        { title: "Import GIS Layers from Online Sources",        date: "5/8/2024",  desc: "You can now import terrain and map data directly from WMS and other online sources." }
                                    ]

                                    delegate: ColumnLayout {
                                        Layout.fillWidth: true
                                        spacing: 0

                                        Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: 1
                                            color: root.bdColor
                                            visible: index > 0
                                        }

                                        Item {
                                            Layout.preferredHeight: index > 0 ? 8 : 0
                                            visible: index > 0
                                        }

                                        RowLayout {
                                            Layout.fillWidth: true
                                            spacing: 8

                                            Text {
                                                text: "●"
                                                color: root.accent
                                                font.pixelSize: 9
                                                Layout.alignment: Qt.AlignTop
                                                topPadding: 3
                                            }

                                            ColumnLayout {
                                                spacing: 2
                                                Layout.fillWidth: true

                                                RowLayout {
                                                    Layout.fillWidth: true

                                                    Text {
                                                        text: modelData.title
                                                        color: root.textPrimary
                                                        font.pixelSize: 13
                                                        font.weight: Font.Medium
                                                        wrapMode: Text.WordWrap
                                                        Layout.fillWidth: true
                                                    }

                                                    Text {
                                                        text: modelData.date
                                                        color: root.textDim
                                                        font.pixelSize: 11
                                                        Layout.alignment: Qt.AlignTop
                                                    }
                                                }

                                                Text {
                                                    text: modelData.desc
                                                    color: root.textMuted
                                                    font.pixelSize: 12
                                                    wrapMode: Text.WordWrap
                                                    Layout.fillWidth: true
                                                }
                                            }
                                        }

                                        Item { Layout.preferredHeight: 8 }
                                    }
                                }
                            }
                        }

                        // Resource Hub Panel
                        Rectangle {
                            Layout.fillWidth: true
                            Layout.preferredHeight: resourceCol.implicitHeight + 28
                            color: root.bgCard
                            border.color: root.bdColor
                            border.width: 1
                            radius: 4

                            ColumnLayout {
                                id: resourceCol
                                anchors.fill: parent
                                anchors.margins: 14
                                spacing: 6

                                Text {
                                    text: "Resource Hub"
                                    color: root.textPrimary
                                    font.pixelSize: 14
                                    font.weight: Font.DemiBold
                                }

                                Item { Layout.preferredHeight: 4 }

                                GridLayout {
                                    Layout.fillWidth: true
                                    columns: 2
                                    columnSpacing: 8
                                    rowSpacing: 6

                                    Repeater {
                                        model: [
                                            { icon: "📖", title: "User Manual",       desc: "Comprehensive software documentation." },
                                            { icon: "🔍", title: "Knowledge Base",    desc: "Search common questions and solutions." },
                                            { icon: "▶",  title: "Video Tutorials",   desc: "Step-by-step video guides." },
                                            { icon: "📁", title: "Example Projects",  desc: "Explore sample projects and datasets." },
                                            { icon: "📋", title: "Release Notes",     desc: "Read the latest changes and improvements." },
                                            { icon: "🎧", title: "Support",           desc: "Get help from our support team." }
                                        ]

                                        delegate: Rectangle {
                                            Layout.fillWidth: true
                                            Layout.preferredHeight: resItemCol.implicitHeight + 8
                                            color: resHover ? "#393b40" : "transparent"
                                            radius: 3
                                            property bool resHover: false

                                            RowLayout {
                                                id: resItemCol
                                                anchors.fill: parent
                                                anchors.margins: 4
                                                spacing: 8

                                                // Text {
                                                //     text: modelData.icon
                                                //     font.pixelSize: 18
                                                //     color: root.accent
                                                //     Layout.preferredWidth: 26
                                                //     Layout.alignment: Qt.AlignVCenter
                                                // }

                                                ColumnLayout {
                                                    spacing: 1
                                                    Layout.fillWidth: true
                                                    Layout.alignment: Qt.AlignVCenter

                                                    Text {
                                                        text: modelData.title
                                                        color: root.textPrimary
                                                        font.pixelSize: 13
                                                        font.weight: Font.Medium
                                                    }

                                                    Text {
                                                        text: modelData.desc
                                                        color: root.textMuted
                                                        font.pixelSize: 11
                                                        wrapMode: Text.WordWrap
                                                        Layout.fillWidth: true
                                                    }
                                                }
                                            }

                                            MouseArea {
                                                anchors.fill: parent
                                                cursorShape: Qt.PointingHandCursor
                                                hoverEnabled: true
                                                onEntered: parent.resHover = true
                                                onExited: parent.resHover = false
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Bottom Separator
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: root.bdColor
            }

            // Status Bar
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 28
                color: root.bgSidebar

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 14
                    anchors.rightMargin: 14
                    spacing: 0

                    Text {
                        text: "Ready"
                        color: root.textMuted
                        font.pixelSize: 12
                        Layout.alignment: Qt.AlignVCenter
                    }

                    Item { Layout.fillWidth: true }

                    Text {
                        text: "v1.4.0 (Build 20240515)"
                        color: root.textDim
                        font.pixelSize: 12
                        Layout.alignment: Qt.AlignVCenter
                    }

                    Item { Layout.preferredWidth: 8 }
                    Rectangle {
                        Layout.preferredWidth: 1
                        Layout.preferredHeight: 16
                        color: root.bdColor
                        Layout.alignment: Qt.AlignVCenter
                    }
                    Item { Layout.preferredWidth: 8 }

                    Text {
                        text: "↻  Check for Updates"
                        color: root.textMuted
                        font.pixelSize: 12
                        Layout.alignment: Qt.AlignVCenter
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                        }
                    }

                    Item { Layout.preferredWidth: 8 }

                    Rectangle {
                        Layout.preferredWidth: 1
                        Layout.preferredHeight: 16
                        color: root.bdColor
                        Layout.alignment: Qt.AlignVCenter
                    }

                    Item { Layout.preferredWidth: 8 }

                    Text {
                        text: "💬  Give Feedback"
                        color: root.textMuted
                        font.pixelSize: 12
                        Layout.alignment: Qt.AlignVCenter
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                        }
                    }
                }
            }
        }
    }
}
