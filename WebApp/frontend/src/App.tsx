import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  ArrowRight,
  Database,
  Brain,
  Activity,
  Compass,
  Map,
  Bell,
  Cpu,
  CheckCircle,
  AlertCircle,
  Mail,
  Sparkles,
  Info,
  Server,
  CloudLightning,
  ChevronRight,
  Shield,
  Clock,
  RefreshCw,
} from "lucide-react";
import { REGIONS } from "./data";
import EarthGlobe from "./components/EarthGlobe";
import type { SimulationRegion } from "./types";
import { TerrainApiView } from "./components/TerrainApiView";

export default function App() {
  // Region context mapping states
  const [selectedRegionId, setSelectedRegionId] =
    useState<string>("southeast-asia");
  const [showDemoModal, setShowDemoModal] = useState<boolean>(false);

  // Waitlist collection states
  const [waitlistEmail, setWaitlistEmail] = useState<string>("");
  const [waitlistLoading, setWaitlistLoading] = useState<boolean>(false);
  const [waitlistSuccess, setWaitlistSuccess] = useState<boolean>(false);
  const [waitlistError, setWaitlistError] = useState<string>("");
  const [waitlistCount, setWaitlistCount] = useState<number>(1428); // Dynamic simulated subscriber base

  const [currentView, setCurrentView] = useState<"home" | "terrain">("home");

  // Slider animation mock values in landing page bento box
  const [perfScrollPercent, setPerfScrollPercent] = useState<number>(85);
  const [liveMemUsage, setLiveMemUsage] = useState<number>(12.4);
  const [liveCpuLoad, setLiveCpuLoad] = useState<number>(42.1);
  const [perfFrame, setPerfFrame] = useState<number>(412);

  // References for anchor scroll links
  const waitlistSectionRef = useRef<HTMLDivElement>(null);
  const simulationsSectionRef = useRef<HTMLDivElement>(null);

  // Simulate bento grid real-time numbers fluctuating slightly to convey the "live compute engine"
  useEffect(() => {
    const interval = setInterval(() => {
      setLiveCpuLoad((prev) => {
        const delta = Math.random() * 4 - 2;
        return Math.max(
          35.0,
          Math.min(55.0, parseFloat((prev + delta).toFixed(1))),
        );
      });
      setLiveMemUsage((prev) => {
        const delta = Math.random() * 0.2 - 0.1;
        return Math.max(
          12.0,
          Math.min(13.0, parseFloat((prev + delta).toFixed(1))),
        );
      });
      setPerfFrame((prev) => {
        if (prev >= 1000) return 1;
        return prev + 1;
      });
    }, 2500);

    return () => clearInterval(interval);
  }, []);

  // Quick action: Scroll to a given section with offset
  const scrollToSection = (
    targetRef: React.RefObject<HTMLDivElement | null>,
  ) => {
    if (targetRef && targetRef.current) {
      targetRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  // Waitlist signup handler
  const handleWaitlistSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!waitlistEmail || !waitlistEmail.includes("@")) {
      setWaitlistError(
        "Invalid email format. Please provide a functional professional address.",
      );
      return;
    }

    setWaitlistLoading(true);
    setWaitlistError("");

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || ""}/api/waitlist`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: waitlistEmail }),
        },
      );

      const data = await response.json();
      if (response.ok) {
        setWaitlistSuccess(true);
        if (data.count) {
          setWaitlistCount(1428 + data.count);
        }
        setWaitlistEmail("");
      } else {
        setWaitlistError(data.error || "Email already registered.");
      }
    } catch (err) {
      setWaitlistError("Connection failed. Please try again.");
      setWaitlistSuccess(false);
    } finally {
      setWaitlistLoading(false);
    }
  };

  // Region click handler to focus on the active telemetry
  const handleRegionCardClick = (regionId: string) => {
    setSelectedRegionId(regionId);
  };

  return (
    <div className="min-h-screen flex flex-col selection:bg-blue-100 selection:text-primary">
      {/* Top Navbar Header */}
      <header className="w-full sticky top-0 bg-white z-50 border-b border-slate-100 font-sans">
        <div className="flex justify-between items-center px-8 lg:px-[64px] py-[15px] max-w-[1440px] mx-auto">
          <div className="flex items-center">
            <span className="font-sans text-[26px] font-bold tracking-tight text-[#0000ff]">
              Nerolith
            </span>
          </div>

          <nav className="hidden md:flex items-center gap-[40px]">
           <button
  onClick={() => {
    setCurrentView("home");
    window.scrollTo(0, 0);
  }}
  className="font-sans text-[16px] font-medium text-[#5c647a] hover:text-[#0000ff] transition-colors cursor-pointer"
>
  Product
</button>

            <button
              onClick={() => {
                setCurrentView("terrain");
                window.scrollTo(0, 0);
              }}
              className="font-sans text-[16px] font-medium text-[#5c647a] hover:text-[#0000ff] transition-colors cursor-pointer"
            >
              Terrain API
            </button>
          </nav>

          <div className="flex items-center gap-[32px]">
            {/* <button 
              onClick={() => scrollToSection(waitlistSectionRef)}
              className="font-sans text-[16px] font-medium text-[#5c647a] hover:text-[#0000ff] transition-colors hidden sm:inline cursor-pointer"
            >
              Log In
            </button> */}
           
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 w-full max-w-[1440px] mx-auto px-8 lg:px-[64px] pt-[80px] pb-24 space-y-28">

          {currentView === "terrain" ? (
    <TerrainApiView
      onScrollToTop={() => {
        setCurrentView("home");
        window.scrollTo(0, 0);
      }}
      onNavigateToPlatformScreen={() => {
        setCurrentView("home");
        window.scrollTo(0, 0);
      }}
    />
  ) : (
<>
    
        {/* Hero Section */}

        <section className="relative flex flex-col items-center justify-center text-center min-h-[88vh] overflow-hidden">
          {/* Animated topographic grid background */}
          <div className="absolute inset-0 pointer-events-none">
            {/* Base grid */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(0,0,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(0,0,255,0.03)_1px,transparent_1px)] bg-[size:48px_48px]" />
            {/* Blue radial glow behind headline */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[400px] bg-[radial-gradient(ellipse,rgba(0,0,255,0.06)_0%,transparent_70%)]" />
            {/* Bottom fade */}
            <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-white to-transparent" />
          </div>

          <div className="relative z-10 flex flex-col items-center max-w-4xl px-4">
            <h1 className="text-4xl sm:text-5xl lg:text-[62px] font-extrabold text-slate-950 font-sans leading-[1.05] tracking-tight mb-6">
              From Terrain Data
              <br />
              <span className="text-[#0000ff]">to Flood Intelligence</span>
            </h1>

            <p className="text-[17px] text-[#4a5568] leading-relaxed font-sans max-w-xl text-center mb-10">
              Physics-constrained ML flood simulation. Real-time satellite
              recalibration. 72-hour early warning. Built for disaster response
              at scale.
            </p>

            <div className="flex flex-wrap gap-4 mb-16 justify-center">
              <button
                onClick={() => scrollToSection(waitlistSectionRef)}
                className="bg-[#0000ff] text-white font-sans text-[17px] font-bold px-[30px] py-[16px] rounded-[3px] shadow-[0_4px_16px_rgba(0,0,255,0.15)] hover:bg-[#0000d6] transition-all duration-200 flex items-center gap-[10px] group cursor-pointer"
              >
                Request Demo
                <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1 shrink-0" />
              </button>
              <button
                onClick={() => scrollToSection(simulationsSectionRef)}
                className="bg-transparent border border-[#cbd2e1] text-slate-950 font-sans text-[17px] font-bold px-[30px] py-[16px] rounded-[3px] hover:bg-[#f4f5f8]/40 hover:border-slate-400 transition-all duration-200 cursor-pointer"
              >
                View Technology
              </button>
            </div>

            {/* Kerala heatmap preview */}
            <div className="relative w-full max-w-3xl rounded-sm overflow-hidden border border-slate-200 shadow-[0_8px_48px_rgba(0,0,0,0.10)]">
              {/* Top bar */}
              <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-between px-4 py-2.5 bg-slate-950/80 backdrop-blur-sm border-b border-white/10">
                <div className="flex items-center gap-2">
                  <span className="relative flex h-1.5 w-1.5">
                    {/* <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" /> */}
                    {/* <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-green-400" /> */}
                  </span>
                  <span className="font-mono text-[10px] text-white/70 uppercase tracking-wider">
                    Chalakudy Basin · Kerala 2018 · Sentinel-1 SAR
                  </span>
                </div>
                <span className="font-mono text-[10px] text-green-400 font-bold">
                  RECALIBRATED
                </span>
              </div>

              <img
                src="/kerala.png"
                alt="Kerala 2018 flood simulation heatmap"
                className="w-full object-cover aspect-[16/7]"
              />

              {/* Bottom overlay */}
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-slate-950/90 to-transparent px-5 py-4">
                <div className="flex justify-between items-end">
                  <div className="flex gap-4">
                    {[
                      { k: "RAINFALL", v: "2346.6mm" },
                      { k: "DAMS", v: "35 opened" },
                      { k: "DIVERGENCE", v: "18.4%→<5%" },
                    ].map(({ k, v }) => (
                      <div key={k}>
                        <span className="font-mono text-[9px] text-white/40 block uppercase">
                          {k}
                        </span>
                        <span className="font-mono text-[11px] text-white font-bold">
                          {v}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Stats Grid Bar */}
        <section
          className="grid grid-cols-2 md:grid-cols-4 gap-6 py-10 border-y border-slate-200 px-2"
          style={{ backgroundColor: "transparent", backgroundImage: "none" }}
        >
          <div className="flex flex-col items-center justify-center text-center">
            <span className="font-mono text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2">
              Divergence Reduction
            </span>
            <span className="text-3xl font-extrabold text-[#0000ff] tracking-tight font-sans">
              73%
            </span>
          </div>
          <div className="flex flex-col items-center justify-center text-center border-l border-slate-200">
            <span className="font-mono text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2">
              SAR Recalib Cycle
            </span>
            <span className="text-3xl font-extrabold text-[#0000ff] tracking-tight font-sans leading-none">
              {"<5 min"}
            </span>
          </div>
          <div className="flex flex-col items-center justify-center text-center border-l border-slate-200">
            <span className="font-mono text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2">
              Early Warning
            </span>
            <span className="text-3xl font-extrabold text-[#0000ff] tracking-tight font-sans">
              72–96 hr
            </span>
          </div>
          <div className="flex flex-col items-center justify-center text-center border-l border-slate-200">
            <span className="font-mono text-[10px] uppercase font-bold text-slate-500 tracking-wider mb-2">
              Grid Resolution
            </span>
            <span className="text-3xl font-extrabold text-[#0000ff] tracking-tight font-sans">
              30 m
            </span>
          </div>
        </section>

        {/* System Architecture Bento Grid */}
        <section className="space-y-12" ref={simulationsSectionRef}>
          <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 border-b border-slate-100 pb-6">
            <div>
              <span className="font-mono text-[11px] font-bold text-[#0000ff] tracking-widest block uppercase mb-1">
                Technical Core
              </span>
              <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight font-sans">
                System Architecture
              </h2>
            </div>
            <p className="text-xs sm:text-[13px] text-[#5c647a] font-sans max-w-md md:text-right leading-relaxed">
              A modular physics-informed artificial intelligence engine built
              for extreme precision and planetary-scale hydrologic analysis.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
            {/* Box 1: Data Pipeline */}
            <div className="technical-card rounded-none flex flex-col md:col-span-4 overflow-hidden">
              <div className="technical-header px-5 py-3 flex justify-between items-center bg-slate-50 border-b border-slate-100">
                <span className="font-mono text-[10px] uppercase font-bold text-slate-800">
                  Data Pipeline
                </span>
                <Database className="w-4 h-4 text-primary" />
              </div>
              <div className="p-6 flex-1 flex flex-col justify-between bg-white">
                <div>
                  <h3 className="text-base font-bold text-slate-950 leading-snug mb-2">
                    Automated Data Ingestion
                  </h3>
                  <p className="text-[#4a5568] text-[13px] leading-relaxed">
                    Continuous streaming of high-frequency satellite, radar, and
                    local IoT gauge telemetry from over 450 global stations.
                  </p>
                </div>
              </div>
            </div>

            {/* Box 2: Neural Core - Featured */}
            <div className="technical-card rounded-none flex flex-col md:col-span-4 overflow-hidden border-orange-200/50">
              <div className="technical-header px-5 py-3 flex justify-between items-center bg-blue-50/60 border-b border-blue-100">
                <span className="font-mono text-[10px] uppercase font-bold text-primary">
                  Neural Core
                </span>
                <Brain className="w-4 h-4 text-primary" />
              </div>
              <div className="p-6 flex-1 flex flex-col justify-between bg-blue-50/10">
                <div>
                  <h3 className="text-base font-bold text-slate-950 leading-snug mb-2">
                    Physics-ML Simulation
                  </h3>
                  <p className="text-[#4a5568] text-[13px] leading-relaxed">
                    Deep neural operators constrained by 2D Navier-Stokes
                    Navier-Stokes equations ensuring physically correct flow
                    vectors.
                  </p>
                </div>
              </div>
            </div>

            {/* Box 3: Distribution */}
            <div className="technical-card rounded-none flex flex-col md:col-span-4 overflow-hidden">
              <div className="technical-header px-5 py-3 flex justify-between items-center bg-slate-50 border-b border-slate-100">
                <span className="font-mono text-[10px] uppercase font-bold text-slate-800">
                  Distribution
                </span>
                <Server className="w-4 h-4 text-primary" />
              </div>
              <div className="p-6 flex-1 flex flex-col justify-between bg-white">
                <div>
                  <h3 className="text-base font-bold text-slate-950 leading-snug mb-2">
                    Intelligence Delivery
                  </h3>
                  <p className="text-[#4a5568] text-[13px] leading-relaxed">
                    Low-latency API parameters and ultra-light JSON-based
                    WebSocket streams for instant country dashboards
                    Integration.
                  </p>
                </div>
              </div>
            </div>

            {/* Box 4: Interactive Simulation Performance (Span-8) */}
            <div className="technical-card rounded-none md:col-span-8 flex flex-col overflow-hidden">
              <div className="technical-header px-5 py-3 flex justify-between items-center bg-slate-50 border-b border-slate-100">
                <span className="font-mono text-[10px] uppercase font-bold text-slate-800">
                  Performance Benchmarks
                </span>
                <Activity className="w-4 h-4 text-primary" />
              </div>

              <div className="p-6 sm:p-8 flex flex-col md:flex-row gap-8 items-center bg-white">
                <div className="flex-1 w-full space-y-4">
                  <h3 className="text-base font-bold text-slate-950 leading-snug">
                    Kerala 2018 Validation Run
                  </h3>
                  <div className="space-y-3 bg-white p-4 rounded-none border border-slate-200">
                    {/* Divergence reduction bar */}
                    <div className="space-y-1">
                      <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                        <span>SATELLITE RECALIBRATION DIVERGENCE</span>
                        <span className="text-green-600 font-bold">
                          18.4% → &lt;5%
                        </span>
                      </div>
                      <div className="w-full bg-slate-100 h-2 rounded-none overflow-hidden">
                        <div
                          className="bg-primary h-full"
                          style={{ width: "73%" }}
                        />
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        73% DIVERGENCE REDUCTION POST-RECALIBRATION
                      </div>
                    </div>

                    {/* Key run params */}
                    <div className="grid grid-cols-2 gap-2 pt-1">
                      {[
                        { label: "DOMAIN", value: "Chalakudy Basin" },
                        { label: "SIM PERIOD", value: "14–19 Aug 2018" },
                        { label: "RAINFALL INPUT", value: "3-hr IMD Gridded" },
                        { label: "DAMS MODELED", value: "35 Simultaneous" },
                      ].map(({ label, value }) => (
                        <div key={label} className="text-[10px] font-mono">
                          <span className="text-slate-400 block">{label}</span>
                          <span className="text-slate-800 font-bold">
                            {value}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Right stat cards — real numbers */}
                <div className="w-full md:w-1/3 grid grid-cols-2 md:grid-cols-1 gap-3">
                  <div className="bg-slate-50 p-3.5 rounded-none border border-slate-200 text-center md:text-left">
                    <span className="font-mono text-[10px] block text-slate-400 uppercase tracking-wider mb-1">
                      GRID_RES
                    </span>
                    <span className="font-mono font-bold text-[#0000ff] text-base sm:text-lg">
                      30 m
                    </span>
                    <span className="font-mono text-[9px] text-slate-400 block mt-0.5">
                      ~1.2M CELLS
                    </span>
                  </div>
                  <div className="bg-slate-50 p-3.5 rounded-none border border-slate-200 text-center md:text-left">
                    <span className="font-mono text-[10px] block text-slate-400 uppercase tracking-wider mb-1">
                      SAR_CYCLE
                    </span>
                    <span className="font-mono font-bold text-[#0000ff] text-base sm:text-lg">
                      &lt; 5 min
                    </span>
                    <span className="font-mono text-[9px] text-slate-400 block mt-0.5">
                      SENTINEL-1 UPDATE
                    </span>
                  </div>
                </div>
              </div>
            </div>
            {/* Box 5: Azure Scalability */}
            <div className="technical-card rounded-none flex flex-col md:col-span-4 overflow-hidden">
              <div className="technical-header px-5 py-3 flex justify-between items-center bg-slate-50 border-b border-slate-100">
                <span className="font-mono text-[10px] uppercase font-bold text-slate-800">
                  Infrastructure
                </span>
                <Compass className="w-4 h-4 text-primary" />
              </div>
              <div className="p-6 flex-1 flex flex-col justify-between bg-white">
                <div>
                  <h3 className="text-base font-bold text-slate-950 leading-snug mb-2">
                    Azure Scalability
                  </h3>
                  <p className="text-[#4a5568] text-[13px] leading-relaxed">
                    Global multi-node orchestration utilization deploying Azure
                    high-performance computing clusters (HPC).
                  </p>
                </div>
              </div>
            </div>

            {/* Box 6: OSM Datas */}
            <div className="technical-card rounded-none flex flex-col md:col-span-4 overflow-hidden">
              <div className="technical-header px-5 py-3 flex justify-between items-center bg-slate-50 border-b border-slate-100">
                <span className="font-mono text-[10px] uppercase font-bold text-slate-800">
                  Geospatial
                </span>
                <Map className="w-4 h-4 text-primary" />
              </div>
              <div className="p-6 flex-1 flex flex-col justify-between bg-white">
                <div>
                  <h3 className="text-base font-bold text-slate-950 leading-snug mb-2">
                    OSM Data Overlays
                  </h3>
                  <p className="text-[#4a5568] text-[13px] leading-relaxed">
                    Native integration with OpenStreetMap for instantaneous
                    structural, facility, and roads damage mappings.
                  </p>
                </div>
              </div>
            </div>

            {/* Box 7: LLM Alerting */}
            <div className="technical-card rounded-none flex flex-col md:col-span-4 overflow-hidden">
              <div className="technical-header px-5 py-3 flex justify-between items-center bg-slate-50 border-b border-slate-100">
                <span className="font-mono text-[10px] uppercase font-bold text-slate-800">
                  Notification
                </span>
                <Bell className="w-4 h-4 text-primary" />
              </div>
              <div className="p-6 flex-1 flex flex-col justify-between bg-white">
                <div>
                  <h3 className="text-base font-bold text-slate-950 leading-snug mb-2">
                    LLM Alerting
                  </h3>
                  <p className="text-[#4a5568] text-[13px] leading-relaxed">
                    Generative AI summaries that translate complex numerical
                    hydraulic data curves into clear, humanized alerts.
                  </p>
                </div>
              </div>
            </div>

            {/* Box 8: C++ Core Optimization */}
            <div className="technical-card rounded-none flex flex-col md:col-span-4 overflow-hidden">
              <div className="technical-header px-5 py-3 flex justify-between items-center bg-slate-50 border-b border-slate-100">
                <span className="font-mono text-[10px] uppercase font-bold text-slate-800">
                  Kernel
                </span>
                <Cpu className="w-4 h-4 text-primary" />
              </div>
              <div className="p-6 flex-1 flex flex-col justify-between bg-white">
                <div>
                  <h3 className="text-base font-bold text-slate-950 leading-snug mb-2">
                    C++ Core
                  </h3>
                  <p className="text-[#4a5568] text-[13px] leading-relaxed">
                    Zero-abstraction compute layer written in modern C++ for
                    bare-metal hydrologic simulation computation speeds.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Operational Deployment (Global Reach) Grid */}
        <section className="space-y-12">
          <div className="flex flex-col gap-2">
            <span className="font-mono text-[11px] font-bold text-primary tracking-widest block uppercase">
              Global Reach
            </span>
            <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight font-sans">
              Operational Deployment
            </h2>
            <p className="text-xs text-slate-500 max-w-xl">
              Select an active sector below to load its corresponding live
              telemetry gauge sets, and configure customized overflow parameters
              directly in our simulator.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-x-8 gap-y-12">
            {REGIONS.map((region) => {
              const worksAsSelected = selectedRegionId === region.id;
              return (
                <div
                  key={region.id}
                  onClick={() => handleRegionCardClick(region.id)}
                  className="group cursor-pointer select-none"
                >
                  <div
                    className={`relative aspect-square overflow-hidden rounded border transition-all duration-300 ${
                      worksAsSelected
                        ? "border-primary ring-2 ring-primary/20 shadow-md shadow-primary/5"
                        : "border-slate-200 hover:border-slate-400"
                    }`}
                  >
                    <img
                      alt={region.name}
                      className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-[1.02]"
                      src={region.image}
                      referrerPolicy="no-referrer"
                    />
                  </div>

                  <div className="mt-5">
                    <h4
                      className={`font-sans text-[24px]/[1.3] font-semibold tracking-tight transition-colors ${
                        worksAsSelected
                          ? "text-primary"
                          : "text-slate-900 group-hover:text-primary"
                      }`}
                    >
                      {region.name}
                    </h4>
                    <span className="font-mono text-xs text-slate-500 mt-1 block">
                      {region.status}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Call To Action: Secure Early Access Join Waitlist */}
        <section
          className="bg-gradient-to-br from-[#0000ff] to-[#1a3fff] px-8 py-16 sm:py-24 rounded-none text-center relative overflow-hidden shadow-xl shadow-blue-900/10"
          ref={waitlistSectionRef}
        >
          {/* Subtle overlay grid */}
          <div className="absolute inset-0 opacity-[0.08] pointer-events-none bg-[radial-gradient(circle_at_2px_2px,white_1px,transparent_0)] bg-[size:24px_24px]" />

          <div className="relative z-10 flex flex-col items-center max-w-xl mx-auto space-y-6">
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white font-sans tracking-tight leading-tight">
              Secure Early Access
            </h2>
            <p className="text-[14px] sm:text-[15px] leading-relaxed text-blue-100/90 font-sans max-w-lg">
              Join the waitlist for Nerolith Intelligence. Experience the next
              generation of hydrologic simulation and predictive data analytics.
            </p>

            <form
              onSubmit={handleWaitlistSubmit}
              className="flex flex-col sm:flex-row gap-3 w-full max-w-[540px]"
            >
              <div className="relative flex-1">
                <input
                  type="email"
                  value={waitlistEmail}
                  onChange={(e) => setWaitlistEmail(e.target.value)}
                  placeholder="Enter professional email"
                  className="w-full px-4 py-3.5 rounded-none text-slate-900 placeholder:text-slate-500 bg-[#e7ecf5] border-0 focus:ring-2 focus:ring-blue-300 focus:outline-none text-sm font-sans"
                  disabled={waitlistLoading || waitlistSuccess}
                  required
                />
              </div>
              <button
                type="submit"
                disabled={waitlistLoading || waitlistSuccess}
                className="bg-white text-[#0000ff] hover:bg-slate-100 font-sans text-xs uppercase tracking-widest font-extrabold px-8 py-3.5 rounded-none transition-all shadow-sm active:scale-95 flex items-center justify-center gap-1.5 shrink-0 disabled:opacity-85"
              >
                {waitlistLoading ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    BUFFERING...
                  </>
                ) : waitlistSuccess ? (
                  <>
                    <CheckCircle className="w-3.5 h-3.5 text-[#0000ff]" />
                    QUEUE RESERVED
                  </>
                ) : (
                  "Join Waitlist"
                )}
              </button>
            </form>

            {/* Error notifications */}
            {waitlistError && (
              <motion.div
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-red-500/20 text-red-200 text-xs font-mono border border-red-500/30 py-2 px-4 rounded flex items-center gap-2"
              >
                <AlertCircle className="w-4 h-4 text-red-350 shrink-0" />
                <span>{waitlistError}</span>
              </motion.div>
            )}

            {/* Success notifications */}
            {waitlistSuccess && (
              <motion.div
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-emerald-500/20 text-emerald-200 text-xs font-mono border border-emerald-500/30 py-2.5 px-4 rounded"
              >
                <div className="flex items-center gap-2 justify-center">
                  <span className="font-bold">You're on the list!</span>
                </div>
                <p className="text-[10px] text-emerald-300 mt-1 uppercase font-mono tracking-wider">
                  We'll reach out when early access opens
                </p>
              </motion.div>
            )}
          </div>
        </section>

        </>
                  )}
      </main>

      {/* Footer SECTION */}
      <footer className="w-full mt-auto bg-slate-100 border-t border-slate-200 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 px-8 lg:px-[64px] max-w-[1440px] mx-auto">
          <div className="flex flex-col gap-2 justify-center">
            <h3 className="font-sans text-xl font-bold text-slate-950 tracking-tight">
              Nerolith Intelligence
            </h3>
            <div className="font-mono text-[11px] text-slate-500 tracking-normal">
              © 2024 Nerolith Intelligence. Satellite Status: Operational
            </div>
          </div>
          <div className="grid grid-cols-2 gap-x-20 gap-y-4 md:justify-self-end self-center">
            <div>
              <a
                className="font-mono text-[11px] text-[#4a5568] hover:text-[#0000ff] transition-colors block md:mb-4 mb-2"
                href="#"
              >
                API Reference
              </a>
              <a
                className="font-mono text-[11px] text-[#4a5568] hover:text-[#0000ff] transition-colors block"
                href="#"
              >
                Network Status
              </a>
            </div>
            <div>
              <a
                className="font-mono text-[11px] text-[#4a5568] hover:text-[#0000ff] transition-colors block md:mb-4 mb-2"
                href="#"
              >
                Methodology
              </a>
              <a
                className="font-mono text-[11px] text-[#4a5568] hover:text-[#0000ff] transition-colors block"
                href="#"
              >
                Privacy Policy
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
