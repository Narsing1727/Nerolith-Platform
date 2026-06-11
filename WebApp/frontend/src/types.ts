export interface TelemetryMetrics {
  rainfall: number;      // mm/hr
  soilMoisture: number;  // %
  waterLevel: number;    // meters
  flowVelocity: number;  // m/s
  slopeSteepness: number; // degrees
  terrainType: string;
}

export interface SimulationRegion {
  id: string;
  name: string;
status: string;
  statusColor: string;
  image: string;
  description: string;
  lat: number;
  lng: number;
  baseMetrics: TelemetryMetrics;
}

export interface TechnicalSystem {
  id: string;
  title: string;
  category: string;
  iconName: string;
  description: string;
  linkText?: string;
}

export interface WaitlistState {
  email: string;
  loading: boolean;
  success: boolean;
  message: string;
  error?: string;
}
