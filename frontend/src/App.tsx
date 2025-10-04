import { useState, useCallback } from "react";
import { ClaimsQueue } from "./components/ClaimsQueue";
import { AdjusterPanel } from "./components/AdjusterPanel";
import { MetricsPanel } from "./components/MetricsPanel";
import { FraudAlerts } from "./components/FraudAlerts";
import { UploadClaim } from "./components/UploadClaim";
import { KanbanBoard } from "./components/KanbanBoard";
import { ChatPanel } from "./components/ChatPanel";
import { useKeyboardShortcut } from "./hooks/useKeyboardShortcut";
import {
  FileText,
  Users,
  AlertTriangle,
  Menu,
  X,
  Kanban,
  ChevronLeft,
  ChevronRight,
  Upload,
} from "lucide-react";
import "./App.css";

const API_BASE = "http://localhost:8080";

function App() {
  const [activeTab, setActiveTab] = useState<
    "claims" | "kanban" | "adjusters" | "fraud"
  >("kanban");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [selectedClaimId, setSelectedClaimId] = useState<string | null>(null);

  // Keyboard shortcut: Shift+L to toggle chat
  const toggleChat = useCallback(() => {
    setChatOpen((prev) => !prev);
  }, []);

  useKeyboardShortcut({ key: "l", shift: true }, toggleChat);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${API_BASE}/api/claims/upload`, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        alert("✅ Claim uploaded successfully! Processing will begin shortly.");
      } else {
        alert("❌ Upload failed. Please try again.");
      }
    } catch (error) {
      console.error("Upload error:", error);
      alert("❌ Upload failed. Please try again.");
    } finally {
      setUploading(false);
      e.target.value = ""; // Reset input
    }
  };

  const navItems = [
    { id: "claims" as const, label: "Claims Queue", icon: FileText },
    { id: "kanban" as const, label: "Kanban Board", icon: Kanban },
    { id: "adjusters" as const, label: "Adjusters", icon: Users },
    { id: "fraud" as const, label: "Fraud Alerts", icon: AlertTriangle },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-200 via-purple-200 to-pink-200">
      {/* Chat Panel */}
      <ChatPanel
        isOpen={chatOpen}
        onClose={() => setChatOpen(false)}
        selectedClaimId={selectedClaimId}
      />
      {/* Minimal Header - Only for mobile menu */}
      {activeTab !== "kanban" && (
        <header className="sticky top-0 z-50 backdrop-blur-lg bg-white shadow-sm border-b border-gray-200 lg:hidden">
          <div className="px-4 py-3 flex items-center justify-between">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
            <label
              className={`
              flex items-center gap-2 px-4 py-2 rounded-lg font-semibold cursor-pointer transition-all duration-200
              ${
                uploading
                  ? "bg-gray-300 text-gray-600 cursor-not-allowed"
                  : "bg-primary text-white"
              }
            `}
            >
              <Upload size={18} />
              <input
                type="file"
                onChange={handleFileUpload}
                disabled={uploading}
                accept=".pdf,.txt,.doc,.docx,.jpg,.jpeg,.png"
                className="hidden"
              />
            </label>
          </div>
        </header>
      )}

      {/* Mobile Navigation Overlay */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Container */}
      <div className="flex min-h-screen">
        {/* Sidebar Navigation */}
        <aside
          className={`
          ${sidebarOpen ? "fixed inset-y-0 left-0 z-40" : "hidden"} lg:block
          gradient-violet transition-all duration-300
          ${sidebarCollapsed ? "w-20" : "w-64"}
        `}
        >
          <div className="relative h-full">
            {/* Logo/Brand Section */}
            <div
              className={`p-6 border-b border-white/20 ${
                sidebarCollapsed ? "flex justify-center" : ""
              }`}
            >
              {sidebarCollapsed ? (
                <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                  <svg
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M12 2L2 7L12 12L22 7L12 2Z"
                      stroke="white"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <path
                      d="M2 17L12 22L22 17"
                      stroke="white"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <path
                      d="M2 12L12 17L22 12"
                      stroke="white"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center flex-shrink-0">
                    <svg
                      width="24"
                      height="24"
                      viewBox="0 0 24 24"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        d="M12 2L2 7L12 12L22 7L12 2Z"
                        stroke="white"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                      <path
                        d="M2 17L12 22L22 17"
                        stroke="white"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                      <path
                        d="M2 12L12 17L22 12"
                        stroke="white"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-white">ClaimPilot</h2>
                  </div>
                </div>
              )}
            </div>

            <nav className="p-4 space-y-2 mt-2">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      setActiveTab(item.id);
                      setSidebarOpen(false);
                    }}
                    className={`
                      w-full flex items-center gap-3 px-4 py-3 rounded-lg
                      font-medium transition-all duration-200
                      ${
                        isActive
                          ? "bg-white text-violet-700 shadow-lg"
                          : "text-white hover:bg-white/20"
                      }
                      ${sidebarCollapsed ? "justify-center px-3" : ""}
                    `}
                    title={sidebarCollapsed ? item.label : undefined}
                  >
                    <Icon size={20} className="flex-shrink-0" />
                    {!sidebarCollapsed && <span>{item.label}</span>}
                  </button>
                );
              })}
            </nav>

            {/* Collapse/Expand Button */}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="absolute bottom-6 left-1/2 -translate-x-1/2 p-2.5 bg-white/20 hover:bg-white/30 rounded-lg transition-colors hidden lg:flex items-center justify-center text-white shadow-lg"
              title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            >
              {sidebarCollapsed ? (
                <ChevronRight size={20} />
              ) : (
                <ChevronLeft size={20} />
              )}
            </button>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 gradient-violet">
          <div
            className={`${
              activeTab === "kanban"
                ? "p-6 h-full max-w-7xl overflow-y-auto"
                : "max-w-7xl p-6 h-full overflow-y-auto"
            } mx-auto animate-fade-in`}
          >
            {/* Show Metrics and Upload only for non-Kanban views */}
            {activeTab !== "kanban" && (
              <>
                <div className="flex items-center justify-between mb-6">
                  <h1 className="text-3xl font-bold text-gray-800">
                    {activeTab === "claims"
                      ? "Claims Queue"
                      : activeTab === "adjusters"
                      ? "Adjusters"
                      : "Fraud Alerts"}
                  </h1>
                  <label
                    className={`
                    flex items-center gap-2 px-4 py-2 rounded-lg font-semibold cursor-pointer transition-all duration-200
                    ${
                      uploading
                        ? "bg-gray-300 text-gray-600 cursor-not-allowed"
                        : "bg-primary text-white hover:shadow-lg"
                    }
                  `}
                  >
                    <Upload size={18} />
                    <span>{uploading ? "Uploading..." : "Upload"}</span>
                    <input
                      type="file"
                      onChange={handleFileUpload}
                      disabled={uploading}
                      accept=".pdf,.txt,.doc,.docx,.jpg,.jpeg,.png"
                      className="hidden"
                    />
                  </label>
                </div>
                <MetricsPanel />
                <div className="grid grid-cols-1 gap-6">
                  <UploadClaim />
                </div>
              </>
            )}

            {/* Content Area */}
            <div
              className={
                activeTab === "kanban"
                  ? ""
                  : "bg-white/80 backdrop-blur-sm rounded-xl shadow-lg border border-gray-200 overflow-hidden"
              }
            >
              <div className={activeTab === "kanban" ? "" : "p-6"}>
                {activeTab === "claims" && <ClaimsQueue />}
                {activeTab === "kanban" && <KanbanBoard />}
                {activeTab === "adjusters" && <AdjusterPanel />}
                {activeTab === "fraud" && <FraudAlerts />}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
