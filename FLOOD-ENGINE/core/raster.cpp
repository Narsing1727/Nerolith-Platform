#include "raster.h"
#include<utility>
#include <iostream>
#include <fstream>
#include <sstream>
#include <queue>
#include <tuple>
#include <cmath>
#include <algorithm>
using namespace std;

Raster::Raster() {
    rows = 0;
    cols = 0;
    

}

bool Raster::loadCSVFile(const string& filename) {
    ifstream iFile(filename);
    cout << "File opened successfully\n";

    if (!iFile.is_open()) {
        cout << "Error opening file"<<endl;
        return false;
    }

    grid.clear();
    string line;

    while (getline(iFile, line)) {
        string temp;
        vector<double> row;
        stringstream ss(line);

        while (getline(ss, temp, ',')) {
            row.push_back(stod(temp));
        }

        if (!row.empty()) {
            grid.push_back(row);
        }
    }

    if (grid.empty()) return false;

    rows = grid.size();
    cols = grid[0].size();
    return true;
}

int Raster::getRows() const {
    return rows;
}

int Raster::getCols() const {
    return cols;
}

double Raster::getMax() const {
    double maxVal = grid[0][0];

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (grid[i][j] > maxVal) {
                maxVal = grid[i][j];
            }
        }
    }
    return maxVal;
}

double Raster::getMin() const {
    double minVal = grid[0][0];

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            if (grid[i][j] < minVal) {
                minVal = grid[i][j];
            }
        }
    }
    return minVal;
}

double Raster::getAverage() const {
    double sum = 0.0;

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            sum += grid[i][j];
        }
    }

    return sum / (rows * cols);
}

void Raster::printGrid() const {
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            cout << grid[i][j] << " ";
        }
        cout << endl;
    }
}


vector<pair<int , int>> Raster :: getNeighbours(int i , int j) const {
       vector<pair<int , int>> neighbours;
           static int di[8] = {-1,-1,-1, 0,0, 1,1,1};
         static int dj[8] = {-1, 0, 1,-1,1,-1,0,1};
    for(int k = 0 ; k<8 ; k++){
        int ni = i + di[k];
        int nj = j + dj[k];
        if(ni>=0 && ni<rows && nj >=0 && nj<cols){
            neighbours.push_back({ni , nj});
        }
    }
    return neighbours;
}

vector<vector<int>> Raster :: RiverGrid() const {
    int threshhold = 3;
    auto fa = computeFlowAccumulation();
    vector<vector<int>>river(rows , vector<int>(cols , 0));
for(int i = 0 ; i<rows ; i++){
    for(int j = 0 ; j<cols ; j++){
        if(fa[i][j] >= threshhold){
            river[i][j] =1;
        }
    }
}
return river;
}
vector<vector<double>> Raster :: FloodDepthGrid(int t) const {
double rainfall = rainTime(t);
auto fa = computeFlowAccumulation();

vector<vector<double>> v(rows , vector<double>(cols , 0.0));
for(int i  = 0 ; i<rows ; i++){
    for(int j  = 0 ; j<cols ; j++){
        v[i][j] = rainfall * fa[i][j];
    }
}
return v;
}

void Raster :: exportCSV(vector<vector<double>>& grid , const string& filename){
    ofstream file(filename);
    if(!file.is_open()){
        cout<<"Error while opening the file";
    }
    int rows = grid.size();
    int cols = grid[0].size();
    file <<"x,y,value\n";


    for(int i = 0 ;i<rows ; i++){
        for(int j= 0; j<cols ; j++){
            file << i+0.5 << "," << -(j+0.5) << "," << grid[i][j]<<"\n";
        }
    }
    file.close();
    cout<<"CSV file exported successfully "<<filename<<endl;
} 
double Raster :: rainTime(int t) const{
    if(t<0 || t>=8){
        return 35.00;
    }
double a[8] = {10.0,20.0,30.0,40.0,50.0,60.0,70.0,80.0};
return a[t];
}

vector<vector<double>> Raster :: gridReturn() const{
    return grid;
}

std::vector<std::vector<double>> Raster :: MLFloodDepthGrid(int t , RandomForest& rf) const{
    

    auto physicsDepth = FloodDepthGrid(t);
    auto flowAcc = computeFlowAccumulation();

    std::vector<std::vector<double>> ml(rows,
        std::vector<double>(cols, 0.0));

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {

            std::vector<double> features = {
                rainTime(t),                  // rain_t
                (t == 0 ? 0 : rainTime(t-1)), // rain_t-1
                (double)flowAcc[i][j],        // flow accumulation
                grid[i][j],                   // elevation
                physicsDepth[i][j]            // physics flood
            };

            ml[i][j] = rf.predict(features);
        }
}
return ml;
}

