import React, { useEffect, useState } from "react";
import type { Claim } from "../types";
import { Badge } from "./ui/badge";
import { Card, CardContent } from "./ui/card";
import {
  Upload,
  FileSearch,
  Shield,
  GitBranch,
  UserCheck,
  PlayCircle,
  CheckCircle2,
  DollarSign,
  AlertTriangle,
  Clock,
  Trash2,
  Mail,
} from "lucide-react";
import { useSSE } from "../hooks/useSSE";
import { ProcessingStageIndicator } from "./ProcessingStageIndicator";
import { Notification } from "./ui/notification";

const API_BASE = "http://localhost:8080";

type KanbanColumn = {
  id: string;
  title: string;
  statuses: string[];
  icon: React.ComponentType<{ size?: number; className?: string }>;
  color: string;
};

const KANBAN_COLUMNS: KanbanColumn[] = [
  {
    id: "unassigned",
    title: "BACKLOGS",
    statuses: ["uploaded", "extracting", "scoring", "routing"],
    icon: Clock,
    color: "bg-white border-gray-200 text-gray-800",
  },
  {
    id: "in_progress",
    title: "IN PROGRESS",
    statuses: ["assigned", "auto_approved", "auto_routed", "in_progress"],
    icon: PlayCircle,
    color: "bg-white border-gray-200 text-gray-800",
  },
  {
    id: "review",
    title: "ON REVIEW",
    statuses: ["review", "pending_review"],
    icon: Shield,
    color: "bg-white border-gray-200 text-gray-800",
  },
  {
    id: "done",
    title: "DONE",
    statuses: ["completed", "closed", "approved"],
    icon: CheckCircle2,
    color: "bg-white border-gray-200 text-gray-800",
  },
];

