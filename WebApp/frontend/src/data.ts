import type { SimulationRegion, TechnicalSystem } from "./types";
export const REGIONS: SimulationRegion[] = [
  {
    id: "chalakudy-kerala",
    name: "Chalakudy River Basin, Kerala",
    status: "Validation Case Study · IIT Roorkee 2025",
    statusColor: "text-emerald-600 bg-emerald-50 border-emerald-200",
    image: "kerala.png",
    description: "Primary validation basin for Nerolith. August 2018 extreme flood event — 35 dams opened simultaneously, 2346.6mm rainfall, 42% above LPA. Validated against Sentinel-1 SAR ground truth.",
    lat: 10.3529,
    lng: 76.5120,
    baseMetrics: {
      rainfall: 2347,
      soilMoisture: 96,
      waterLevel: 8.5,
      flowVelocity: 3.4,
      slopeSteepness: 14,
      terrainType: "Tropical River Basin"
    }
  },
  {
    id: "brahmaputra-assam",
    name: "Brahmaputra Basin, Assam",
    status: "Research Phase · Northeast India",
    statusColor: "text-blue-600 bg-blue-50 border-blue-200",
    image: "assam.png",
    description: "Highly braided river system with compound riverine and flash flood dynamics across a 580,000 km² catchment. Targeted for next validation cycle.",
    lat: 26.1445,
    lng: 91.7362,
    baseMetrics: {
      rainfall: 68,
      soilMoisture: 91,
      waterLevel: 11.2,
      flowVelocity: 4.1,
      slopeSteepness: 6,
      terrainType: "Braided Floodplain"
    }
  },
  {
    id: "godavari-andhra",
    name: "Godavari Delta, Andhra Pradesh",
    status: "In Scoping · Coastal Flood Risk",
    statusColor: "text-amber-600 bg-amber-50 border-amber-200",
    image: "Andhra.png",
    description: "Coastal delta system exposed to compounded riverine flooding and cyclonic storm surge. High structural damage risk across dense agricultural zones.",
    lat: 16.9174,
    lng: 81.7500,
    baseMetrics: {
      rainfall: 48,
      soilMoisture: 83,
      waterLevel: 7.0,
      flowVelocity: 2.6,
      slopeSteepness: 3,
      terrainType: "Coastal River Delta"
    }
  },
  {
    id: "yamuna-delhi",
    name: "Yamuna Corridor, Delhi-NCR",
    status: "Planned · Urban Flood Intelligence",
    statusColor: "text-purple-600 bg-purple-50 border-purple-200",
    image: "Delhi.png",
    description: "Urban flash and riverine compound flood modeling across a 3.2M population exposure zone. High-resolution 10m grid targeting critical infrastructure triage.",
    lat: 28.6139,
    lng: 77.2090,
    baseMetrics: {
      rainfall: 31,
      soilMoisture: 74,
      waterLevel: 5.0,
      flowVelocity: 1.9,
      slopeSteepness: 2,
      terrainType: "Urban Riverine Corridor"
    }
  }
];