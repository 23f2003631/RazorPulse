import React, { useEffect, useState } from "react";
import {
  DemoScenarioResponse,
  InvestigationDetailResponse,
  InvestigationResponse,
  InvestigationStatus,
  RiskEvent,
  RiskEventCreate,
} from "./types";
import { api } from "./services/api";
import { ConsoleTab, Sidebar } from "./components/Sidebar";
import { TopHeader } from "./components/TopHeader";
import { Dashboard } from "./components/Dashboard";
import { DossierView } from "./components/DossierView";
import { DemoScenarioSelector } from "./components/DemoScenarioSelector";
import { InvestigationsView } from "./components/InvestigationsView";
import { EvidenceVault, VaultEvidenceItem } from "./components/EvidenceVault";
import { SimulateAnomalyModal } from "./components/SimulateAnomalyModal";
import { SystemHealthModal } from "./components/SystemHealthModal";
import { HelpDocsModal } from "./components/HelpDocsModal";
import { ErrorBanner, LoadingSpinner } from "./components/Common";
import { InvestigationProgress } from "./components/InvestigationProgress";

// Offline snapshot fixture for true offline / backend-independent demo mode
import demoScenariosFixture from "./data/demoScenariosFixture.json";

export const App: React.FC = () => {
  const [activeMode, setActiveMode] = useState<"live" | "demo">("live");
  const [currentTab, setCurrentTab] = useState<ConsoleTab>("dashboard");
  const [isBackendConnected, setIsBackendConnected] = useState<boolean>(false);

  // Live datasets
  const [events, setEvents] = useState<RiskEvent[]>([]);
  const [investigationsList, setInvestigationsList] = useState<InvestigationResponse[]>([]);
  const [investigationsMap, setInvestigationsMap] = useState<Record<string, string>>({}); // risk_event_id -> investigation_id
  const [contradictionsMap, setContradictionsMap] = useState<Record<string, boolean>>({}); // investigation_id -> hasContradiction
  const [selectedInvestigation, setSelectedInvestigation] = useState<InvestigationDetailResponse | null>(null);
  const [cachedDetailsMap, setCachedDetailsMap] = useState<Record<string, InvestigationDetailResponse>>({});

  // Loading states
  const [isLoadingEvents, setIsLoadingEvents] = useState<boolean>(false);
  const [isLoadingDossier, setIsLoadingDossier] = useState<boolean>(false);

  // Active investigation execution state
  const [activeInvestigatingId, setActiveInvestigatingId] = useState<string | null>(null);
  const [activeProgressStatus, setActiveProgressStatus] = useState<InvestigationStatus | null>(null);
  const [activeErrorStage, setActiveErrorStage] = useState<string | null>(null);

  // Demo scenarios dataset
  const [demoScenarios, setDemoScenarios] = useState<DemoScenarioResponse[]>(
    (demoScenariosFixture as any).scenarios || []
  );
  const [isLoadingDemos, setIsLoadingDemos] = useState<boolean>(false);

  // Filters & search state
  const [searchVal, setSearchVal] = useState<string>("");
  const [activeQueueFilter, setActiveQueueFilter] = useState<
    "all" | "needs_investigation" | "investigated" | "contradictions"
  >("all");

  // Modals state
  const [isSimulateModalOpen, setIsSimulateModalOpen] = useState<boolean>(false);
  const [isSubmittingSimulate, setIsSubmittingSimulate] = useState<boolean>(false);
  const [isHealthModalOpen, setIsHealthModalOpen] = useState<boolean>(false);
  const [isHelpDocsOpen, setIsHelpDocsOpen] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Initial check & data load
  useEffect(() => {
    checkHealthAndLoad();
  }, []);

  const checkHealthAndLoad = async () => {
    try {
      const health = await api.checkHealth();
      const isOk = health.status === "ok";
      setIsBackendConnected(isOk);
      if (isOk) {
        await Promise.all([loadLiveEvents(), loadDemoScenariosFromBackend()]);
      }
    } catch {
      setIsBackendConnected(false);
      // In offline state, load from the offline snapshot fixture
      if (demoScenarios.length === 0 && (demoScenariosFixture as any)?.scenarios) {
        setDemoScenarios((demoScenariosFixture as any).scenarios);
      }
    }
  };

  const loadLiveEvents = async () => {
    setIsLoadingEvents(true);
    setErrorMessage(null);
    try {
      // Use limit=100 to retrieve complete MVP dataset
      const [eventsRes, invsRes] = await Promise.all([
        api.getRiskEvents(100, 0),
        api.listInvestigations(100, 0),
      ]);

      setEvents(eventsRes.data);
      setInvestigationsList(invsRes.data);

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

  const loadDemoScenariosFromBackend = async () => {
    setIsLoadingDemos(true);
    try {
      const res = await api.getDemoScenarios();
      setDemoScenarios(res.scenarios);
    } catch {
      // Fallback to offline distribution snapshot
      if ((demoScenariosFixture as any)?.scenarios) {
        setDemoScenarios((demoScenariosFixture as any).scenarios);
      }
    } finally {
      setIsLoadingDemos(false);
    }
  };

  const handleModeChange = (mode: "live" | "demo") => {
    setActiveMode(mode);
    if (mode === "demo") {
      setCurrentTab("demos");
      if (demoScenarios.length === 0) {
        loadDemoScenariosFromBackend();
      }
    } else {
      setCurrentTab("dashboard");
      if (isBackendConnected) {
        loadLiveEvents();
      }
    }
  };

  // Synchronous investigation trigger
  const handleInvestigate = async (event: RiskEvent) => {
    setActiveInvestigatingId(event.id);
    setActiveProgressStatus("searching");
    setActiveErrorStage(null);
    setErrorMessage(null);

    try {
      const result = await api.triggerInvestigation(event.id);
      setActiveProgressStatus("completed");
      setSelectedInvestigation(result);

      // Cache details
      setCachedDetailsMap((prev) => ({ ...prev, [result.id]: result }));

      // Check contradictions
      const hasContra =
        (result.dossier?.contradictions && result.dossier.contradictions.length > 0) ||
        (result.verification_items &&
          result.verification_items.some(
            (v) => (v.contradictions_identified && v.contradictions_identified.length > 0) || v.evidence_strength === "contradicted"
          ));
      if (hasContra) {
        setContradictionsMap((prev) => ({ ...prev, [result.id]: true }));
      }

      // Update map & event status
      setInvestigationsMap((prev) => ({ ...prev, [event.id]: result.id }));
      setInvestigationsList((prev) => {
        const existing = prev.filter((i) => i.id !== result.id);
        const newSummary: InvestigationResponse = {
          id: result.id,
          risk_event_id: result.risk_event_id,
          status: result.status,
          eci_score: result.eci_score,
          eci_band: result.eci_band,
          eci_version: result.eci_version,
          evidence_count: result.evidence_count,
          created_at: result.created_at,
          started_at: result.started_at,
          completed_at: result.completed_at,
        };
        return [newSummary, ...existing];
      });

      // Navigate to synthesized dossier
      setActiveInvestigatingId(null);
      setActiveProgressStatus(null);
      setCurrentTab("dossier");
    } catch (err: any) {
      setActiveProgressStatus("failed");
      setActiveErrorStage("pipeline");
      setErrorMessage(`Investigation failed: ${err.message}`);
      setTimeout(() => {
        setActiveInvestigatingId(null);
        setActiveProgressStatus(null);
      }, 4000);
    }
  };

  const handleViewDossier = async (investigationId: string) => {
    // Check if already cached
    if (cachedDetailsMap[investigationId]) {
      setSelectedInvestigation(cachedDetailsMap[investigationId]);
      setCurrentTab("dossier");
      return;
    }

    setIsLoadingDossier(true);
    setErrorMessage(null);
    try {
      const result = await api.getInvestigation(investigationId);
      setSelectedInvestigation(result);
      setCachedDetailsMap((prev) => ({ ...prev, [result.id]: result }));

      // Cache contradiction state
      const hasContra =
        (result.dossier?.contradictions && result.dossier.contradictions.length > 0) ||
        (result.verification_items &&
          result.verification_items.some(
            (v) => (v.contradictions_identified && v.contradictions_identified.length > 0) || v.evidence_strength === "contradicted"
          ));
      if (hasContra) {
        setContradictionsMap((prev) => ({ ...prev, [result.id]: true }));
      }

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

  // Context-aware exports
  const handleExportDossier = () => {
    if (!selectedInvestigation?.dossier) return;
    const merchant = selectedInvestigation.dossier.anomaly_context.merchant_name.replace(/[^a-zA-Z0-9]/g, "_");
    const filename = `razorpulse-dossier-${merchant}-${selectedInvestigation.id.slice(0, 8)}.json`;
    const jsonStr = JSON.stringify(selectedInvestigation, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleExportQueueSummary = () => {
    const filename = `razorpulse-queue-summary-${new Date().toISOString().slice(0, 10)}.json`;
    const exportPayload = {
      export_type: "queue_summary",
      exported_at: new Date().toISOString(),
      mode: activeMode,
      active_filter: activeQueueFilter,
      total_records: events.length,
      records: events.map((ev) => {
        const invId = investigationsMap[ev.id];
        const inv = invId ? investigationsList.find((i) => i.id === invId) : null;
        return {
          risk_event_id: ev.id,
          merchant_name: ev.merchant_name,
          merchant_domain: ev.merchant_domain,
          anomaly_type: ev.anomaly_type,
          occurred_at: ev.occurred_at,
          transaction_amount: ev.transaction_amount,
          currency: ev.currency,
          baseline_transaction_count: ev.baseline_transaction_count,
          observed_transaction_count: ev.observed_transaction_count,
          percentage_change: ev.percentage_change,
          investigation_status: inv ? inv.status : "needs_investigation",
          eci_score: inv ? inv.eci_score : null,
          eci_band: inv ? inv.eci_band : null,
          has_contradiction: invId ? Boolean(contradictionsMap[invId]) : false,
        };
      }),
    };

    const jsonStr = JSON.stringify(exportPayload, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Build merchant maps for fast lookup
  const merchantNamesMap: Record<string, string> = {};
  const merchantDomainsMap: Record<string, string> = {};
  events.forEach((e) => {
    merchantNamesMap[e.id] = e.merchant_name;
    if (e.merchant_domain) merchantDomainsMap[e.id] = e.merchant_domain;
  });

  // Calculate badge counts
  const needsInvestigationCount = events.filter((e) => !investigationsMap[e.id]).length;
  const investigationsCount = investigationsList.length;
  const contradictionsCount = investigationsList.filter(
    (i) => contradictionsMap[i.id] || (i.eci_score !== null && i.eci_score !== undefined && i.eci_score <= 10 && i.eci_band === "low")
  ).length;

  // Compile Evidence Vault items
  const vaultItems: VaultEvidenceItem[] = [];
  if (activeMode === "demo") {
    demoScenarios.forEach((scen) => {
      (scen.evidence_items || []).forEach((item) => {
        vaultItems.push({
          ...item,
          merchantName: scen.merchant_name,
          investigationId: scen.dossier.investigation_id,
          isDemo: true,
        });
      });
    });
  } else {
    // Collect from all cached completed investigations
    Object.values(cachedDetailsMap).forEach((inv) => {
      const merchant = merchantNamesMap[inv.risk_event_id] || "Investigated Merchant";
      (inv.evidence_items || []).forEach((item) => {
        vaultItems.push({
          ...item,
          merchantName: merchant,
          investigationId: inv.id,
          isDemo: false,
        });
      });
    });
  }

  return (
    <div className="app-shell">
      {/* 260px Persistent Left Sidebar */}
      <Sidebar
        currentTab={currentTab}
        onTabChange={setCurrentTab}
        activeMode={activeMode}
        onModeChange={handleModeChange}
        onOpenSimulateModal={() => setIsSimulateModalOpen(true)}
        onOpenHelpDocs={() => setIsHelpDocsOpen(true)}
        onFilterAnomaliesQueue={(f) => {
          setActiveQueueFilter(f);
          setCurrentTab("dashboard");
        }}
        needsInvestigationCount={needsInvestigationCount}
        investigationsCount={investigationsCount}
        contradictionsCount={contradictionsCount}
        evidenceVaultCount={vaultItems.length}
      />

      {/* Main Content Wrapper (offset by 260px) */}
      <div className="main-wrapper">
        {/* Top Header Console */}
        <TopHeader
          isBackendConnected={isBackendConnected}
          searchVal={searchVal}
          onSearchChange={setSearchVal}
          isSearching={Boolean(searchVal.trim())}
          currentTab={currentTab}
          hasActiveDossier={Boolean(selectedInvestigation?.dossier)}
          onExportDossier={handleExportDossier}
          onExportQueue={handleExportQueueSummary}
          onOpenHealthModal={() => setIsHealthModalOpen(true)}
        />

        {/* Global Error Banner */}
        {errorMessage && (
          <div style={{ padding: "0 2rem", marginTop: "1rem" }}>
            <ErrorBanner message={errorMessage} onRetry={checkHealthAndLoad} />
          </div>
        )}

        {/* Active Investigation Synchronous Stepper Progress */}
        {activeInvestigatingId && activeProgressStatus && (
          <div style={{ padding: "0 2rem", marginTop: "1rem" }}>
            <InvestigationProgress
              status={activeProgressStatus}
              errorStage={activeErrorStage}
              errorMessage={errorMessage}
            />
          </div>
        )}

        {/* TAB 1: Dashboard Overview */}
        {currentTab === "dashboard" && (
          <Dashboard
            events={events}
            investigationsMap={investigationsMap}
            investigationsList={investigationsList}
            contradictionsMap={contradictionsMap}
            onInvestigate={handleInvestigate}
            onViewDossier={handleViewDossier}
            onOpenSimulateModal={() => setIsSimulateModalOpen(true)}
            onRefresh={loadLiveEvents}
            isLoading={isLoadingEvents}
            activeInvestigatingId={activeInvestigatingId}
            searchFilterQuery={searchVal}
            activeQueueFilter={activeQueueFilter}
            onQueueFilterChange={setActiveQueueFilter}
            onNavigateToDemoMode={() => handleModeChange("demo")}
          />
        )}

        {/* TAB 2: Dedicated Investigations View */}
        {currentTab === "investigations" && (
          <InvestigationsView
            investigations={investigationsList}
            merchantNamesMap={merchantNamesMap}
            merchantDomainsMap={merchantDomainsMap}
            onViewDossier={handleViewDossier}
            onBackToDashboard={() => setCurrentTab("dashboard")}
            contradictionsMap={contradictionsMap}
          />
        )}

        {/* TAB 3: Evidence Dossier View */}
        {currentTab === "dossier" && (
          <div className="page-container">
            {isLoadingDossier ? (
              <LoadingSpinner text="Retrieving complete evidence dossier from backend..." />
            ) : selectedInvestigation ? (
              <DossierView
                investigation={selectedInvestigation}
                onBackToQueue={() => setCurrentTab(activeMode === "demo" ? "demos" : "dashboard")}
                isDemo={activeMode === "demo"}
              />
            ) : (
              <div className="card" style={{ padding: "3rem", textAlign: "center" }}>
                <p style={{ color: "var(--text-secondary)", marginBottom: "1rem" }}>
                  No investigation dossier selected.
                </p>
                <button className="btn btn-primary" onClick={() => setCurrentTab("dashboard")}>
                  Return to Anomaly Queue
                </button>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: Deterministic Demo Scenarios */}
        {currentTab === "demos" && (
          <div className="page-container">
            <DemoScenarioSelector
              scenarios={demoScenarios}
              isLoading={isLoadingDemos}
              onBackToQueue={() => {
                setActiveMode("live");
                setCurrentTab("dashboard");
              }}
            />
          </div>
        )}

        {/* TAB 5: Discovered Evidence Vault */}
        {currentTab === "vault" && (
          <EvidenceVault
            items={vaultItems}
            isDemoMode={activeMode === "demo"}
            onViewDossier={handleViewDossier}
            onBackToDashboard={() => setCurrentTab("dashboard")}
          />
        )}
      </div>

      {/* MODAL 1: Ingest Simulated Payment Anomaly */}
      <SimulateAnomalyModal
        isOpen={isSimulateModalOpen}
        onClose={() => setIsSimulateModalOpen(false)}
        onSubmit={handleSimulateSubmit}
        isSubmitting={isSubmittingSimulate}
      />

      {/* MODAL 2: Backend Health & Safe Integrations Readout */}
      <SystemHealthModal
        isOpen={isHealthModalOpen}
        onClose={() => setIsHealthModalOpen(false)}
        isBackendConnected={isBackendConnected}
        onRefreshHealth={checkHealthAndLoad}
      />

      {/* MODAL 3: Analyst Reference Guide (ECI v1.1 Methodology) */}
      <HelpDocsModal
        isOpen={isHelpDocsOpen}
        onClose={() => setIsHelpDocsOpen(false)}
      />
    </div>
  );
};

export default App;
