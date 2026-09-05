import React, { useEffect, useState } from "react";
import {
  DemoScenarioResponse,
  InvestigationDetailResponse,
  RiskEvent,
  RiskEventCreate,
} from "./types";
import { api } from "./services/api";
import { Navbar } from "./components/Navbar";
import { Dashboard } from "./components/Dashboard";
import { DossierView } from "./components/DossierView";
import { DemoScenarioSelector } from "./components/DemoScenarioSelector";
import { SimulateAnomalyModal } from "./components/SimulateAnomalyModal";
import { ErrorBanner, LoadingSpinner } from "./components/Common";
import { InvestigationProgress } from "./components/InvestigationProgress";

export const App: React.FC = () => {
  const [activeMode, setActiveMode] = useState<"live" | "demo">("live");
  const [currentTab, setCurrentTab] = useState<"dashboard" | "dossier" | "demos">("dashboard");
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);

  // Live data
  const [events, setEvents] = useState<RiskEvent[]>([]);
  const [investigationsMap, setInvestigationsMap] = useState<Record<string, string>>({});
  const [selectedInvestigation, setSelectedInvestigation] = useState<InvestigationDetailResponse | null>(null);
  const [isLoadingEvents, setIsLoadingEvents] = useState<boolean>(false);
  const [isLoadingDossier, setIsLoadingDossier] = useState<boolean>(false);

  // Active investigation execution state
  const [activeInvestigatingId, setActiveInvestigatingId] = useState<string | null>(null);
  const [activeProgressStatus, setActiveProgressStatus] = useState<any>(null);

  // Demo data
  const [demoScenarios, setDemoScenarios] = useState<DemoScenarioResponse[]>([]);
  const [isLoadingDemos, setIsLoadingDemos] = useState<boolean>(false);

  // Modal & Error state
  const [isSimulateModalOpen, setIsSimulateModalOpen] = useState<boolean>(false);
  const [isSubmittingSimulate, setIsSubmittingSimulate] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Initial connectivity check & data load
  useEffect(() => {
    checkHealthAndLoad();
  }, []);

  const checkHealthAndLoad = async () => {
    try {
      const health = await api.checkHealth();
      setIsBackendConnected(health.status === "ok");
      loadLiveEvents();
    } catch {
      setIsBackendConnected(false);
      setErrorMessage("Unable to connect to FastAPI backend at http://localhost:8000. Please ensure the server is running.");
    }
  };

  const loadLiveEvents = async () => {
    setIsLoadingEvents(true);
    setErrorMessage(null);
    try {
      const [eventsRes, invsRes] = await Promise.all([
        api.getRiskEvents(50, 0),
        api.listInvestigations(100, 0),
      ]);

      setEvents(eventsRes.data);

      // Build map of risk_event_id -> investigation_id
      const map: Record<string, string> = {};
      invsRes.data.forEach((inv) => {
        map[inv.risk_event_id] = inv.id;
      });
      setInvestigationsMap(map);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to load risk events queue.");
    } finally {
      setIsLoadingEvents(false);
    }
  };

  const loadDemoScenarios = async () => {
    setIsLoadingDemos(true);
    setErrorMessage(null);
    try {
      const res = await api.getDemoScenarios();
      setDemoScenarios(res.scenarios);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to load deterministic demo scenarios.");
    } finally {
      setIsLoadingDemos(false);
    }
  };

  const handleModeChange = (mode: "live" | "demo") => {
    setActiveMode(mode);
    if (mode === "demo") {
      setCurrentTab("demos");
      if (demoScenarios.length === 0) {
        loadDemoScenarios();
      }
    } else {
      setCurrentTab("dashboard");
      loadLiveEvents();
    }
  };

  const handleInvestigate = async (event: RiskEvent) => {
    setActiveInvestigatingId(event.id);
    setActiveProgressStatus("searching");
    setErrorMessage(null);

    try {
      // Simulate live stage transitions for responsive UX
      setTimeout(() => setActiveProgressStatus("verifying"), 800);
      setTimeout(() => setActiveProgressStatus("scoring"), 1600);

      const result = await api.triggerInvestigation(event.id);
      setActiveProgressStatus("completed");
      setSelectedInvestigation(result);

      // Update map & event status locally
      setInvestigationsMap((prev) => ({ ...prev, [event.id]: result.id }));
      setEvents((prev) =>
        prev.map((e) => (e.id === event.id ? { ...e, status: "completed" } : e))
      );

      // Transition to Dossier View after completion
      setTimeout(() => {
        setActiveInvestigatingId(null);
        setActiveProgressStatus(null);
        setCurrentTab("dossier");
      }, 500);
    } catch (err: any) {
      setActiveProgressStatus("failed");
      setErrorMessage(`Investigation failed: ${err.message}`);
      setTimeout(() => {
        setActiveInvestigatingId(null);
        setActiveProgressStatus(null);
      }, 3000);
    }
  };

  const handleViewDossier = async (investigationId: string) => {
    setIsLoadingDossier(true);
    setErrorMessage(null);
    try {
      const result = await api.getInvestigation(investigationId);
      setSelectedInvestigation(result);
      setCurrentTab("dossier");
    } catch (err: any) {
      setErrorMessage(`Failed to fetch dossier: ${err.message}`);
    } finally {
      setIsLoadingDossier(false);
    }
  };

  const handleSimulateSubmit = async (payload: RiskEventCreate) => {
    setIsSubmittingSimulate(true);
    setErrorMessage(null);
    try {
      await api.createRiskEvent(payload);
      await loadLiveEvents();
    } catch (err: any) {
      setErrorMessage(`Failed to ingest simulated anomaly: ${err.message}`);
    } finally {
      setIsSubmittingSimulate(false);
    }
  };

  return (
    <div>
      <Navbar
        currentTab={currentTab}
        onTabChange={(tab) => {
          setCurrentTab(tab);
          if (tab === "demos" && demoScenarios.length === 0) {
            loadDemoScenarios();
          }
        }}
        isBackendConnected={isBackendConnected}
        activeMode={activeMode}
        onModeChange={handleModeChange}
      />

      <main className="main-content">
        <div className="container">
          {errorMessage && (
            <ErrorBanner message={errorMessage} onRetry={checkHealthAndLoad} />
          )}

          {/* Active investigation progress banner */}
          {activeInvestigatingId && activeProgressStatus && (
            <InvestigationProgress status={activeProgressStatus} />
          )}

          {/* Tab 1: Live Dashboard Queue */}
          {currentTab === "dashboard" && (
            <Dashboard
              events={events}
              investigationsMap={investigationsMap}
              onInvestigate={handleInvestigate}
              onViewDossier={handleViewDossier}
              onOpenSimulateModal={() => setIsSimulateModalOpen(true)}
              onRefresh={loadLiveEvents}
              isLoading={isLoadingEvents}
              activeInvestigatingId={activeInvestigatingId}
            />
          )}

          {/* Tab 2: Investigation Dossier View */}
          {currentTab === "dossier" && (
            isLoadingDossier ? (
              <LoadingSpinner text="Retrieving comprehensive evidence dossier..." />
            ) : selectedInvestigation ? (
              <DossierView
                investigation={selectedInvestigation}
                onBackToQueue={() => setCurrentTab("dashboard")}
                isDemo={activeMode === "demo"}
              />
            ) : (
              <div className="panel" style={{ padding: "2rem", textAlign: "center" }}>
                <p style={{ color: "var(--text-secondary)" }}>No investigation selected.</p>
                <button className="btn btn-secondary" onClick={() => setCurrentTab("dashboard")} style={{ marginTop: "1rem" }}>
                  Go to Anomaly Queue
                </button>
              </div>
            )
          )}

          {/* Tab 3: Deterministic Demo Scenarios */}
          {currentTab === "demos" && (
            <DemoScenarioSelector
              scenarios={demoScenarios}
              isLoading={isLoadingDemos}
              onBackToQueue={() => {
                setActiveMode("live");
                setCurrentTab("dashboard");
              }}
            />
          )}
        </div>
      </main>

      {/* Modal: Simulate Risk Anomaly */}
      <SimulateAnomalyModal
        isOpen={isSimulateModalOpen}
        onClose={() => setIsSimulateModalOpen(false)}
        onSubmit={handleSimulateSubmit}
        isSubmitting={isSubmittingSimulate}
      />
    </div>
  );
};

export default App;