void Raster::exportGridCSV(
    const std::vector<std::vector<double>>& grid,
    const std::string& filename
) const
{
    std::ofstream file(filename);

    if (!file.is_open()) {
        std::cerr << "Failed to open file: " << filename << std::endl;
        return;
    }

    int rows = grid.size();
    int cols = grid[0].size();

    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            file << grid[i][j];
            if (j < cols - 1)
                file << ",";
        }
        file << "\n";
    }

    file.close();
    std::cout << "Grid exported to " << filename << std::endl;
}
void Raster::loadFromGrid(const std::vector<std::vector<double>>& g) {
    grid          = g;
    rows          = grid.size();
    cols          = grid[0].size();
    flowAccCached = false;
    fillPitsInPlace();
}
 
double Raster::computeSlopeAt(int i, int j, double cellSize) const {
    double dzdx, dzdy;
 
    if (j == 0)           dzdx = (grid[i][j+1] - grid[i][j])   / cellSize;
    else if (j == cols-1) dzdx = (grid[i][j]   - grid[i][j-1]) / cellSize;
    else                  dzdx = (grid[i][j+1] - grid[i][j-1]) / (2.0 * cellSize);
 
    if (i == 0)           dzdy = (grid[i+1][j] - grid[i][j])   / cellSize;
    else if (i == rows-1) dzdy = (grid[i][j]   - grid[i-1][j]) / cellSize;
    else                  dzdy = (grid[i+1][j] - grid[i-1][j]) / (2.0 * cellSize);
 
    return std::sqrt(dzdx * dzdx + dzdy * dzdy);
}
 
// ── Private: Wang & Liu pit filling (modifies grid in place) ────
void Raster::fillPitsInPlace() {
    using Cell = std::tuple<double, int, int>;
    std::priority_queue<Cell, std::vector<Cell>, std::greater<Cell>> open;
    std::vector<std::vector<bool>> closed(rows, std::vector<bool>(cols, false));
 
    static const int DI8[] = {-1,-1,-1, 0, 0, 1, 1, 1};
    static const int DJ8[] = {-1, 0, 1,-1, 1,-1, 0, 1};
 
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            bool border = (i == 0 || i == rows-1 || j == 0 || j == cols-1);
            if (border) {
                open.push({grid[i][j], i, j});
                closed[i][j] = true;
            }
        }
    }
 
    while (!open.empty()) {
        auto [e, i, j] = open.top();
        open.pop();
 
        for (int d = 0; d < 8; d++) {
            int ni = i + DI8[d];
            int nj = j + DJ8[d];
 
            if (ni < 0 || ni >= rows || nj < 0 || nj >= cols) continue;
            if (closed[ni][nj]) continue;
 
            grid[ni][nj] = std::max(grid[ni][nj], e);
            open.push({grid[ni][nj], ni, nj});
            closed[ni][nj] = true;
        }
    }
 
    flowAccCached = false;
}
 
// ── Public: TWI grid ─────────────────────────────────────────────
std::vector<std::vector<double>> Raster::computeTWI(double cellSize) const {
    auto fa = computeFlowAccumulation();
    std::vector<std::vector<double>> twi(rows, std::vector<double>(cols, 0.0));
 
    const double minSlope = 0.001;
 
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            double area  = fa[i][j] * cellSize * cellSize;
            double slope = computeSlopeAt(i, j, cellSize);
            slope = std::max(slope, minSlope);
            twi[i][j] = std::log(area / std::tan(std::atan(slope)));
        }
    }
 
    return twi;
}
 
// ── Public: scale-corrected river detection ──────────────────────
std::vector<std::vector<int>> Raster::RiverGridScaled(
    double cellSize, double minAreaM2
) const {
    auto fa = computeFlowAccumulation();
    std::vector<std::vector<int>> river(rows, std::vector<int>(cols, 0));
 
    for (int i = 0; i < rows; i++) {
        for (int j = 0; j < cols; j++) {
            double drainageArea = fa[i][j] * cellSize * cellSize;
            if (drainageArea >= minAreaM2) {
                river[i][j] = 1;
            }
        }
    }
 
    return river;
}