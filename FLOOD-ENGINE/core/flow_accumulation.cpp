#include<iostream>
#include "raster.h"
#include<utility>
using namespace std;
pair<int ,int> Raster :: nextCell(int i , int j , int dir) const  {
    int rows = getRows();
    int cols = getCols();
    
 if(dir == -1){
    return {-1 , -1};
 }
     static int di[8] = { 0,  1,  1,  1,  0, -1, -1, -1 };
    static int dj[8] = { 1,  1,  0, -1, -1, -1,  0,  1 };

 int ni = i + di[dir];
 int nj = j + dj[dir];

if(ni < 0 || nj < 0 || ni >= rows || nj >= cols){
    return {-1 , -1};
}


 return {ni , nj};
}

int Raster :: flowAccumulator(int i , int j , vector<vector<int>>& fa , vector<vector<bool>>& visited) const{
if(visited[i][j]){
    return fa[i][j];
}
visited[i][j] = true;
int sum = 1;
auto neigh = getNeighbours(i , j);
for(auto &p : neigh){
 int r = p.first;
 int c = p.second;


 int dir = getFlowDirection(r , c);
 auto nxt = nextCell(r , c , dir);
 if(nxt.first == i && nxt.second == j){
    sum = sum + flowAccumulator(r , c , fa , visited);
 }
}
fa[i][j] = sum;
return sum;
}

   vector<vector<int>> Raster::computeFlowAccumulation() const {
        if (flowAccCached) {
            return cachedFlowAcc;
        }

        vector<vector<int>> fa(rows, vector<int>(cols, 0));
        vector<vector<bool>> visited(rows, vector<bool>(cols, false));

        for (int i = 0; i < rows; i++) {
            for (int j = 0; j < cols; j++) {
                if (!visited[i][j]) {
                    flowAccumulator(i, j, fa, visited);
                }
            }
        }

        cachedFlowAcc = fa;
        flowAccCached = true;
        return cachedFlowAcc;
    }