export const KanbanBoard: React.FC = () => {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedClaim, setSelectedClaim] = useState<Claim | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [fetchingEmails, setFetchingEmails] = useState(false);
  const [notification, setNotification] = useState<{
    message: string;
    type: 'success' | 'error' | 'info' | 'loading';
  } | null>(null);

  // SSE for real-time stage updates
  const { lastEvent } = useSSE(`${API_BASE}/api/events/stream`);

  const fetchClaims = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/claims/list`);
      const data = await response.json();
      setClaims(data.claims || []);
    } catch (error) {
      console.error("Failed to fetch claims:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClaims();
    const interval = setInterval(fetchClaims, 2000); // Refresh every 2s for real-time updates
    return () => clearInterval(interval);
  }, []);

  // Handle SSE events for stage updates
  useEffect(() => {
    if (!lastEvent) return;

    // Handle claim_uploaded event - create placeholder if not exists
    if (lastEvent.type === "claim_uploaded" && lastEvent.claim_id) {
      setClaims((prevClaims) => {
        const exists = prevClaims.find(c => c.claim_id === lastEvent.claim_id);
        if (!exists) {
          // Create placeholder from SSE event
          const placeholderClaim: any = {
            claim_id: lastEvent.claim_id,
            status: lastEvent.status || "uploaded",
            current_stage: "extraction",
            file_paths: [],
            document_types: [],
            fraud_flags: [],
            created_at: new Date().toISOString(),
            extracted_data: null,
            severity_score: null,
            complexity_score: null,
            routing_decision: null
          };
          return [placeholderClaim, ...prevClaims];
        }
        return prevClaims;
      });
    }
    // Handle status update events
    else if (lastEvent.type === "claim_status_update" && lastEvent.claim_id && lastEvent.stage) {
      setClaims((prevClaims) =>
        prevClaims.map((claim) =>
          claim.claim_id === lastEvent.claim_id
            ? {
                ...claim,
                current_stage: lastEvent.stage,
                status: lastEvent.status || claim.status,
              }
            : claim
        )
      );
    }
    // Handle claim_processed event - refresh from server
    else if (lastEvent.type === "claim_processed" && lastEvent.claim_id) {
      // Fetch the complete claim from server
      fetchClaims();
    }
  }, [lastEvent]);

  const getClaimsForColumn = (column: KanbanColumn): Claim[] => {
    return claims.filter((claim) => column.statuses.includes(claim.status));
  };

  const handleDragStart = (e: React.DragEvent, claim: Claim) => {
    e.dataTransfer.setData("claimId", claim.claim_id);
    e.dataTransfer.effectAllowed = "move";
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
  };

  const handleDrop = async (e: React.DragEvent, column: KanbanColumn) => {
    e.preventDefault();
    const claimId = e.dataTransfer.getData("claimId");
    const targetStatus = column.statuses[0]; // Use first status in column

    try {
      const response = await fetch(`${API_BASE}/api/claims/${claimId}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: targetStatus }),
      });

      if (response.ok) {
        await fetchClaims(); // Refresh claims
      }
    } catch (error) {
      console.error("Failed to update claim status:", error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          <p className="text-muted-foreground">Loading kanban board...</p>
        </div>
      </div>
    );
  }

  const getClaimTypeColor = (incidentType?: string) => {
    if (!incidentType) return "bg-gray-100 text-gray-700";
    const type = incidentType.toLowerCase();
    if (type.includes("auto") || type.includes("vehicle"))
      return "bg-lime-100 text-lime-700 border-lime-300";
    if (type.includes("property") || type.includes("home"))
      return "bg-blue-100 text-blue-700 border-blue-300";
    if (type.includes("injury") || type.includes("medical"))
      return "bg-violet-100 text-violet-700 border-violet-300";
    return "bg-gray-100 text-gray-700 border-gray-300";
  };

  const getProcessingProgress = (claim: Claim): number => {
    // Calculate progress based on current_stage if available, otherwise status
    if (claim.current_stage) {
      const stageProgress: Record<string, number> = {
        extraction: 25,
        scoring: 50,
        fraud_detection: 65,
        auto_processing: 70,
        routing: 85,
      };
      return stageProgress[claim.current_stage] || 20;
    }

    // Fallback to status-based progress
    const statusProgress: Record<string, number> = {
      uploaded: 10,
      extracting: 30,
      scoring: 50,
      routing: 70,
      assigned: 90,
      in_progress: 90,
      review: 95,
      completed: 100,
      closed: 100,
      approved: 100,
    };
    return statusProgress[claim.status] || 0;
  };

  const getStatusTags = (claim: Claim): string[] => {
    const tags: string[] = [];

    // Add status-based tags
    if (claim.current_stage) {
      tags.push(claim.current_stage.toUpperCase().replace("_", " "));
    }

    // Add fraud tag if present
    if (claim.fraud_flags && claim.fraud_flags.length > 0) {
      tags.push("FRAUD ALERT");
    }

    // Add priority tag
    if (claim.routing_decision?.priority) {
      tags.push(claim.routing_decision.priority.toUpperCase());
    }

    // Add complexity tag
    if (claim.complexity_score && claim.complexity_score > 70) {
      tags.push("COMPLEX");
    }

    return tags;
  };

  const getTagColor = (tag: string): string => {
    if (tag.includes("FRAUD")) return "bg-red-100 text-red-700 border-red-300";
    if (tag.includes("URGENT") || tag.includes("HIGH"))
      return "bg-orange-100 text-orange-700 border-orange-300";
    if (tag.includes("COMPLEX"))
      return "bg-purple-100 text-purple-700 border-purple-300";
    if (tag.includes("EXTRACTING") || tag.includes("SCORING"))
      return "bg-blue-100 text-blue-700 border-blue-300";
    if (tag.includes("ROUTING"))
      return "bg-yellow-100 text-yellow-700 border-yellow-300";
    return "bg-gray-100 text-gray-700 border-gray-300";
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const API_BASE = "http://localhost:8080";
    const formData = new FormData();
    formData.append("file", file);

    // Show uploading notification
    setUploading(true);
    setNotification({
      message: `Uploading ${file.name}...`,
      type: 'loading'
    });

    try {
      const response = await fetch(`${API_BASE}/api/claims/upload`, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();

        // Create placeholder claim immediately
        const placeholderClaim: any = {
          claim_id: data.claim_id,
          status: "uploaded",
          current_stage: "extraction",
          file_paths: [file.name],
          document_types: [],
          fraud_flags: [],
          created_at: new Date().toISOString(),
          extracted_data: null,
          severity_score: null,
          complexity_score: null,
          routing_decision: null
        };

        // Add placeholder to state immediately
        setClaims(prevClaims => [placeholderClaim, ...prevClaims]);

        // Show success notification
        setNotification({
          message: `Upload successful! Processing ${data.claim_id.substring(0, 15)}...`,
          type: 'success'
        });
      } else {
        // Show error notification
        setNotification({
          message: 'Upload failed. Please try again.',
          type: 'error'
        });
      }
    } catch (error) {
      console.error("Upload error:", error);
      // Show error notification
      setNotification({
        message: 'Upload failed. Check your connection.',
        type: 'error'
      });
    } finally {
      setUploading(false);
      e.target.value = ""; // Reset input
    }
  };

  const handleFetchEmails = async () => {
    setFetchingEmails(true);
    setNotification({
      message: 'Fetching claim emails from Gmail...',
      type: 'loading'
    });

    try {
      const response = await fetch(`${API_BASE}/api/gmail/auto-fetch/fetch-now`, {
        method: 'POST',
      });

      const data = await response.json();

      if (response.ok) {
        setNotification({
          message: `✅ Fetched ${data.emails_processed} of ${data.emails_found} emails`,
          type: 'success'
        });
        // Refresh claims to show newly fetched ones
        setTimeout(() => fetchClaims(), 2000);
      } else {
        setNotification({
          message: data.detail || 'Failed to fetch emails',
          type: 'error'
        });
      }
    } catch (error) {
      setNotification({
        message: 'Failed to fetch emails: ' + (error as Error).message,
        type: 'error'
      });
    } finally {
      setFetchingEmails(false);
    }
  };

  const handleDeleteClaim = async () => {
    if (!selectedClaim) return;

    setDeleteError(null);

    try {
      const response = await fetch(`${API_BASE}/api/claims/${selectedClaim.claim_id}`, {
        method: "DELETE",
      });

      if (response.ok) {
        // Remove from local state
        setClaims(prevClaims => prevClaims.filter(c => c.claim_id !== selectedClaim.claim_id));
        // Close modal
        setSelectedClaim(null);
        setShowDeleteConfirm(false);
      } else {
        const data = await response.json();
        setDeleteError(data.detail || "Failed to delete claim");
      }
    } catch (error) {
      setDeleteError("Failed to delete claim: " + (error as Error).message);
    }
  };

  return (
    <div
      className="w-full h-full p-6 bg-white rounded-3xl shadow-2xl space-y-6 flex flex-col"
      style={{
        boxShadow:
          "0 25px 50px -12px rgba(91, 104, 242, 0.35), 0 10px 30px -10px rgba(139, 92, 246, 0.3)",
      }}
    >
      {/* Top Header */}
      <div className="flex items-center justify-between pb-4 border-b border-gray-200">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Board</h2>
          <p className="text-xs text-gray-500 mt-1">
            ClaimPilot • Real-time claim triage
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleFetchEmails}
            disabled={fetchingEmails}
            className={`px-5 py-2.5 text-sm font-semibold rounded-lg transition-colors flex items-center gap-2 ${
              fetchingEmails
                ? 'bg-gray-400 text-white cursor-not-allowed'
                : 'bg-blue-500 hover:bg-blue-600 text-white'
            }`}
          >
            <Mail size={16} className={fetchingEmails ? 'animate-pulse' : ''} />
            {fetchingEmails ? 'Fetching...' : 'Fetch Emails'}
          </button>
          <label className={`px-5 py-2.5 text-sm font-semibold text-white rounded-lg transition-colors flex items-center gap-2 ${
            uploading
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-primary hover:bg-primary/90 cursor-pointer'
          }`}>
            <Upload size={16} className={uploading ? 'animate-pulse' : ''} />
            {uploading ? 'Uploading...' : 'Upload Claim'}
            <input
              type="file"
              onChange={handleFileUpload}
              accept=".pdf,.txt,.doc,.docx,.jpg,.jpeg,.png"
              className="hidden"
              disabled={uploading}
            />
          </label>
          <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M10 6V10M10 14H10.01M19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Kanban Columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 flex-1">
        {KANBAN_COLUMNS.map((column) => {
          const columnClaims = getClaimsForColumn(column);

          return (
            <div
              key={column.id}
              className="flex flex-col"
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, column)}
            >
              {/* Column Header */}
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-bold text-xs text-gray-700 tracking-wide uppercase">
                  {column.title}
                </h3>
                <span className="text-xs text-gray-500 font-semibold bg-gray-200 px-2 py-0.5 rounded-full">
                  {columnClaims.length}
                </span>
              </div>

              {/* Column Content */}
              <div className="flex-1 bg-gray-100 border border-gray-200 rounded-lg p-3 space-y-3 min-h-[75vh]">
                {columnClaims.map((claim) => (
                  <Card
                    key={claim.claim_id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, claim)}
                    onClick={() => setSelectedClaim(claim)}
                    className="cursor-move hover:shadow-md transition-all duration-200 bg-white border border-gray-200"
                  >
                    <CardContent className="p-4">
                      <div className="space-y-3">
                        {/* Claim ID - Show full unique ID */}
                        <div className="space-y-1">
                          <div className="flex items-center justify-between">
                            <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Claim ID</p>
                            {claim.source === "gmail" && (
                              <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-300">
                                <Mail size={10} className="mr-1" />
                                Email
                              </Badge>
                            )}
                          </div>
                          <h4 className="font-bold text-sm text-primary leading-tight font-mono">
                            {claim.claim_id}
                          </h4>
                          {claim.extracted_data?.incident_type && (
                            <p className="text-xs text-gray-600 capitalize">
                              {claim.extracted_data.incident_type}
                            </p>
                          )}
                        </div>

                        {/* Processing Stage Indicator - Show prominently for claims in processing */}
                        {claim.current_stage && (
                          <div className="my-2">
                            <ProcessingStageIndicator stage={claim.current_stage} />
                          </div>
                        )}

                        {/* Progress Bar with Percentage */}
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <span className="text-xs font-semibold text-orange-600">
                              {getProcessingProgress(claim)}% completed
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-1.5">
                            <div
                              className="bg-gradient-to-r from-orange-400 to-orange-600 h-1.5 rounded-full transition-all duration-300"
                              style={{
                                width: `${getProcessingProgress(claim)}%`,
                              }}
                            ></div>
                          </div>
                        </div>

                        {/* Status Tags */}
                        <div className="flex flex-wrap gap-1.5">
                          {/* Type Tag */}
                          {claim.extracted_data?.incident_type && (
                            <span
                              className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border uppercase ${getClaimTypeColor(
                                claim.extracted_data.incident_type
                              )}`}
                            >
                              {claim.extracted_data.incident_type.substring(
                                0,
                                12
                              )}
                            </span>
                          )}

                          {/* Additional Status Tags */}
                          {getStatusTags(claim)
                            .slice(0, 2)
                            .map((tag, idx) => (
                              <span
                                key={idx}
                                className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold border ${getTagColor(
                                  tag
                                )}`}
                              >
                                {tag}
                              </span>
                            ))}
                        </div>

                        {/* Amount and Scores Row */}
                        <div className="flex items-center justify-between text-xs text-gray-600">
                          {claim.extracted_data?.claim_amount && (
                            <div className="flex items-center gap-1">
                              <DollarSign
                                size={12}
                                className="text-green-600"
                              />
                              <span className="font-bold text-green-700">
                                $
                                {(
                                  claim.extracted_data.claim_amount / 1000
                                ).toFixed(1)}
                                K
                              </span>
                            </div>
                          )}
                          <div className="flex gap-2">
                            {claim.severity_score !== undefined && claim.severity_score !== null && (
                              <span className="text-orange-600 font-semibold">
                                S:{claim.severity_score.toFixed(0)}
                              </span>
                            )}
                            {claim.complexity_score !== undefined && claim.complexity_score !== null && (
                              <span className="text-purple-600 font-semibold">
                                C:{claim.complexity_score.toFixed(0)}
                              </span>
                            )}
                          </div>
                        </div>

                        {/* Bottom: Avatars and Status Icons */}
                        <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                          <div className="flex items-center -space-x-2">
                            {/* AI Agent or Human Avatar */}
                            {claim.routing_decision?.assigned_to ? (
                              // Human adjuster
                              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-violet-400 to-purple-500 flex items-center justify-center text-white text-[10px] font-bold border-2 border-white">
                                {claim.routing_decision.assigned_to
                                  .charAt(0)
                                  .toUpperCase()}
                              </div>
                            ) : (
                              // AI Agent
                              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-400 to-cyan-500 flex items-center justify-center text-white text-[10px] font-bold border-2 border-white">
                                🤖
                              </div>
                            )}

                            {/* Additional team members placeholder */}
                            {claim.routing_decision?.assigned_to && (
                              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-pink-400 to-rose-500 flex items-center justify-center text-white text-[10px] font-bold border-2 border-white">
                                +2
                              </div>
                            )}
                          </div>

                          {/* Status Icons */}
                          <div className="flex items-center gap-1">
                            {claim.fraud_flags &&
                              claim.fraud_flags.length > 0 && (
                                <div
                                  className="text-red-500"
                                  title="Fraud Alert"
                                >
                                  <AlertTriangle size={14} />
                                </div>
                              )}
                            {claim.routing_decision?.priority === "urgent" && (
                              <div
                                className="text-orange-500"
                                title="Urgent Priority"
                              >
                                ⚠️
                              </div>
                            )}
                            {getProcessingProgress(claim) === 100 && (
                              <div className="text-green-500" title="Completed">
                                <CheckCircle2 size={14} />
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}

                {columnClaims.length === 0 && (
                  <div className="text-center py-8 text-sm text-muted-foreground">
                    No claims
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Claim Details Modal */}
      {selectedClaim && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-[9999] animate-fade-in"
          onClick={() => setSelectedClaim(null)}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl max-w-7xl w-full min-h-[90vh] max-h-[90vh] overflow-hidden animate-slide-in relative z-[10000]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="sticky top-0 bg-gradient-to-r from-primary to-violet-600 p-6 flex justify-between items-start">
              <div>
                <h3 className="text-2xl font-bold text-white">
                  {selectedClaim.claim_id}
                </h3>
                <p className="text-white/80 text-sm mt-1">
                  {selectedClaim.extracted_data?.incident_type ||
                    "Unknown Type"}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors text-white"
                  title="Delete claim"
                >
                  <Trash2 size={20} />
                </button>
                <button
                  onClick={() => {
                    setSelectedClaim(null);
                    setShowDeleteConfirm(false);
                    setDeleteError(null);
                  }}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors text-white"
                >
                  ✕
                </button>
              </div>
            </div>

            <div className="flex gap-6 max-h-[calc(90vh-120px)]">
              {/* Left side: Document Viewer */}
              <div className="w-1/2 bg-gray-100 overflow-hidden flex flex-col">
                <div className="p-4 bg-gray-200 border-b border-gray-300">
                  <h4 className="font-semibold text-gray-700 text-sm">Original Document</h4>
                </div>
                <div className="flex-1 overflow-auto p-4">
                  {selectedClaim.file_paths && selectedClaim.file_paths.length > 0 ? (
                    (() => {
                      const filePath = selectedClaim.file_paths[0];
                      const fileName = filePath.split('/').pop() || '';
                      const fileUrl = `${API_BASE}/uploads/${fileName}`;
                      const fileExt = fileName.split('.').pop()?.toLowerCase();

                      if (fileExt === 'pdf') {
                        return (
                          <iframe
                            src={fileUrl}
                            className="w-full h-full border-0 rounded-lg"
                            title="Document Viewer"
                          />
                        );
                      } else if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(fileExt || '')) {
                        return (
                          <img
                            src={fileUrl}
                            alt="Document"
                            className="w-full h-auto rounded-lg border border-gray-300"
                          />
                        );
                      } else {
                        return (
                          <div className="flex flex-col items-center justify-center h-full text-gray-500">
                            <p className="text-sm mb-2">Preview not available</p>
                            <a
                              href={fileUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary hover:underline text-sm font-semibold"
                            >
                              Download File
                            </a>
                          </div>
                        );
                      }
                    })()
                  ) : (
                    <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                      No document available
                    </div>
                  )}
                </div>
              </div>

              {/* Right side: Claim Details */}
              <div className="w-1/2 p-6 overflow-y-auto space-y-6">
              {/* Delete Confirmation */}
              {showDeleteConfirm && (
                <div className="bg-red-50 border-2 border-red-300 rounded-xl p-4">
                  <p className="text-sm font-semibold text-red-800 mb-3">
                    Are you sure you want to delete this claim? This action cannot be undone.
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={handleDeleteClaim}
                      className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-semibold transition-colors"
                    >
                      Yes, Delete
                    </button>
                    <button
                      onClick={() => {
                        setShowDeleteConfirm(false);
                        setDeleteError(null);
                      }}
                      className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg text-sm font-semibold transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {/* Delete Error */}
              {deleteError && (
                <div className="bg-red-50 border border-red-300 rounded-lg p-4 text-red-800 text-sm">
                  {deleteError}
                </div>
              )}

              {/* Scores Section */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-orange-50 p-4 rounded-xl border border-orange-200">
                  <p className="text-xs text-orange-600 font-semibold uppercase mb-1">
                    Severity Score
                  </p>
                  <p className="text-3xl font-bold text-orange-700">
                    {selectedClaim.severity_score?.toFixed(0) || "N/A"}
                    <span className="text-lg">/100</span>
                  </p>
                </div>
                <div className="bg-purple-50 p-4 rounded-xl border border-purple-200">
                  <p className="text-xs text-purple-600 font-semibold uppercase mb-1">
                    Complexity Score
                  </p>
                  <p className="text-3xl font-bold text-purple-700">
                    {selectedClaim.complexity_score?.toFixed(0) || "N/A"}
                    <span className="text-lg">/100</span>
                  </p>
                </div>
              </div>

              {/* Assignment Section */}
              {selectedClaim.routing_decision && (
                <div>
                  <h4 className="font-semibold text-lg text-foreground mb-3 flex items-center gap-2">
                    <UserCheck size={20} className="text-violet-600" />
                    Assignment Details
                  </h4>
                  <div className="bg-gradient-to-br from-violet-50 to-purple-50 p-5 rounded-xl border border-violet-200 space-y-3">
                    <div className="flex items-center justify-between pb-3 border-b border-violet-200">
                      <div>
                        <p className="text-xs text-violet-600 font-semibold uppercase mb-1">
                          Assigned To
                        </p>
                        <p className="text-xl font-bold text-violet-800">
                          {selectedClaim.routing_decision.assigned_to}
                        </p>
                      </div>
                      {selectedClaim.routing_decision.adjuster_id && (
                        <div className="text-right">
                          <p className="text-xs text-violet-600 font-semibold uppercase mb-1">
                            User ID
                          </p>
                          <p className="text-sm font-mono font-semibold text-violet-700">
                            {selectedClaim.routing_decision.adjuster_id}
                          </p>
                        </div>
                      )}
                    </div>

                    <div>
                      <p className="text-xs text-violet-600 font-semibold uppercase mb-1">
                        Priority
                      </p>
                      <Badge
                        variant={
                          selectedClaim.routing_decision.priority === "urgent"
                            ? "destructive"
                            : selectedClaim.routing_decision.priority === "high"
                            ? "warning"
                            : "default"
                        }
                        className="text-sm"
                      >
                        {selectedClaim.routing_decision.priority?.toUpperCase()}
                      </Badge>
                    </div>

                    <div>
                      <p className="text-xs text-violet-600 font-semibold uppercase mb-1">
                        Assignment Reason
                      </p>
                      <p className="text-sm text-gray-700 bg-white p-3 rounded-lg border border-violet-100">
                        {selectedClaim.routing_decision.reason}
                      </p>
                    </div>

                    {selectedClaim.routing_decision
                      .estimated_workload_hours && (
                      <div>
                        <p className="text-xs text-violet-600 font-semibold uppercase mb-1">
                          Estimated Hours
                        </p>
                        <p className="text-lg font-bold text-violet-700">
                          {
                            selectedClaim.routing_decision
                              .estimated_workload_hours
                          }{" "}
                          hours
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Fraud Flags */}
              {selectedClaim.fraud_flags &&
                selectedClaim.fraud_flags.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-lg text-red-700 mb-3 flex items-center gap-2">
                      <AlertTriangle size={20} />
                      Fraud Alerts ({selectedClaim.fraud_flags.length})
                    </h4>
                    <div className="space-y-2">
                      {selectedClaim.fraud_flags.map((flag, idx) => (
                        <div
                          key={idx}
                          className="bg-red-50 border-l-4 border-red-500 p-3 rounded"
                        >
                          <div className="flex justify-between items-start mb-1">
                            <p className="font-bold text-red-800 text-sm uppercase">
                              {flag.type.replace(/_/g, " ")}
                            </p>
                            <Badge variant="destructive" className="text-xs">
                              {flag.severity}
                            </Badge>
                          </div>
                          <p className="text-xs text-gray-700">
                            {flag.evidence}
                          </p>
                          <div className="mt-2 flex items-center gap-2">
                            <div className="flex-1 bg-white rounded-full h-1.5 overflow-hidden">
                              <div
                                className="h-full bg-red-500"
                                style={{ width: `${flag.confidence * 100}%` }}
                              ></div>
                            </div>
                            <span className="text-xs font-semibold text-red-700">
                              {(flag.confidence * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              {/* Claim Details */}
              <div>
                <h4 className="font-semibold text-lg text-foreground mb-3">
                  Claim Details
                </h4>
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2 text-sm">
                  {selectedClaim.extracted_data?.claim_amount && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Amount:</span>
                      <span className="font-bold text-blue-700">
                        $
                        {selectedClaim.extracted_data.claim_amount.toLocaleString()}
                      </span>
                    </div>
                  )}
                  {selectedClaim.extracted_data?.incident_type && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Type:</span>
                      <span className="font-semibold">
                        {selectedClaim.extracted_data.incident_type}
                      </span>
                    </div>
                  )}
                  {selectedClaim.status && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Status:</span>
                      <Badge variant="default">{selectedClaim.status}</Badge>
                    </div>
                  )}
                  {selectedClaim.processing_time_seconds && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Processing Time:</span>
                      <span className="font-semibold">
                        {selectedClaim.processing_time_seconds.toFixed(1)}s
                      </span>
                    </div>
                  )}
                </div>
              </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Inline Notification at Bottom */}
      {notification && (
        <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 z-[10000]">
          <Notification
            message={notification.message}
            type={notification.type}
            onClose={() => setNotification(null)}
            duration={notification.type === 'loading' ? 0 : 4000}
          />
        </div>
      )}
    </div>
  );
};
