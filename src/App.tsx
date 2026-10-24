import React, { useState, useEffect } from "react";
import { Case, Evidence, GlobalStats, ForensicEvent } from "./types/forenx";
import { Sidebar, NavPage } from "./components/Sidebar";
import { Header } from "./components/Header";
import { OverviewPage } from "./components/pages/OverviewPage";
import { CasesPage } from "./components/pages/CasesPage";
import { LocalForensicsPage } from "./components/pages/LocalForensicsPage";
import { RemoteForensicsPage } from "./components/pages/RemoteForensicsPage";
import { EndpointsPage } from "./components/pages/EndpointsPage";
import { CollectionJobsPage } from "./components/pages/CollectionJobsPage";
import { EvidenceVaultPage } from "./components/pages/EvidenceVaultPage";
import { ArtifactExplorerPage } from "./components/pages/ArtifactExplorerPage";
import { UnifiedTimelinePage } from "./components/pages/UnifiedTimelinePage";
import { ValidationLabPage } from "./components/pages/ValidationLabPage";
import { ReportsPage } from "./components/pages/ReportsPage";
import { AuditLogPage } from "./components/pages/AuditLogPage";
import { SettingsPage } from "./components/pages/SettingsPage";
import { AboutPage } from "./components/pages/AboutPage";
import { NewCaseModal } from "./components/NewCaseModal";
import { UploadEvidenceModal } from "./components/UploadEvidenceModal";
import { EventDetailModal } from "./components/EventDetailModal";

