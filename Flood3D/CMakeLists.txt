cmake_minimum_required(VERSION 3.16)
project(Flood3D VERSION 0.1 LANGUAGES CXX)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
find_package(QT NAMES Qt6 Qt5 REQUIRED COMPONENTS
    Widgets
    Network
    OpenGL
    OpenGLWidgets
    Concurrent
    Quick
    QuickControls2
    QuickWidgets
)
find_package(Qt${QT_VERSION_MAJOR} REQUIRED COMPONENTS
    Widgets
    Network
    OpenGL
    OpenGLWidgets
    Concurrent
    Quick
    QuickControls2
    QuickWidgets
)
set(PROJECT_SOURCES
    main.cpp
    mainwindow.cpp
    mainwindow.h
    mainwindow.ui
)
file(GLOB_RECURSE SOURCES_3D
    "3D/*.cpp"
    "3D/*.h"
)
if(${QT_VERSION_MAJOR} GREATER_EQUAL 6)
    qt_add_executable(Flood3D
        MANUAL_FINALIZATION
        ${PROJECT_SOURCES}
        ${SOURCES_3D}
        dialog.h
        dialog.cpp
        dialog.ui
        mapcanvas2d.h
        mapcanvas2d.cpp
        rainfall_dialog.h
        rainfall_dialog.cpp
        rainfall_dialog.ui
        floodengineclient.h
        floodengineclient.cpp
        mapcanvas3d.h
        mapcanvas3d.cpp
        intro_window.h
        intro_window.cpp
        intro_window.ui
        flood_ai_sender.h
        satelliteloop.cpp
        satelliteloop.h
        fragment.frag
        vertex.vert
        shaders.qrc
        resources.qrc
        WelcomeWindow.h
        qml.qrc
    )
else()
    if(ANDROID)
        add_library(Flood3D SHARED ${PROJECT_SOURCES})
    else()
        add_executable(Flood3D ${PROJECT_SOURCES})
    endif()
endif()
set(GDAL_INCLUDE_DIR "D:/OSGeoW4/include")
set(GDAL_LIBRARY "D:/OSGeoW4/lib/gdal_i.lib")
target_include_directories(Flood3D PRIVATE
    ${GDAL_INCLUDE_DIR}
    ${CMAKE_SOURCE_DIR}/3D/headers
)
target_link_libraries(Flood3D
    PRIVATE
    Qt${QT_VERSION_MAJOR}::Widgets
    Qt${QT_VERSION_MAJOR}::Network
    Qt${QT_VERSION_MAJOR}::OpenGL
    Qt${QT_VERSION_MAJOR}::OpenGLWidgets
    Qt${QT_VERSION_MAJOR}::Concurrent
    Qt${QT_VERSION_MAJOR}::Quick
    Qt${QT_VERSION_MAJOR}::QuickWidgets
       Qt${QT_VERSION_MAJOR}::QuickControls2
    ${GDAL_LIBRARY}
)
if(${QT_VERSION} VERSION_LESS 6.1.0)
    set(BUNDLE_ID_OPTION MACOSX_BUNDLE_GUI_IDENTIFIER com.example.Flood3D)
endif()
set_target_properties(Flood3D PROPERTIES
    ${BUNDLE_ID_OPTION}
    MACOSX_BUNDLE_BUNDLE_VERSION ${PROJECT_VERSION}
    MACOSX_BUNDLE_SHORT_VERSION_STRING ${PROJECT_VERSION_MAJOR}.${PROJECT_VERSION_MINOR}
    MACOSX_BUNDLE TRUE
    WIN32_EXECUTABLE TRUE
)
include(GNUInstallDirs)
install(TARGETS Flood3D
    BUNDLE DESTINATION .
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
if(QT_VERSION_MAJOR EQUAL 6)
    qt_finalize_executable(Flood3D)
endif()
