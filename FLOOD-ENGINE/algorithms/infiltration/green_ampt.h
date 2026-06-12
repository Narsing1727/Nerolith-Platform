#pragma once

double infiltrationRate(double Ks, double psi, double dTheta, double F);

double cumulativeInfiltration(double Ks, double psi, double dTheta, double t, int iterations = 10);
