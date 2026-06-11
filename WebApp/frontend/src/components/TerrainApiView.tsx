import React, { useState, useRef } from "react";
import { motion } from "motion/react";
import {
  ArrowRight,
  Check,
  Copy,
  Terminal,
  Database,
  Brain,
  Layers,
  Compass,
  Cpu,
  Globe,
  AreaChart,
  FileText,
  Play,
  ShieldCheck,
  Activity,
  RefreshCw,
  CheckCircle,
  HelpCircle,
} from "lucide-react";

interface TerrainApiViewProps {
  onScrollToTop: () => void;
  onNavigateToPlatformScreen: () => void;
}

export function TerrainApiView({
  onScrollToTop,
  onNavigateToPlatformScreen,
}: TerrainApiViewProps) {
  const [copied, setCopied] = useState(false);

  const [leafletLoaded, setLeafletLoaded] = useState(false);
  const [minLon, setMinLon] = useState("");
  const [minLat, setMinLat] = useState("");
  const [maxLon, setMaxLon] = useState("");
  const [maxLat, setMaxLat] = useState("");

  const [selectedLayers, setSelectedLayers] = useState<Record<string, boolean>>(
    {
      filled_dem: true,
      flow_direction: true,
      flow_accumulation: true,
      twi: true,
      watershed: true,
      stream_network: true,
      slope: true,
      aspect: true,
      confidence: true,
    },
  );

  const [apiHost, setApiHost] = useState(() => {
    return (
      localStorage.getItem("nerolith_api_host") ||
      "https://your-ngrok-url.ngrok-free.app"
    );
  });
  const [apiKey, setApiKey] = useState(() => {
    return localStorage.getItem("nerolith_api_key") || "YOUR_SECRET_KEY";
  });
  const [apiMode, setApiMode] = useState<"real" | "sandbox">("sandbox");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [jobId, setJobId] = useState<string>("");
  const [jobStatus, setJobStatus] = useState<string>("");
  const [jobProgress, setJobProgress] = useState<number>(0);
  const [terminalLogs, setTerminalLogs] = useState<string[]>([]);
  const [jobMetadata, setJobMetadata] = useState<any>(null);
  const [jobOutputs, setJobOutputs] = useState<any>(null);
  const [errorMessage, setErrorMessage] = useState<string>("");

  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const drawnItemsRef = useRef<any>(null);

  React.useEffect(() => {
    const checkL = () => typeof (window as any).L !== "undefined";
    const checkDraw = () =>
      typeof (window as any).L !== "undefined" &&
      typeof (window as any).L.Control !== "undefined" &&
      typeof (window as any).L.Control.Draw !== "undefined";

    if (checkDraw()) {
      setLeafletLoaded(true);
      return;
    }

    const loadCss = (href: string) => {
      const existing = document.querySelector(`link[href="${href}"]`);
      if (existing) return Promise.resolve();
      return new Promise<void>((resolve, reject) => {
        const link = document.createElement("link");
        link.rel = "stylesheet";
        link.href = href;
        link.crossOrigin = "anonymous";
        link.onload = () => resolve();
        link.onerror = () => reject(new Error(`Failed to load CSS: ${href}`));
        document.head.appendChild(link);
      });
    };

    const loadScript = (src: string, globalObjectCheck: () => boolean) => {
      if (globalObjectCheck()) return Promise.resolve();

      const existing = document.querySelector(
        `script[src="${src}"]`,
      ) as HTMLScriptElement;
      if (existing) {
        return new Promise<void>((resolve) => {
          let attempts = 0;
          const interval = setInterval(() => {
            if (globalObjectCheck()) {
              clearInterval(interval);
              resolve();
            } else {
              attempts++;
              if (attempts > 120) {
                clearInterval(interval);
                resolve();
              }
            }
          }, 50);
        });
      }

      return new Promise<void>((resolve, reject) => {
        const script = document.createElement("script");
        script.src = src;
        script.crossOrigin = "anonymous";
        script.async = true;
        script.onload = () => {
          let attempts = 0;
          const interval = setInterval(() => {
            if (globalObjectCheck()) {
              clearInterval(interval);
              resolve();
            } else {
              attempts++;
              if (attempts > 100) {
                clearInterval(interval);
                resolve();
              }
            }
          }, 30);
        };
        script.onerror = () =>
          reject(new Error(`Failed to load script: ${src}`));
        document.body.appendChild(script);
      });
    };

    Promise.all([
      loadCss(
        "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css",
      ),
      loadScript(
        "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js",
        checkL,
      ),
    ])
      .then(() => {
        return Promise.all([
          loadCss(
            "https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.css",
          ),
          loadScript(
            "https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.4/leaflet.draw.js",
            checkDraw,
          ),
        ]);
      })
      .then(() => {
        if (checkDraw()) {
          setLeafletLoaded(true);
        } else {
          let attempts = 0;
          const interval = setInterval(() => {
            if (checkDraw()) {
              clearInterval(interval);
              setLeafletLoaded(true);
            } else {
              attempts++;
              if (attempts > 30) {
                clearInterval(interval);
                console.error(
                  "Leaflet Draw could not be fully resolved in window.L",
                );
              }
            }
          }, 100);
        }
      })
      .catch((err) => {
        console.error("Failed to load Leaflet resources", err);
      });
  }, []);

  React.useEffect(() => {
    if (!leafletLoaded || !mapContainerRef.current || mapInstanceRef.current)
      return;

    const L = (window as any).L;
    if (!L) return;

    const map = L.map(mapContainerRef.current, {
      center: [20.5937, 78.9629],
      zoom: 5,
      zoomControl: true,
    });

    mapInstanceRef.current = map;

    L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
      {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: "abcd",
        maxZoom: 20,
      },
    ).addTo(map);

    const drawnItems = new L.FeatureGroup();
    map.addLayer(drawnItems);
    drawnItemsRef.current = drawnItems;

    const drawControl = new L.Control.Draw({
      draw: {
        polyline: false,
        polygon: false,
        circle: false,
        marker: false,
        circlemarker: false,
        rectangle: {
          shapeOptions: {
            color: "#0000ff",
            weight: 2,
            fillColor: "#0000ff",
            fillOpacity: 0.15,
          },
        },
      },
      edit: {
        featureGroup: drawnItems,
        remove: true,
      },
    });

    map.addControl(drawControl);

    map.on(L.Draw.Event.CREATED, (e: any) => {
      const layer = e.layer;
      drawnItems.clearLayers();
      drawnItems.addLayer(layer);

      const bounds = layer.getBounds();
      const west = bounds.getWest();
      const south = bounds.getSouth();
      const east = bounds.getEast();
      const north = bounds.getNorth();

      setMinLon(west.toFixed(6));
      setMinLat(south.toFixed(6));
      setMaxLon(east.toFixed(6));
      setMaxLat(north.toFixed(6));
    });

    map.on(L.Draw.Event.DELETED, () => {
      setMinLon("");
      setMinLat("");
      setMaxLon("");
      setMaxLat("");
    });

    setTimeout(() => {
      map.invalidateSize();
    }, 500);

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [leafletLoaded]);

  const selectPreset = (coords: number[]) => {
    const [min_lon, min_lat, max_lon, max_lat] = coords;
    setMinLon(min_lon.toString());
    setMinLat(min_lat.toString());
    setMaxLon(max_lon.toString());
    setMaxLat(max_lat.toString());

    if (mapInstanceRef.current && (window as any).L) {
      const L = (window as any).L;
      const bounds = L.latLngBounds([min_lat, min_lon], [max_lat, max_lon]);

      if (drawnItemsRef.current) {
        drawnItemsRef.current.clearLayers();
        const rect = L.rectangle(bounds, {
          color: "#0000ff",
          weight: 2,
          fillColor: "#0000ff",
          fillOpacity: 0.15,
        });
        drawnItemsRef.current.addLayer(rect);
      }

      mapInstanceRef.current.fitBounds(bounds, { padding: [20, 20] });
    }
  };

  const handleReset = () => {
    if (drawnItemsRef.current) {
      drawnItemsRef.current.clearLayers();
    }
    setMinLon("");
    setMinLat("");
    setMaxLon("");
    setMaxLat("");
  };

  const toggleLayer = (layerKey: string) => {
    setSelectedLayers((prev) => ({
      ...prev,
      [layerKey]: !prev[layerKey],
    }));
  };

  const addLog = (text: string) => {
    const time = new Date().toLocaleTimeString();
    setTerminalLogs((prev) => [...prev, `[${time}] ${text}`]);
  };

  const PRESETS = [
    { name: "Western Ghats (Pune)", coords: [73.68, 18.41, 74.12, 18.89] },
    { name: "Chalakudy River Basin", coords: [76.25, 10.2, 76.65, 10.5] },
    { name: "Himalayan Ridge", coords: [77.1, 31.05, 77.25, 31.15] },
  ];

  const STAGES = [
    { key: "source_selection", label: "source_selection", percent: 5 },
    { key: "fetching_dem", label: "fetching_dem", percent: 15 },
    { key: "datum_normalization", label: "datum_normalization", percent: 25 },
    { key: "void_fill", label: "void_fill", percent: 35 },
    {
      key: "wang_liu_conditioning",
      label: "wang_liu_conditioning",
      percent: 45,
    },
    { key: "flow_routing", label: "flow_routing", percent: 55 },
    { key: "terrain_derivatives", label: "terrain_derivatives", percent: 65 },
    { key: "stream_extraction", label: "stream_extraction", percent: 75 },
    {
      key: "watershed_delineation",
      label: "watershed_delineation",
      percent: 85,
    },
    { key: "confidence_raster", label: "confidence_raster", percent: 90 },
    { key: "packaging_outputs", label: "packaging_outputs", percent: 95 },
    { key: "completed", label: "completed", percent: 100 },
  ];

  const getStageState = (stageKey: string, stagePercent: number) => {
    if (jobStatus === "completed") return "completed";

    const active = STAGES.find((s) => s.percent > jobProgress);
    const activeKey = active ? active.key : "none";

    if (activeKey === stageKey) {
      return "current";
    }
    if (jobProgress >= stagePercent) {
      return "completed";
    }
    return "pending";
  };

  const handleApiHostChange = (val: string) => {
    setApiHost(val);
    localStorage.setItem("nerolith_api_host", val);
  };

  const handleApiKeyChange = (val: string) => {
    setApiKey(val);
    localStorage.setItem("nerolith_api_key", val);
  };

  const runSandboxSimulation = () => {
    const simJobId = "job_sim_" + Math.random().toString(36).substring(2, 9);
    setJobId(simJobId);
    setJobStatus("processing");
    addLog(`[SIMULATOR] Starting UI sandbox simulation. Job ID: ${simJobId}`);

    const stepDuration = 1000;
    let currentStepIndex = 0;

    const steps = [
      {
        name: "source_selection",
        progress: 5,
        log: "Selecting optimal DEM coverage grid... Found CopDEM-30 (100% overlap)",
      },
      {
        name: "fetching_dem",
        progress: 15,
        log: "Downloading raw elevation tiles from Copernicus Imagery API...",
      },
      {
        name: "datum_normalization",
        progress: 25,
        log: "Converting vertical reference from EGM96 Geoid down to WGS84 Ellipsoid...",
      },
      {
        name: "void_fill",
        progress: 35,
        log: "Normalizing data vectors and interpolating 4 void sectors on borders...",
      },
      {
        name: "wang_liu_conditioning",
        progress: 45,
        log: "Running Wang-Liu sink fill/depression remediation routine (1024x1024 matrix)...",
      },
      {
        name: "flow_routing",
        progress: 55,
        log: "Generating Flow Direction maps using multiple flow flow accumulation (MFD)...",
      },
      {
        name: "terrain_derivatives",
        progress: 65,
        log: "Calculating slope values (degrees) and cell aspect headings...",
      },
      {
        name: "stream_extraction",
        progress: 75,
        log: "Extracting stream routing mesh at Strahler Order classification thresholds...",
      },
      {
        name: "watershed_delineation",
        progress: 85,
        log: "Tracing closed watershed boundaries from dynamic pour point coords...",
      },
      {
        name: "confidence_raster",
        progress: 90,
        log: "Assembling confidence indexes (mean accuracy metric: 98.50%)...",
      },
      {
        name: "packaging_outputs",
        progress: 95,
        log: "Packing individual output layers to Cloud-Optimized GeoTIFF format...",
      },
      {
        name: "completed",
        progress: 100,
        log: "All 9 output layers parsed & compressed successfully. Creation complete!",
      },
    ];

    const intervalId = setInterval(() => {
      if (currentStepIndex < steps.length) {
        const step = steps[currentStepIndex];
        setJobProgress(step.progress);
        addLog(
          `[STAGE] ${step.name.toUpperCase()} -> ${step.progress}%: ${step.log}`,
        );
        currentStepIndex++;
      } else {
        clearInterval(intervalId);
        setJobStatus("completed");
        setJobProgress(100);
        setIsSubmitting(false);

        const activeLayers = Object.entries(selectedLayers)
          .filter(([_, enabled]) => enabled)
          .map(([key]) => key);

        setJobMetadata({
          source: "Copernicus DEM 30m / SRTM-1 v3",
          confidence_mean: "0.985 (Excellent)",
          resolution_m: "30 meters",
          lat_range: `[${parseFloat(minLat).toFixed(4)}, ${parseFloat(maxLat).toFixed(4)}]`,
          lon_range: `[${parseFloat(minLon).toFixed(4)}, ${parseFloat(maxLon).toFixed(4)}]`,
        });

        const mockOutputs: Record<string, string> = {};
        activeLayers.forEach((layer) => {
          mockOutputs[layer] = `nerolith_outputs_${simJobId}_${layer}.tif`;
        });
        setJobOutputs(mockOutputs);
        addLog(
          `[SUCCESS] Sandbox pipeline complete. Download outputs loaded below!`,
        );
      }
    }, stepDuration);
  };

  const startPolling = (id: string, host: string) => {
    const pollInterval = setInterval(async () => {
      try {
        addLog(`[POLL] Checking status for Job: ${id}...`);

        const response = await fetch(`${host}/terrain/v1/jobs/${id}`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${apiKey}`,
            "ngrok-skip-browser-warning": "true",
          },
        });

        if (!response.ok) {
          throw new Error(`Server status returned ${response.status}`);
        }

        const data = await response.json();
        const status = data.status || "processing";
        const rawProgress =
          data.percent !== undefined
            ? data.percent
            : data.progress !== undefined
              ? data.progress
              : 50;
        const progress =
          rawProgress <= 1 ? Math.round(rawProgress * 100) : rawProgress;

        setJobStatus(status);
        setJobProgress(progress);

        if (data.log) {
          addLog(`[SERVER] ${data.log}`);
        } else {
          addLog(
            `[POLL] Job Status: ${status.toUpperCase()} | Progress: ${progress}%`,
          );
        }

        if (status === "completed" || status === "success" || progress >= 100) {
          clearInterval(pollInterval);
          setIsSubmitting(false);
          setJobStatus("completed");
          setJobProgress(100);

          setJobMetadata({
            source: data.metadata?.source || "SRTM/Copernicus Mixed Base",
            confidence_mean: data.metadata?.confidence_mean || "0.942",
            resolution_m: data.metadata?.resolution_m || "30m",
            lat_range:
              data.metadata?.lat_range ||
              `[${parseFloat(minLat).toFixed(4)}, ${parseFloat(maxLat).toFixed(4)}]`,
            lon_range:
              data.metadata?.lon_range ||
              `[${parseFloat(minLon).toFixed(4)}, ${parseFloat(maxLon).toFixed(4)}]`,
          });

          setJobOutputs(data.outputs || {});
          addLog(
            `[SUCCESS] Pipeline runs completed. ${Object.keys(data.outputs || {}).length} output layers loaded!`,
          );
        } else if (status === "failed" || status === "error") {
          clearInterval(pollInterval);
          setIsSubmitting(false);
          setJobStatus("failed");
          addLog(`[ERROR] Pipeline tracking reported failure state.`);
          setErrorMessage(
            data.error || "Remote processing failed. Check remote server logs.",
          );
        }
      } catch (err: any) {
        console.error("Polling error", err);
        addLog(`[POLL WARNING] Connection issue: ${err.message || err}`);
      }
    }, 5000);
  };

  const handleAnalyze = async () => {
    setErrorMessage("");
    setJobId("");
    setJobStatus("");
    setJobProgress(0);
    setTerminalLogs([]);
    setJobMetadata(null);
    setJobOutputs(null);

    if (!minLon || !minLat || !maxLon || !maxLat) {
      setErrorMessage(
        "Please select a bounding box rectangle on the map or click a preset first.",
      );
      return;
    }

    const activeLayers = Object.entries(selectedLayers)
      .filter(([_, enabled]) => enabled)
      .map(([key]) => key);

    if (activeLayers.length === 0) {
      setErrorMessage("Please select at least one layer to analyze.");
      return;
    }

    const payload = {
      aoi: {
        type: "bbox",
        coordinates: [
          parseFloat(minLon),
          parseFloat(minLat),
          parseFloat(maxLon),
          parseFloat(maxLat),
        ],
      },
      layers: activeLayers,
      output_crs: "EPSG:4326",
      output_format: "COG",
    };

    setIsSubmitting(true);

    if (apiMode === "sandbox") {
      runSandboxSimulation();
      return;
    }

    addLog(
      "[INIT] Calling real REST API at: " + apiHost + "/terrain/v1/analyze ...",
    );

    try {
      const formattedHost = apiHost.endsWith("/")
        ? apiHost.slice(0, -1)
        : apiHost;
      const response = await fetch(`${formattedHost}/terrain/v1/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey}`,
          "ngrok-skip-browser-warning": "true",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(
          `Server returned HTTP ${response.status}: ${await response.text()}`,
        );
      }

      const data = await response.json();
      const id =
        data.job_id ||
        data.id ||
        "job_" + Math.random().toString(36).substring(2, 9);
      setJobId(id);
      setJobStatus("processing");
      addLog(`[SUCCESS] Pipeline job initialized on server. ID: ${id}`);

      startPolling(id, formattedHost);
    } catch (err: any) {
      console.error(err);
      const msg = err.message || "Unknown error";
      addLog(`[ERROR] Run failed: ${msg}`);
      setErrorMessage(
        `Failed to connect to host: ${apiHost}. Please confirm that your local backend server is running, the ngrok tunnel is active, and CORS is enabled.`,
      );
      setIsSubmitting(false);
    }
  };
  const howItWorksSectionRef = useRef<HTMLDivElement>(null);

  const handleCopyCode = () => {
    const code = `POST https://api.nerolith.in/terrain/v1/analyze

{
  "aoi": {
    "type": "bbox",
    "coordinates": [73.68, 18.41, 74.12, 18.89]
  },
  "layers": [
    "filled_dem",
    "flow_direction",
    "flow_accumulation",
    "twi",
    "watershed",
    "stream_network",
    "slope",
    "confidence"
  ],
  "output_crs": "EPSG:32643",
  "output_format": "COG"
}`;
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const scrollToDocs = () => {
    if (howItWorksSectionRef.current) {
      howItWorksSectionRef.current.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }
  };

  return (
    <div className="space-y-32">
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center pt-8">
        <div className="lg:col-span-7 flex flex-col space-y-6">
          <div>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-50 border border-blue-100 text-[#0000ff] font-mono text-[11px] font-bold tracking-wider uppercase">
              <span className="w-1.5 h-1.5 rounded-full bg-[#0000ff] animate-pulse" />
              Nerolith Terrain · Now in Early Access
            </span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-sans font-semibold tracking-tight text-slate-950 leading-[1.08]">
            Terrain Intelligence. <br />
            <span className="text-[#0000ff]">API-First. Analysis-Ready.</span>
          </h1>

          <p className="text-[13px] text-[#4a5568] leading-relaxed font-sans max-w-xl">
            Stop spending days cleaning DEMs. Send us any coordinates — get back
            hydrologically conditioned terrain, derived layers, and AI-ready
            elevation data in seconds. No GDAL. No datum headaches. No
            preprocessing.
          </p>

          <div className="flex flex-wrap gap-4 pt-2">
            <button
              onClick={onNavigateToPlatformScreen}
              className="bg-[#0000ff] text-white font-sans text-sm font-bold px-7 py-4 hover:bg-[#0000d6] transition-all duration-200 flex items-center gap-2 group cursor-pointer shadow-sm"
            >
              Launch Simulations
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
            </button>
            <a
              href="#documentation"
              onClick={(e) => {
                e.preventDefault();
                scrollToDocs();
              }}
              className="bg-transparent border border-[#cbd2e1] text-slate-950 font-sans text-sm font-bold px-7 py-4 hover:bg-[#f4f5f8]/40 hover:border-slate-400 transition-all duration-200 text-center cursor-pointer"
            >
              View Documentation
            </a>
          </div>

          <div className="pt-4 border-t border-slate-100 max-w-xl">
            <p className="text-[12px] text-slate-550 font-sans leading-relaxed text-slate-500">
              Built on the same physics engine powering Nerolith flood
              simulations across Indian watersheds.
            </p>
          </div>
        </div>

        <div className="lg:col-span-5 relative">
          <div className="absolute -inset-1.5 bg-[#0000ff]/5 rounded-none blur-lg opacity-40" />
          <div className="relative glass-panel rounded-none overflow-hidden border border-slate-200 shadow-md p-2 bg-slate-50">
            <div className="bg-white border border-slate-200/60 p-4 font-mono text-[11px] leading-relaxed text-slate-700 space-y-3">
              <div className="flex justify-between items-center border-b border-slate-100 pb-2">
                <span className="text-[10px] font-bold text-slate-400">
                  INPUT DATA SOURCE CONFIG
                </span>
                <span className="flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#0000ff] opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-[#0000ff]"></span>
                </span>
              </div>
              <p>📍 Latitude: 18.5204° N | Longitude: 73.8567° E</p>
              <p>🛰️ Matching sensor grid maps: CopDEM-30, SRTM-1, ALOS-30</p>
              <p>
                🛡️ Normalization pipeline parameters initialized: EGM96 to WGS84
              </p>
              <hr className="border-dashed border-slate-200" />
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-[10px] text-slate-400">
                  <span>WANG-LIU DEPRESSION REMOVAL</span>
                  <span className="text-[#0000ff]">COMPLETED (4ms)</span>
                </div>
                <div className="w-full bg-slate-100 h-1">
                  <div
                    className="bg-[#0000ff] h-full"
                    style={{ width: "100%" }}
                  ></div>
                </div>
              </div>
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-[10px] text-slate-400">
                  <span>D8/MFD FLOW ROUTING</span>
                  <span className="text-[#0000ff]">COMPLETED (12ms)</span>
                </div>
                <div className="w-full bg-slate-100 h-1">
                  <div
                    className="bg-[#0000ff] h-full"
                    style={{ width: "100%" }}
                  ></div>
                </div>
              </div>
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-[10px] text-slate-400">
                  <span>STREAM NETWORK GEOJSON EXTRACT</span>
                  <span className="text-[#0000ff]">COMPLETED (8ms)</span>
                </div>
                <div className="w-full bg-slate-100 h-1">
                  <div
                    className="bg-[#0000ff] h-full"
                    style={{ width: "100%" }}
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-12 border-t border-slate-100 pt-16">
        <div className="flex flex-col gap-2">
          <span className="font-mono text-[11px] font-bold text-[#0000ff] tracking-widest block uppercase">
            Try Nerolith Terrain · Live
          </span>
          <h2 className="text-3xl font-semibold text-slate-950 tracking-tight font-sans">
            Analyze Any Terrain. Right Now.
          </h2>
          <p className="text-[13px] text-slate-500 max-w-2xl font-sans">
            Define a geographic bounding box directly on the high-performance
            dark vector map or select one of our pre-configured region presets.
            Run real-time grid computations either via standard UI Sandbox
            simulation or by connecting your own live development API endpoints.
          </p>
        </div>

        <div className="bg-slate-50 border border-slate-200 p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <span className="font-mono text-[10px] text-slate-400 uppercase tracking-widest block font-bold">
                API COMPUTE ENVIRONMENT
              </span>
              <h3 className="text-sm font-bold text-slate-900 font-sans">
                Select Pipeline Mode
              </h3>
            </div>

            <div className="flex items-center bg-slate-200 p-1 rounded-[3px] gap-1">
              <button
                type="button"
                onClick={() => setApiMode("sandbox")}
                className={`px-4 py-2 text-xs font-mono font-bold uppercase transition-all rounded-[2px] ${apiMode === "sandbox" ? "bg-white text-[#0000ff] shadow-sm" : "text-slate-600 hover:text-slate-900"}`}
              >
                UI Sandbox Simulation
              </button>
              <button
                type="button"
                onClick={() => setApiMode("real")}
                className={`px-4 py-2 text-xs font-mono font-bold uppercase transition-all rounded-[2px] ${apiMode === "real" ? "bg-white text-[#0000ff] shadow-sm" : "text-slate-600 hover:text-slate-900"}`}
              >
                Real API Connection
              </button>
            </div>
          </div>

          {apiMode === "real" && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-slate-200"
            >
              <div className="space-y-2">
                <label className="block text-[11px] font-mono text-slate-500 uppercase tracking-wider">
                  NGROK TUNNEL HOST URL
                </label>
                <input
                  type="text"
                  value={apiHost}
                  onChange={(e) => handleApiHostChange(e.target.value)}
                  placeholder="https://your-ngrok-url.ngrok-free.app"
                  className="w-full px-4 py-3 bg-white border border-slate-200 text-slate-950 font-mono text-xs focus:ring-1 focus:ring-[#0000ff] focus:outline-none rounded-[3px]"
                />
                <span className="text-[10px] text-slate-400 font-sans block">
                  Runs POST /terrain/v1/analyze against this host.
                </span>
              </div>

              <div className="space-y-2">
                <label className="block text-[11px] font-mono text-slate-500 uppercase tracking-wider">
                  BEARER SECURITY TOKEN (SECRET KEY)
                </label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => handleApiKeyChange(e.target.value)}
                  placeholder="Bearer your-secret-key"
                  className="w-full px-4 py-3 bg-white border border-slate-200 text-slate-950 font-mono text-xs focus:ring-1 focus:ring-[#0000ff] focus:outline-none rounded-[3px]"
                />
                <span className="text-[10px] text-slate-400 font-sans block">
                  Secures outbound analytical pipeline queries.
                </span>
              </div>
            </motion.div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          <div className="lg:col-span-7 space-y-4">
            <span className="font-mono text-[11px] text-[#0000ff] font-bold uppercase tracking-wider block">
              Part 1 — Map Bbox Picker
            </span>

            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs font-mono text-slate-400 mr-1 uppercase">
                Presets:
              </span>
              {PRESETS.map((preset, idx) => (
                <button
                  key={idx}
                  onClick={() => selectPreset(preset.coords)}
                  className="px-3 py-1.5 bg-slate-50 hover:bg-slate-100 text-slate-700 font-sans text-xs border border-slate-200 hover:border-slate-350 transition-all rounded-[3px] font-medium"
                >
                  📍 {preset.name}
                </button>
              ))}
            </div>

            <div className="w-full h-[400px] border border-slate-200 relative group overflow-hidden bg-slate-50 shadow-sm">
              <div ref={mapContainerRef} className="w-full h-full z-0" />

              {!leafletLoaded && (
                <div className="absolute inset-0 bg-slate-50/95 flex flex-col items-center justify-center font-mono text-[11px] text-slate-500 gap-3">
                  <RefreshCw className="w-6 h-6 animate-spin text-[#0000ff]" />
                  <span>INITIALIZING HIGH-PRECISION GL MAP...</span>
                </div>
              )}

              <div className="absolute left-3 bottom-3 z-10 bg-white/95 backdrop-blur-md border border-slate-200 shadow-sm px-3 py-2 text-[10px] font-mono text-slate-600 rounded-[3px]">
                ✏️ Draw a rectangle tool to select coordinates
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-slate-50 border border-slate-200 p-4">
              <div className="space-y-1">
                <label className="block text-[10px] font-mono text-slate-500 uppercase">
                  Min Lon (West)
                </label>
                <input
                  type="text"
                  readOnly
                  value={minLon}
                  placeholder="Not Set"
                  className="w-full bg-white border border-slate-200 p-2 font-mono text-xs text-slate-900 focus:outline-none rounded-[2px]"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-[10px] font-mono text-slate-500 uppercase">
                  Min Lat (South)
                </label>
                <input
                  type="text"
                  readOnly
                  value={minLat}
                  placeholder="Not Set"
                  className="w-full bg-white border border-slate-200 p-2 font-mono text-xs text-slate-900 focus:outline-none rounded-[2px]"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-[10px] font-mono text-slate-500 uppercase">
                  Max Lon (East)
                </label>
                <input
                  type="text"
                  readOnly
                  value={maxLon}
                  placeholder="Not Set"
                  className="w-full bg-white border border-slate-200 p-2 font-mono text-xs text-slate-900 focus:outline-none rounded-[2px]"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-[10px] font-mono text-slate-500 uppercase">
                  Max Lat (North)
                </label>
                <input
                  type="text"
                  readOnly
                  value={maxLat}
                  placeholder="Not Set"
                  className="w-full bg-white border border-slate-200 p-2 font-mono text-xs text-slate-900 focus:outline-none rounded-[2px]"
                />
              </div>
            </div>

            <div className="flex justify-end pt-1">
              <button
                onClick={handleReset}
                className="font-mono text-xs text-slate-500 hover:text-[#0000ff] cursor-pointer flex items-center gap-1.5 uppercase font-bold"
              >
                <RefreshCw className="w-3 h-3" /> Clear Drawn Box
              </button>
            </div>
          </div>

          <div className="lg:col-span-5 space-y-6">
            <div className="space-y-2">
              <span className="font-mono text-[11px] text-[#0000ff] font-bold uppercase tracking-wider block">
                Part 2 — Layer Selector
              </span>
              <p className="text-[12px] text-slate-500 font-sans">
                Select geospatial raster bands to package inside the completed
                COG bundle. All selected by default.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {[
                {
                  key: "filled_dem",
                  label: "filled_dem",
                  desc: "Conditioned DEM",
                },
                {
                  key: "flow_direction",
                  label: "flow_direction",
                  desc: "Flow Direction",
                },
                {
                  key: "flow_accumulation",
                  label: "flow_accumulation",
                  desc: "Flow Accumulation",
                },
                { key: "twi", label: "twi", desc: "TWI" },
                { key: "watershed", label: "watershed", desc: "Watershed" },
                {
                  key: "stream_network",
                  label: "stream_network",
                  desc: "Stream Network",
                },
                { key: "slope", label: "slope", desc: "Slope" },
                { key: "aspect", label: "aspect", desc: "Aspect" },
                { key: "confidence", label: "confidence", desc: "Confidence" },
              ].map((layer) => {
                const isSelected = selectedLayers[layer.key];
                return (
                  <button
                    key={layer.key}
                    onClick={() => toggleLayer(layer.key)}
                    className={`p-3 border font-sans text-xs font-bold text-left cursor-pointer select-none transition-all duration-150 rounded-[3px] flex flex-col justify-between h-[68px] ${
                      isSelected
                        ? "bg-[#0000ff] text-white border-[#0000ff] shadow-sm"
                        : "bg-white text-slate-800 border-slate-200 hover:border-slate-400 hover:bg-slate-50"
                    }`}
                  >
                    <span className="font-mono text-[10px] opacity-80 block uppercase tracking-wide leading-none">
                      {layer.label}
                    </span>
                    <span className="text-xs truncate font-medium mt-1 leading-tight">
                      {layer.desc}
                    </span>
                  </button>
                );
              })}
            </div>

            <div className="space-y-4 pt-4 border-t border-slate-100">
              <span className="font-mono text-[11px] text-[#0000ff] font-bold uppercase tracking-wider block">
                Part 3 — Submit Request
              </span>

<div className="bg-amber-50 border border-amber-200 p-3 rounded-[3px] flex items-start gap-2">
  <span className="text-amber-500 text-sm mt-0.5">⚠️</span>
  <div>
    <p className="text-[11px] font-bold text-amber-800 font-mono uppercase tracking-wide">Processing Time Notice</p>
    <p className="text-[11px] text-amber-700 font-sans mt-0.5">
      Keep your bounding box small (under 0.5° × 0.5°) for fastest results. Large areas may take 2–5 minutes to process. Pipeline runs on your local compute via ngrok.
    </p>
  </div>
</div>

              <button
                onClick={handleAnalyze}
                disabled={isSubmitting}
                className="w-full bg-[#0000ff] hover:bg-[#0000d6] disabled:bg-slate-200 text-white font-sans text-sm font-bold py-4 px-6 transition-all flex items-center justify-center gap-2 rounded-[3px] shadow-sm tracking-wide cursor-pointer"
              >
                {isSubmitting ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    CONSOLIDATING COG COMPILATION...
                  </>
                ) : (
                  <>Analyze Terrain →</>
                )}
              </button>

              {errorMessage && (
                <div className="bg-rose-50 border border-rose-200 p-4 text-xs font-sans text-rose-800 leading-relaxed rounded-[3px]">
                  <strong>⚠️ Pipeline Interruption:</strong> {errorMessage}
                </div>
              )}
            </div>
          </div>
        </div>

        {(jobId || isSubmitting) && (
          <div className="space-y-4 pt-6 border-t border-slate-100">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[11px] text-[#0000ff] font-bold uppercase tracking-wider block">
                Part 4 — Progress Panel
              </span>
              <div className="font-mono text-xs text-slate-500">
                Job ID:{" "}
                <span className="text-[#0000ff] font-bold">{jobId}</span> |
                Status:{" "}
                <span className="font-bold text-slate-800 uppercase">
                  {jobStatus}
                </span>
              </div>
            </div>

            <div className="bg-[#0d1117] border border-slate-800 p-6 font-mono rounded-[3px] overflow-hidden text-slate-350">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4 text-xs font-bold text-slate-500">
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <Terminal className="w-4 h-4" /> LIVE COMPUTE GRID PROTOCOL
                </span>
                <span className="font-mono">{jobProgress}% COMPLETE</span>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                <div className="lg:col-span-5 space-y-2 border-r border-slate-800 lg:pr-8">
                  {STAGES.map((stage) => {
                    const state = getStageState(stage.key, stage.percent);
                    return (
                      <div
                        key={stage.key}
                        className="flex items-center justify-between text-xs"
                      >
                        <div className="flex items-center gap-2">
                          {state === "completed" && (
                            <span
                              className="w-2.5 h-2.5 rounded-full bg-[#0000ff]"
                              title="Completed"
                            />
                          )}
                          {state === "current" && (
                            <span
                              className="w-2.5 h-2.5 rounded-full bg-[#0000ff] animate-ping"
                              title="Active Stage"
                            />
                          )}
                          {state === "pending" && (
                            <span
                              className="w-2.5 h-2.5 rounded-full bg-[#3d444d]"
                              title="Pending"
                            />
                          )}
                          <span
                            className={`${state === "completed" ? "text-slate-200" : state === "current" ? "text-[#0000ff] font-bold" : "text-slate-500"}`}
                          >
                            {stage.key}
                          </span>
                        </div>
                        <span className="text-slate-500">{stage.percent}%</span>
                      </div>
                    );
                  })}
                </div>

                <div className="lg:col-span-7 flex flex-col h-[280px]">
                  <div className="flex-1 overflow-y-auto pr-2 space-y-1.5 scrollbar-thin max-h-[280px]">
                    {terminalLogs.length === 0 ? (
                      <div className="text-slate-600 italic text-[11px]">
                        Connecting stream pipe, awaiting system signals...
                      </div>
                    ) : (
                      terminalLogs.map((log, index) => (
                        <div
                          key={index}
                          className="text-[11px] text-emerald-450 text-[#4ade80] leading-relaxed break-all"
                        >
                          {log}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {jobStatus === "completed" && jobMetadata && (
          <div className="space-y-6 pt-6 border-t border-slate-100">
            <span className="font-mono text-[11px] text-[#0000ff] font-bold uppercase tracking-wider block">
              Part 5 — Download Panel
            </span>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 bg-slate-50 border border-slate-200 p-6 rounded-[3px]">
              <div>
                <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest block font-bold">
                  SOURCE COMPOSITION
                </span>
                <span className="text-sm font-bold text-slate-900 font-sans block mt-1">
                  {jobMetadata.source}
                </span>
              </div>
              <div>
                <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest block font-bold">
                  MEAN MATRIX CONFIDENCE
                </span>
                <span className="text-sm font-bold text-[#0000ff] font-sans block mt-1">
                  {jobMetadata.confidence_mean}
                </span>
              </div>
              <div>
                <span className="text-[10px] font-mono text-slate-400 uppercase tracking-widest block font-bold">
                  SPATIAL RESOLUTION
                </span>
                <span className="text-sm font-bold text-slate-900 font-sans block mt-1">
                  {jobMetadata.resolution_m}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {Object.entries(selectedLayers)
                .filter(([_, enabled]) => enabled)
                .map(([key]) => {
                  const path =
                    jobOutputs?.[key] || `outputs/${jobId}/${key}.tif`;

                  return (
                    <div
                      key={key}
                      className="border border-slate-200 bg-white p-4 flex flex-col justify-between hover:border-slate-300 transition-all rounded-[3px] block"
                    >
                      <div className="space-y-1.5 pb-4">
                        <span className="font-mono text-[9px] font-bold uppercase tracking-widest text-[#0000ff] block leading-none">
                          OUTPUT RASTER DEVICE
                        </span>
                        <h4 className="font-sans font-bold text-[14px] text-slate-900 truncate leading-tight">
                          {key}.tif
                        </h4>
                        <p className="text-[11px] text-slate-450 text-slate-500 font-sans line-clamp-2">
                          Available resolution raster mesh. COG file type,
                          EPSG:4326.
                        </p>
                      </div>

                      <button
                       onClick={() => {
  const fileUrl = `${apiHost}/outputs/${jobId}/${key}.tif`;
  const a = document.createElement("a");
  a.href = fileUrl;
  a.download = `${key}.tif`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}}
                        className="w-full bg-[#0000ff] hover:bg-[#0000d6] text-white text-xs font-bold font-sans py-2 px-3 rounded-[2px] transition-colors flex items-center justify-center gap-1 cursor-pointer"
                      >
                        Download Layer
                      </button>
                    </div>
                  );
                })}
            </div>
          </div>
        )}
      </section>

      <section className="space-y-12">
        <div className="flex flex-col gap-2">
          <span className="font-mono text-[11px] font-bold text-[#0000ff] tracking-widest block uppercase">
            The Problem
          </span>
          <h2 className="text-3xl font-semibold text-slate-950 tracking-tight font-sans">
            Hydrology Engineers Spend More Time Cleaning Data Than Doing
            Science.
          </h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          <div className="lg:col-span-7 space-y-6">
            <div className="font-sans text-[13px] text-[#4a5568] space-y-5 leading-relaxed">
              <p>
                The global terrain data market is valued at{" "}
                <strong className="text-slate-950 font-semibold">
                  $2.26 billion in 2025
                </strong>{" "}
                — and growing at{" "}
                <strong className="text-slate-950 font-semibold">
                  17.2% CAGR
                </strong>{" "}
                toward $9.4 billion by 2034. Every infrastructure project, flood
                model, drainage plan, and site survey depends on elevation data.
              </p>
              <p className="font-semibold text-[#0000ff]">
                Yet the actual workflow is broken.
              </p>
              <p>
                Before a single simulation runs, an engineer must manually
                download hundreds of individual DEM tiles from scattered
                portals, reconcile conflicting vertical datums (EGM96, EGM2008,
                local MSL), fix mixed unit systems (metric and English in the
                same dataset), reproject to the right coordinate system, fill
                voids and spurious pits without destroying real terrain
                features, compute flow direction, accumulate drainage networks,
                and delineate watershed boundaries — entirely by hand.
              </p>
              <p>
                Esri's own research confirms that{" "}
                <strong className="text-slate-950 font-semibold">
                  GIS analysts spend days
                </strong>{" "}
                sifting through data portals, correcting projections, and
                preparing data before any useful analysis begins. For large
                basins, processing a single DEM strip on a compute cluster takes{" "}
                <strong className="text-slate-950 font-semibold">
                  over 48 hours
                </strong>
                . For major watershed studies, engineers routinely handle{" "}
                <strong className="text-slate-950 font-semibold">
                  3,000+ individual DEM tiles
                </strong>{" "}
                with disparate datums and units.
              </p>
              <p>
                The result: weeks of setup for every new study area. Months for
                complex basins. The analysis — the part that actually matters —
                is an afterthought.
              </p>
            </div>
          </div>

          <div className="lg:col-span-5 flex flex-col gap-4">
            <div className="border border-slate-200 bg-slate-50 p-6 flex flex-col justify-between">
              <span className="font-mono text-[10px] text-slate-500 block uppercase tracking-wider mb-2">
                Market Size
              </span>
              <div>
                <span className="text-4xl font-extrabold text-[#0000ff] tracking-tight font-sans block mb-1">
                  $9.4B
                </span>
                <span className="text-[12px] text-slate-600 font-sans block leading-snug">
                  Global DEM market size by 2034 growing at 16.7% CAGR
                </span>
              </div>
            </div>

            <div className="border border-slate-200 bg-slate-50 p-6 flex flex-col justify-between">
              <span className="font-mono text-[10px] text-slate-500 block uppercase tracking-wider mb-2">
                Processing Time
              </span>
              <div>
                <span className="text-4xl font-extrabold text-[#0000ff] tracking-tight font-sans block mb-1">
                  48+ Hours
                </span>
                <span className="text-[12px] text-slate-600 font-sans block leading-snug">
                  Time to process a single custom DEM strip at leading compute
                  centers
                </span>
              </div>
            </div>

            <div className="border border-slate-200 bg-slate-50 p-6 flex flex-col justify-between">
              <span className="font-mono text-[10px] text-slate-500 block uppercase tracking-wider mb-2">
                GIS Bottleneck
              </span>
              <div>
                <span className="text-4xl font-extrabold text-[#0000ff] tracking-tight font-sans block mb-1">
                  Days
                </span>
                <span className="text-[12px] text-slate-600 font-sans block leading-snug">
                  Time GIS analysts spend on preprocessing before real analysis
                  begins (Esri, 2025)
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-12 bg-slate-50 border border-slate-200 p-8 sm:p-12">
        <div className="max-w-3xl space-y-4">
          <span className="font-mono text-[11px] font-bold text-[#0000ff] tracking-widest block uppercase">
            Nerolith Terrain
          </span>
          <h2 className="text-3xl font-semibold text-slate-950 tracking-tight font-sans">
            From Coordinates to Analysis-Ready Terrain in Seconds.
          </h2>
          <p className="text-[#0000ff] text-base font-medium font-sans">
            One API call. Eight derived layers. Zero preprocessing.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-4">
          <div className="text-[13px] text-[#4a5568] leading-relaxed font-sans space-y-4">
            <p>
              Nerolith Terrain is the terrain intelligence layer for developers,
              hydrology teams, and AI agents. You define an area of interest — a
              bounding box, a polygon, or even a plain-text location. We handle
              everything else.
            </p>
          </div>
          <div className="text-[13px] text-[#4a5568] leading-relaxed font-sans space-y-4">
            <p>
              Behind every response, Nerolith's processing engine automatically
              selects the best available source data (SRTM, ALOS AW3D30,
              Copernicus DEM, or your own upload), normalizes vertical and
              horizontal datums, fills voids with hydrologically-aware
              interpolation, reprojects to your target CRS, runs Wang-Liu
              depression filling, computes multi-flow-direction drainage
              networks, and returns a complete, simulation-ready terrain package
              — in seconds, not days.
            </p>
            <p>
              The same engine that recalibrates Nerolith's flood models using
              live Sentinel-1 SAR data is now available to every developer
              through a clean REST API.
            </p>
          </div>
        </div>
      </section>

      <section
        className="space-y-12"
        ref={howItWorksSectionRef}
        id="documentation"
      >
        <div className="flex flex-col gap-2">
          <span className="font-mono text-[11px] font-bold text-[#0000ff] tracking-widest block uppercase">
            How It Works
          </span>
          <h2 className="text-3xl font-semibold text-slate-950 tracking-tight font-sans">
            Three Steps. One Call.
          </h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
          <div className="lg:col-span-5 space-y-8">
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <span className="w-6 h-6 rounded-none bg-[#0000ff] text-white flex items-center justify-center font-mono text-xs font-bold">
                  1
                </span>
                <h3 className="text-base font-bold text-slate-950 font-sans">
                  Define Your Area
                </h3>
              </div>
              <p className="text-[13px] text-[#4a5568] leading-relaxed font-sans pl-9">
                Send a bounding box, GeoJSON polygon, coordinates, or a
                plain-text location. ("Godavari basin upstream of Rajahmundry"
                works too.)
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <span className="w-6 h-6 rounded-none bg-[#0000ff] text-white flex items-center justify-center font-mono text-xs font-bold">
                  2
                </span>
                <h3 className="text-base font-bold text-slate-950 font-sans">
                  We Handle the Preprocessing
                </h3>
              </div>
              <p className="text-[13px] text-[#4a5568] leading-relaxed font-sans pl-9">
                Nerolith automatically fetches the best available DEM source,
                normalizes datums, fills voids, resolves projection conflicts,
                and runs hydrological conditioning — Wang-Liu pit filling, MFD
                flow routing, and stream network extraction.
              </p>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <span className="w-6 h-6 rounded-none bg-[#0000ff] text-white flex items-center justify-center font-mono text-xs font-bold">
                  3
                </span>
                <h3 className="text-base font-bold text-slate-950 font-sans">
                  Receive Analysis-Ready Data
                </h3>
              </div>
              <p className="text-[13px] text-[#4a5568] leading-relaxed font-sans pl-9">
                Get back a full terrain package: conditioned DEM, flow grids,
                watershed boundary, stream network, and derived indices — all as
                Cloud-Optimized GeoTIFF or GeoJSON, ready to plug into HEC-HMS,
                QGIS, ArcGIS, or your own models.
              </p>
            </div>
          </div>

          <div className="lg:col-span-7 space-y-3">
            <div className="bg-slate-900 text-slate-200 border border-slate-800 p-6 rounded-none font-mono text-xs relative overflow-hidden group">
              <div className="absolute right-3 top-3 z-10">
                <button
                  onClick={handleCopyCode}
                  className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-white transition-colors cursor-pointer"
                  title="Copy Code Snippet"
                >
                  {copied ? (
                    <Check className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>
              </div>

              <div className="flex items-center gap-2 text-slate-400 border-b border-slate-800 pb-3 mb-4">
                <Terminal className="w-4 h-4 text-[#0000ff]" />
                <span className="text-[11px] font-bold tracking-wider">
                  REQUEST STREAM TERMINAL
                </span>
              </div>

              <pre className="overflow-x-auto text-[11px] leading-relaxed text-blue-100">
                {`POST https://api.nerolith.in/terrain/v1/analyze

{
  "aoi": {
    "type": "bbox",
    "coordinates": [73.68, 18.41, 74.12, 18.89]
  },
  "layers": [
    "filled_dem",
    "flow_direction",
    "flow_accumulation",
    "twi",
    "watershed",
    "stream_network",
    "slope",
    "confidence"
  ],
  "output_crs": "EPSG:32643",
  "output_format": "COG"
}`}
              </pre>
            </div>
            <div className="flex items-center justify-between font-mono text-[11px] text-slate-500 px-1">
              <span>RESPONSE WINDOW SPEED</span>
              <span className="font-bold text-[#0000ff]">
                RETURNS IN &lt; 30 SECONDS
              </span>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-12">
        <div className="flex flex-col gap-2">
          <span className="font-mono text-[11px] font-bold text-[#0000ff] tracking-widest block uppercase">
            What You Get
          </span>
          <h2 className="text-3xl font-semibold text-slate-950 tracking-tight font-sans">
            Eight Layers. One Request.
          </h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="border border-slate-200 bg-white p-6 flex flex-col justify-between hover:border-[#0000ff] transition-all group">
            <div className="space-y-3">
              <div className="w-8 h-8 bg-blue-50 text-[#0000ff] flex items-center justify-center font-bold font-mono text-sm">
                01
              </div>
              <h3 className="font-sans font-bold text-[15px] text-slate-950 leading-tight group-hover:text-[#0000ff] transition-colors">
                Hydrologically Conditioned DEM
              </h3>
              <p className="text-[13px] text-slate-650 text-slate-600 leading-relaxed font-sans">
                Void-filled, datum-normalized, pit-corrected elevation model.
                Simulation-ready out of the box.
              </p>
            </div>
          </div>

          <div className="border border-slate-200 bg-white p-6 flex flex-col justify-between hover:border-[#0000ff] transition-all group">
            <div className="space-y-3">
              <div className="w-8 h-8 bg-blue-50 text-[#0000ff] flex items-center justify-center font-bold font-mono text-sm">
                02
              </div>
              <h3 className="font-sans font-bold text-[15px] text-slate-950 leading-tight group-hover:text-[#0000ff] transition-colors">
                Flow Direction Grid
              </h3>
              <p className="text-[13px] text-slate-650 text-slate-600 leading-relaxed font-sans">
                D8 and Multi-Flow Direction (MFD) grids. Choose based on terrain
                complexity and model requirements.
              </p>
            </div>
          </div>

          <div className="border border-slate-200 bg-white p-6 flex flex-col justify-between hover:border-[#0000ff] transition-all group">
            <div className="space-y-3">
              <div className="w-8 h-8 bg-blue-50 text-[#0000ff] flex items-center justify-center font-bold font-mono text-sm">
                03
              </div>
              <h3 className="font-sans font-bold text-[15px] text-slate-950 leading-tight group-hover:text-[#0000ff] transition-colors">
                Flow Accumulation
              </h3>
              <p className="text-[13px] text-slate-650 text-slate-600 leading-relaxed font-sans">
                Cell-by-cell drainage counts. The foundation of every watershed
                and stream network derivation.
              </p>
            </div>
          </div>

          <div className="border border-slate-200 bg-white p-6 flex flex-col justify-between hover:border-[#0000ff] transition-all group">
            <div className="space-y-3">
              <div className="w-8 h-8 bg-blue-50 text-[#0000ff] flex items-center justify-center font-bold font-mono text-sm">
                04
              </div>
              <h3 className="font-sans font-bold text-[15px] text-slate-950 leading-tight group-hover:text-[#0000ff] transition-colors">
                Topographic Wetness Index (TWI)
              </h3>
              <p className="text-[13px] text-slate-650 text-slate-600 leading-relaxed font-sans">
                Ln(a / tan β) — the standard index for soil moisture, runoff
                potential, and flood susceptibility mapping.
              </p>
            </div>
          </div>

          <div className="border border-slate-200 bg-white p-6 flex flex-col justify-between hover:border-[#0000ff] transition-all group">
            <div className="space-y-3">
              <div className="w-8 h-8 bg-blue-50 text-[#0000ff] flex items-center justify-center font-bold font-mono text-sm">
                05
              </div>
              <h3 className="font-sans font-bold text-[15px] text-slate-950 leading-tight group-hover:text-[#0000ff] transition-colors">
                Watershed Delineation
              </h3>
              <p className="text-[13px] text-slate-650 text-slate-600 leading-relaxed font-sans">
                GeoJSON watershed boundary for any pour point. Automated,
                accurate, hydrology-consistent.
              </p>
            </div>
          </div>

          <div className="border border-slate-200 bg-white p-6 flex flex-col justify-between hover:border-[#0000ff] transition-all group">
            <div className="space-y-3">
              <div className="w-8 h-8 bg-blue-50 text-[#0000ff] flex items-center justify-center font-bold font-mono text-sm">
                06
              </div>
              <h3 className="font-sans font-bold text-[15px] text-slate-950 leading-tight group-hover:text-[#0000ff] transition-colors">
                Stream Network
              </h3>
              <p className="text-[13px] text-slate-650 text-slate-600 leading-relaxed font-sans">
                Threshold-based channel extraction as GeoJSON. Strahler order
                included.
              </p>
            </div>
          </div>

          <div className="border border-slate-200 bg-white p-6 flex flex-col justify-between hover:border-[#0000ff] transition-all group">
            <div className="space-y-3">
              <div className="w-8 h-8 bg-blue-50 text-[#0000ff] flex items-center justify-center font-bold font-mono text-sm">
                07
              </div>
              <h3 className="font-sans font-bold text-[15px] text-slate-950 leading-tight group-hover:text-[#0000ff] transition-colors">
                Slope + Aspect
              </h3>
              <p className="text-[13px] text-slate-650 text-slate-600 leading-relaxed font-sans">
                Degree and radian slope. Aspect in compass bearing. Essential
                for erosion, landslide, and solar modeling.
              </p>
            </div>
          </div>

          <div className="border border-slate-200 bg-white p-6 flex flex-col justify-between hover:border-[#0000ff] transition-all group">
            <div className="space-y-3">
              <div className="w-8 h-8 bg-blue-50 text-[#0000ff] flex items-center justify-center font-bold font-mono text-sm">
                08
              </div>
              <h3 className="font-sans font-bold text-[15px] text-slate-950 leading-tight group-hover:text-[#0000ff] transition-colors">
                Confidence Raster
              </h3>
              <p className="text-[13px] text-slate-650 text-slate-600 leading-relaxed font-sans">
                Per-pixel source quality score. Know exactly where your data is
                strong and where it is interpolated.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-12">
        <div className="flex flex-col gap-2">
          <span className="font-mono text-[11px] font-bold text-[#0000ff] tracking-widest block uppercase">
            Built for the AI Era
          </span>
          <h2 className="text-3xl font-semibold text-slate-950 tracking-tight font-sans">
            The Terrain Tool for AI Agents.
          </h2>
          <p className="text-[13px] text-slate-500 max-w-2xl font-sans">
            84% of developers are already integrating AI into their workflows
            (Stack Overflow Developer Survey, 2025). As AI agents proliferate,
            they need real-world tools — geospatial tools that actually
            understand terrain.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="border border-slate-200 p-6 bg-white space-y-4">
            <div className="w-10 h-10 bg-blue-50 flex items-center justify-center">
              <Brain className="w-5 h-5 text-[#0000ff]" />
            </div>
            <h3 className="text-base font-bold text-slate-950 font-sans">
              Natural Language Terrain Queries
            </h3>
            <p className="text-[13px] text-[#4a5568] leading-relaxed font-sans">
              Ask in plain English. "Delineate every watershed draining into
              this reservoir." "Find all pour points within 2km of this road."
              "Show me areas with TWI above 8 in this basin." Nerolith parses
              the intent, runs the spatial operation, and returns structured
              geospatial data.
            </p>
          </div>

          <div className="border border-slate-200 p-6 bg-white space-y-4">
            <div className="w-10 h-10 bg-blue-50 flex items-center justify-center">
              <Terminal className="w-5 h-5 text-[#0000ff]" />
            </div>
            <h3 className="text-base font-bold text-slate-950 font-sans">
              MCP Server for AI Agents
            </h3>
            <p className="text-[13px] text-[#4a5568] leading-relaxed font-sans">
              Nerolith Terrain ships as a native MCP (Model Context Protocol)
              server. Any AI agent — Claude, GPT, or your own — can call
              watershed delineation, flow analysis, and terrain conditioning as
              a direct tool. No prompt engineering. No custom wrappers. Plug
              terrain intelligence into your agent in minutes.
            </p>
          </div>

          <div className="border border-slate-200 p-6 bg-white space-y-4">
            <div className="w-10 h-10 bg-blue-50 flex items-center justify-center">
              <Layers className="w-5 h-5 text-[#0000ff]" />
            </div>
            <h3 className="text-base font-bold text-slate-950 font-sans">
              ML-Enhanced Super-Resolution
            </h3>
            <p className="text-[13px] text-[#4a5568] leading-relaxed font-sans">
              Standard free DEMs are 30m resolution. Nerolith's ML layer learns
              local terrain patterns to deliver effective sub-10m resolution
              from open-source inputs — without the cost of proprietary LiDAR
              acquisition.
            </p>
          </div>
        </div>
      </section>

      <section className="space-y-12">
        <div className="flex flex-col gap-2">
          <span className="font-mono text-[11px] font-bold text-[#0000ff] tracking-widest block uppercase">
            Who Uses It
          </span>
          <h2 className="text-3xl font-semibold text-slate-950 tracking-tight font-sans">
            Built for Anyone Who Builds on Terrain.
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Use Case 1 */}
          <div className="border border-slate-200 p-6 bg-slate-50/50">
            <h3 className="font-sans font-bold text-base text-slate-950 mb-2">
              1. Hydrology Consultancies
            </h3>
            <p className="text-[13px] text-[#4a5568] leading-relaxed font-sans">
              Stop spending the first week of every project on DEM
              preprocessing. Get simulation-ready terrain for any watershed in
              India in under a minute. Focus on the model, not the data
              pipeline.
            </p>
          </div>

          <div className="border border-slate-200 p-6 bg-slate-50/50">
            <h3 className="font-sans font-bold text-base text-slate-950 mb-2">
              2. PropTech & Real Estate Platforms
            </h3>
            <p className="text-[13px] text-[#4a5568] leading-relaxed font-sans">
              Add slope analysis, flood-path tracing, and drainage risk scoring
              to any property in your database. One API call per parcel. No GIS
              expertise required.
            </p>
          </div>

          <div className="border border-slate-200 p-6 bg-slate-50/50">
            <h3 className="font-sans font-bold text-base text-slate-950 mb-2">
              3. Infrastructure & EPC Firms
            </h3>
            <p className="text-[13px] text-[#4a5568] leading-relaxed font-sans">
              Site selection, road alignment, drainage design, and retaining
              wall placement all depend on accurate terrain. Get conditioned
              DEMs for any project corridor — fast.
            </p>
          </div>

          <div className="border border-slate-200 p-6 bg-slate-50/50">
            <h3 className="font-sans font-bold text-base text-slate-950 mb-2">
              4. AgriTech Platforms
            </h3>
            <p className="text-[13px] text-[#4a5568] leading-relaxed font-sans">
              TWI, slope, and flow accumulation are the inputs to soil moisture
              modeling, irrigation planning, and waterlogging risk. Build
              terrain intelligence into your precision agriculture workflows.
            </p>
          </div>

          <div className="border border-slate-200 p-6 bg-slate-50/50">
            <h3 className="font-sans font-bold text-base text-slate-950 mb-2">
              5. Climate & Insurance
            </h3>
            <p className="text-[13px] text-[#4a5568] leading-relaxed font-sans">
              Terrain-based flood risk scoring at scale. Assess collateral
              exposure, price parametric products, and meet RBI's climate risk
              disclosure requirements with defensible, physics-grounded data.
            </p>
          </div>

          <div className="border border-slate-200 p-6 bg-slate-50/50">
            <h3 className="font-sans font-bold text-base text-slate-950 mb-2">
              6. AI Agents & LLM Applications
            </h3>
            <p className="text-[13px] text-[#4a5568] leading-relaxed font-sans">
              Use the Nerolith Terrain MCP server to give any AI agent the
              ability to reason about real-world terrain. Watershed awareness,
              drainage logic, and elevation context — as a tool, not a prompt.
            </p>
          </div>
        </div>
      </section>

      <section className="space-y-12">
        <div className="flex flex-col gap-2">
          <span className="font-mono text-[11px] font-bold text-[#0000ff] tracking-widest block uppercase">
            Why Now
          </span>
          <h2 className="text-3xl font-semibold text-slate-950 tracking-tight font-sans">
            A $9 Billion Market with a Preprocessing Problem Nobody Has Solved.
          </h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-7 space-y-5 text-[13px] text-[#4a5568] leading-relaxed font-sans">
            <p>
              The global DEM market is valued at{" "}
              <strong className="text-slate-950 font-semibold">
                $2.26 billion in 2025
              </strong>{" "}
              and growing at{" "}
              <strong className="text-slate-950 font-semibold">
                17.2% CAGR
              </strong>
              . Asia-Pacific alone is projected to reach{" "}
              <strong className="text-slate-950 font-semibold">
                $2 billion by 2028
              </strong>
              , driven by infrastructure expansion, Smart Cities investment, and
              climate adaptation spending across India, Southeast Asia, and
              China.
            </p>
            <p>
              Every project in this market — every flood model, drainage design,
              infrastructure survey, and climate risk assessment — starts with
              the same broken workflow: download raw tiles, fix datums, fill
              voids, reproject, condition, derive. Tools like ArcGIS and QGIS
              handle pieces of this, but none automate the full pipeline. None
              offer it as an API.
            </p>
            <p>
              The raw data is free. The preprocessing expertise is expensive,
              slow, and completely unavailable to developers who aren't trained
              GIS professionals.
            </p>
            <p>
              Nerolith Terrain changes that. We've already built the processing
              engine — the same physics core running flood simulations for
              government disaster response. Now we're opening it to every
              developer, every team, any AI agent that needs to build on
              terrain.
            </p>
          </div>

          <div className="lg:col-span-5 flex flex-col gap-4">
            <div className="border border-slate-200 bg-white p-6">
              <span className="text-3xl font-extrabold text-[#0000ff] font-sans block mb-1">
                $2.26B
              </span>
              <span className="text-[12px] text-slate-500 font-sans uppercase font-mono block">
                Global DEM market in 2025
              </span>
            </div>

            <div className="border border-slate-200 bg-white p-6">
              <span className="text-3xl font-extrabold text-[#0000ff] font-sans block mb-1">
                17.2%
              </span>
              <span className="text-[12px] text-slate-500 font-sans uppercase font-mono block">
                CAGR through 2032
              </span>
            </div>

            <div className="border border-slate-200 bg-white p-6">
              <span className="text-3xl font-extrabold text-[#0000ff] font-sans block mb-1">
                $2B
              </span>
              <span className="text-[12px] text-slate-500 font-sans uppercase font-mono block">
                Asia-Pacific DEM demand projected by 2028
              </span>
            </div>
          </div>
        </div>
      </section>

      <section className="space-y-12 bg-slate-50 border border-slate-200 p-8 sm:p-12">
        <div className="max-w-3xl space-y-4">
          <span className="font-mono text-[11px] font-bold text-[#0000ff] tracking-widest block uppercase">
            Proven Foundation
          </span>
          <h2 className="text-3xl font-semibold text-slate-950 tracking-tight font-sans">
            Not Another Data Portal. An Engine That's Already Running.
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-4">
          <div className="text-[13px] text-[#4a5568] leading-relaxed font-sans space-y-4">
            <p>
              Nerolith Terrain is not a new experiment. It's the terrain
              intelligence layer extracted from Nerolith — the flood simulation
              platform built for government disaster response, running
              physics-constrained simulations on Indian watershed data with
              real-time Sentinel-1 SAR recalibration.
            </p>
          </div>
          <div className="text-[13px] text-[#4a5568] leading-relaxed font-sans space-y-4">
            <p>
              The Wang-Liu depression filling, Multi-Flow-Direction routing,
              Topographic Wetness Index computation, and hydrological
              conditioning at the core of Nerolith Terrain are the same
              algorithms validating flood forecasts across Chalakudy Basin,
              Kerala and beyond.
            </p>
            <p>
              You're not getting a research prototype. You're getting a
              production engine, wrapped in a developer-friendly API.
            </p>
          </div>
        </div>
      </section>

      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 border-t border-slate-100 max-w-[1100px] mx-auto !mt-16">
        <span className="font-mono text-[11px] text-slate-500 uppercase tracking-wider">
          NEROLITH TERRAIN SUITE PROTOCOLS
        </span>
        <div className="flex items-center gap-6">
          <a
            href="#documentation"
            onClick={(e) => {
              e.preventDefault();
              scrollToDocs();
            }}
            className="font-mono text-[11px] text-[#4a5568] hover:text-[#0000ff] uppercase transition-colors"
          >
            Read the Technical Docs →
          </a>
        </div>
      </div>
    </div>
  );
}
