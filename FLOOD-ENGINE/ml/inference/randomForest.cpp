#include "randomForest.h"
#include <fstream>
#include <iostream>

bool RandomForest::loadModel(const char* path)
{
    std::ifstream in(path);
    if (!in.is_open()) {
        std::cerr << "Failed to open RF model file\n";
        return false;
    }

    int numTrees;
    in >> numTrees;

    trees.clear();
    trees.resize(numTrees);

    for (int t = 0; t < numTrees; t++) {
        int nodeCount;
        in >> nodeCount;

        trees[t].resize(nodeCount);

        for (int i = 0; i < nodeCount; i++) {
            char type;
            in >> type;

            if (type == 'L') {
                trees[t][i].isLeaf = true;
                trees[t][i].feature = -1;
                trees[t][i].threshold = 0.0;
                trees[t][i].left = -1;
                trees[t][i].right = -1;
                in >> trees[t][i].value;
            } else {
                trees[t][i].isLeaf = false;
                in >> trees[t][i].feature
                   >> trees[t][i].threshold
                   >> trees[t][i].left
                   >> trees[t][i].right;
                trees[t][i].value = 0.0;
            }
        }
    }

    std::cout << "RF model loaded successfully\n";
    return true;
}

double RandomForest::predict(const std::vector<double>& features) const
{
    double sum = 0.0;

    for (const auto& tree : trees) {
        int idx = 0;

        while (!tree[idx].isLeaf) {
            int f = tree[idx].feature;
            if (features[f] <= tree[idx].threshold)
                idx = tree[idx].left;
            else
                idx = tree[idx].right;
        }

        sum += tree[idx].value;
    }

    return sum / trees.size();
}