export default function App() {
  const [currentPage, setCurrentPage] = useState<NavPage>("Overview");
  const [cases, setCases] = useState<Case[]>([]);
  const [activeCaseId, setActiveCaseId] = useState<string | null>(null);
  const [evidenceItems, setEvidenceItems] = useState<Evidence[]>([]);
  const [stats, setStats] = useState<GlobalStats | null>(null);

  const [isNewCaseOpen, setIsNewCaseOpen] = useState(false);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [inspectingEvent, setInspectingEvent] = useState<ForensicEvent | null>(null);
  const [isSeeding, setIsSeeding] = useState(false);

  // Fetch Cases and System Stats
  const loadCases = async () => {
    try {
      const res = await fetch("/api/cases");
      const json = await res.json();
      if (json.success) {
        setCases(json.data || []);
        if (json.data && json.data.length > 0 && !activeCaseId) {
          setActiveCaseId(json.data[0].id);
        }
      }
    } catch (err) {
      console.error("Error loading cases:", err);
    }
  };

  const loadStats = async () => {
    try {
      const res = await fetch("/api/stats");
      const json = await res.json();
      if (json.success) {
        setStats(json.data);
      }
    } catch (err) {
      console.error("Error loading stats:", err);
    }
  };

  // Fetch Evidence Items for active case
  const loadEvidence = async () => {
    if (!activeCaseId) {
      setEvidenceItems([]);
      return;
    }
    try {
      const res = await fetch(`/api/cases/${activeCaseId}/evidence`);
      const json = await res.json();
      if (json.success) {
        setEvidenceItems(json.data || []);
      }
    } catch (err) {
      console.error("Error loading evidence:", err);
    }
  };

  useEffect(() => {
    loadCases();
    loadStats();
  }, []);

  useEffect(() => {
    loadEvidence();
  }, [activeCaseId]);

  const activeCase = cases.find(c => c.id === activeCaseId) || null;

  // Handle Seeding Synthetic Benchmark Case
  const handleSeedDemo = async () => {
    setIsSeeding(true);
    try {
      const res = await fetch("/api/demo/seed", { method: "POST" });
      const json = await res.json();
      if (json.success) {
        await loadCases();
        await loadStats();
        setActiveCaseId(json.data.case_id);
        setCurrentPage("Overview");
      }
    } catch (err) {
      console.error("Error seeding synthetic demo:", err);
    } finally {
      setIsSeeding(false);
    }
  };

  const handleCaseCreated = (newCase: Case) => {
    setCases(prev => [newCase, ...prev]);
    setActiveCaseId(newCase.id);
    loadStats();
  };

  const handleCaseArchived = (caseId: string) => {
    setCases(prev => prev.map(c => (c.id === caseId ? { ...c, status: "archived" } : c)));
  };

  const handleEvidenceUploaded = () => {
    loadEvidence();
    loadStats();
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#FCFAFD] text-[#282235]">
      {/* Persistent Left Navigation Sidebar */}
      <Sidebar
        currentPage={currentPage}
        onSelectPage={setCurrentPage}
        cases={cases}
        activeCaseId={activeCaseId}
        onSelectCase={setActiveCaseId}
      />

      {/* Main Workspace Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header
          pageTitle={currentPage}
          activeCase={activeCase}
          onOpenNewCase={() => setIsNewCaseOpen(true)}
          onSeedDemo={handleSeedDemo}
          isSeeding={isSeeding}
        />

        <main className="flex-1 overflow-y-auto">
          {currentPage === "Overview" && (
            <OverviewPage
              stats={stats}
              cases={cases}
              onSelectCase={id => {
                setActiveCaseId(id);
                setCurrentPage("Cases");
              }}
              onNavigate={setCurrentPage}
              onSeedDemo={handleSeedDemo}
              onOpenNewCase={() => setIsNewCaseOpen(true)}
              isSeeding={isSeeding}
            />
          )}

          {currentPage === "Cases" && (
            <CasesPage
              cases={cases}
              activeCaseId={activeCaseId}
              onSelectCase={setActiveCaseId}
              onOpenNewCase={() => setIsNewCaseOpen(true)}
              onCaseArchived={handleCaseArchived}
            />
          )}

          {currentPage === "Local System Forensics" && (
            <LocalForensicsPage
              activeCase={activeCase}
              onAcquisitionComplete={() => {
                loadEvidence();
                loadStats();
              }}
              onNavigateToTimeline={() => setCurrentPage("Unified Timeline")}
            />
          )}

          {currentPage === "Remote System Forensics" && (
            <RemoteForensicsPage
              activeCase={activeCase}
              onNavigate={setCurrentPage}
              onOpenUploadPackage={() => setCurrentPage("Evidence Vault")}
            />
          )}

          {currentPage === "Endpoints" && (
            <EndpointsPage />
          )}

          {currentPage === "Collection Jobs" && (
            <CollectionJobsPage
              activeCase={activeCase}
              onNavigateToTimeline={() => setCurrentPage("Unified Timeline")}
              onNavigateToVault={() => setCurrentPage("Evidence Vault")}
            />
          )}

          {currentPage === "Evidence Vault" && (
            <EvidenceVaultPage
              activeCase={activeCase}
              evidenceItems={evidenceItems}
              onOpenUpload={() => setIsUploadOpen(true)}
              onRefreshEvidence={loadEvidence}
            />
          )}

          {currentPage === "Artifact Explorer" && (
            <ArtifactExplorerPage
              activeCase={activeCase}
              evidenceItems={evidenceItems}
              onAnalysisCompleted={() => {
                loadStats();
              }}
              onNavigateToTimeline={() => setCurrentPage("Unified Timeline")}
            />
          )}

          {currentPage === "Unified Timeline" && (
            <UnifiedTimelinePage
              activeCase={activeCase}
              onSelectEvent={setInspectingEvent}
            />
          )}

          {currentPage === "Validation Lab" && (
            <ValidationLabPage activeCase={activeCase} />
          )}

          {currentPage === "Reports" && (
            <ReportsPage activeCase={activeCase} />
          )}

          {currentPage === "Audit Log" && (
            <AuditLogPage />
          )}

          {currentPage === "Settings" && (
            <SettingsPage />
          )}

          {currentPage === "About" && (
            <AboutPage />
          )}
        </main>
      </div>

      {/* Modals */}
      <NewCaseModal
        isOpen={isNewCaseOpen}
        onClose={() => setIsNewCaseOpen(false)}
        onCaseCreated={handleCaseCreated}
      />

      {activeCase && (
        <UploadEvidenceModal
          isOpen={isUploadOpen}
          onClose={() => setIsUploadOpen(false)}
          caseId={activeCase.id}
          onUploaded={handleEvidenceUploaded}
        />
      )}

      <EventDetailModal
        event={inspectingEvent}
        onClose={() => setInspectingEvent(null)}
      />
    </div>
  );
}
