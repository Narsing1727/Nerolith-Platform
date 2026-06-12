#pragma once
#include <vector>

class RandomForest{
public:
bool loadModel(const char* path);
double predict(const std::vector<double>& features) const;
private:
    struct Node {
        bool isLeaf;
        int feature;
        double threshold;
        int left, right;
        double value;
    };

    std::vector<std::vector<Node>> trees;
};