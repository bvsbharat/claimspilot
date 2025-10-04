import React, { useEffect, useState } from 'react';
import type { Claim } from '../types';
import { ClaimCard } from './ClaimCard';
import { Badge } from './ui/badge';
import { X, FileText, AlertTriangle, User, CheckCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8080';

export const ClaimsQueue: React.FC = () => {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedClaim, setSelectedClaim] = useState<Claim | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deleteSuccess, setDeleteSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'document' | 'text'>('document');
  const [processedText, setProcessedText] = useState<string>('');
  const [textLoading, setTextLoading] = useState(false);
  const [textError, setTextError] = useState<string | null>(null);

  const fetchClaims = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/claims/list`);
      const data = await response.json();
      setClaims(data.claims || []);
    } catch (error) {
      console.error('Failed to fetch claims:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClaim = async (claimId: string) => {
    setDeleteError(null);
    setDeleteSuccess(null);

    try {
      const response = await fetch(`${API_BASE}/api/claims/${claimId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setDeleteSuccess(`Claim ${claimId} deleted successfully`);
        // Remove claim from local state
        setClaims(prevClaims => prevClaims.filter(c => c.claim_id !== claimId));
        // Close modal if this claim was selected
        if (selectedClaim?.claim_id === claimId) {
          setSelectedClaim(null);
        }
        // Clear success message after 3 seconds
        setTimeout(() => setDeleteSuccess(null), 3000);
      } else {
        const data = await response.json();
        setDeleteError(data.detail || 'Failed to delete claim');
        // Clear error message after 5 seconds
        setTimeout(() => setDeleteError(null), 5000);
      }
    } catch (error) {
      setDeleteError('Failed to delete claim: ' + (error as Error).message);
      setTimeout(() => setDeleteError(null), 5000);
    }
  };

  const fetchProcessedText = async (claimId: string) => {
    setTextLoading(true);
    setTextError(null);

    try {
      // First try to get from the claim's extracted_text field
      if (selectedClaim?.extracted_text) {
        setProcessedText(selectedClaim.extracted_text);
        setTextLoading(false);
        return;
      }

      // If not available, try the API endpoint
      const response = await fetch(`${API_BASE}/api/chat/processed-data/${claimId}`);

      if (response.ok) {
        const data = await response.json();
        setProcessedText(data.raw_text || 'No processed text available');
      } else {
        setTextError('Processed text not available for this claim');
      }
    } catch (error) {
      console.error('Failed to fetch processed text:', error);
      setTextError('Failed to load processed text');
    } finally {
      setTextLoading(false);
    }
  };

  useEffect(() => {
    let abortController = new AbortController();

    const fetchWithAbort = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/claims/list`, {
          signal: abortController.signal
        });
        const data = await response.json();
        setClaims(data.claims || []);
      } catch (error) {
        if (error.name !== 'AbortError') {
          console.error('Failed to fetch claims:', error);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchWithAbort();
    const interval = setInterval(() => {
      abortController.abort();
      abortController = new AbortController();
      fetchWithAbort();
    }, 15000); // Increased from 5s to 15s

    return () => {
      clearInterval(interval);
      abortController.abort();
    };
  }, []);

  // Reset states when modal is opened/closed
  useEffect(() => {
    if (selectedClaim) {
      setActiveTab('document');
      setProcessedText('');
      setTextError(null);
      setTextLoading(false);
    }
  }, [selectedClaim]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          <p className="text-muted-foreground">Loading claims...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-foreground flex items-center gap-2">
            <FileText size={28} className="text-primary" />
            Claims Queue
          </h2>
          <p className="text-sm text-muted-foreground mt-1">Manage and review all insurance claims</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-teal-50 to-cyan-50 border border-teal-200">
          <span className="text-sm text-muted-foreground">Total:</span>
          <span className="text-2xl font-bold text-teal-700">{claims.length}</span>
        </div>
      </div>

      {deleteSuccess && (
        <div className="p-4 bg-green-50 border border-green-300 rounded-lg text-green-800 animate-fade-in">
          {deleteSuccess}
        </div>
      )}

      {deleteError && (
        <div className="p-4 bg-red-50 border border-red-300 rounded-lg text-red-800 animate-fade-in">
          {deleteError}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {claims.map((claim, index) => (
          <div
            key={claim.claim_id}
            className="animate-fade-in"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <ClaimCard
              claim={claim}
              onClick={() => setSelectedClaim(claim)}
              onDelete={handleDeleteClaim}
            />
          </div>
        ))}
      </div>

      {claims.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-20 h-20 bg-gradient-to-br from-teal-100 to-cyan-100 rounded-full flex items-center justify-center mb-4">
            <FileText size={40} className="text-teal-600" />
          </div>
          <p className="text-xl font-semibold text-foreground">No claims in queue</p>
          <p className="text-sm text-muted-foreground mt-2">Upload a claim document to get started</p>
        </div>
      )}

      {/* Modal for claim details */}
      {selectedClaim && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-[9999] animate-fade-in"
          onClick={() => setSelectedClaim(null)}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl max-w-7xl w-full min-h-[90vh] max-h-[90vh] flex flex-col overflow-hidden animate-slide-in relative z-[10000]"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="bg-gradient-to-r from-teal-500 to-cyan-500 p-4 flex justify-between items-start shrink-0">
              <div>
                <h3 className="text-2xl font-bold text-white">{selectedClaim.claim_id}</h3>
                <p className="text-teal-100 text-sm mt-1">
                  {selectedClaim.extracted_data?.incident_type || 'Unknown Type'}
                </p>
              </div>
              <div className="flex items-center gap-2">
                {/* Tab Toggle */}
                <div className="flex gap-2 bg-white/20 p-1 rounded-lg">
                  <button
                    onClick={() => setActiveTab('document')}
                    className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                      activeTab === 'document'
                        ? 'bg-white text-teal-600 shadow-sm'
                        : 'text-white hover:bg-white/10'
                    }`}
                  >
                    Document
                  </button>
                  <button
                    onClick={() => {
                      setActiveTab('text');
                      if (!processedText && !textLoading) {
                        fetchProcessedText(selectedClaim.claim_id);
                      }
                    }}
                    className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                      activeTab === 'text'
                        ? 'bg-white text-teal-600 shadow-sm'
                        : 'text-white hover:bg-white/10'
                    }`}
                  >
                    Extracted Text
                  </button>
                </div>
                <button
                  onClick={() => setSelectedClaim(null)}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                >
                  <X size={24} className="text-white" />
                </button>
              </div>
            </div>

            {/* Main Content - Two Column Layout */}
            <div className="flex-1 flex overflow-hidden min-h-0">
              {/* Left Column - Document View */}
              <div className="w-1/2 bg-slate-50 p-4 flex flex-col min-h-0">
                <div className="bg-white rounded-xl border border-slate-200 flex-1 overflow-y-auto">
                  {activeTab === 'document' ? (
                    <div className="p-4 h-full">
                      {selectedClaim.file_paths && selectedClaim.file_paths.length > 0 ? (
                        <img
                          src={`${API_BASE}${selectedClaim.file_paths[0]}`}
                          alt="Claim Document"
                          className="w-full h-auto rounded-lg"
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = 'none';
                            const parent = (e.target as HTMLElement).parentElement;
                            if (parent) {
                              parent.innerHTML = '<p class="text-gray-500 text-center py-8">Document preview not available</p>';
                            }
                          }}
                        />
                      ) : (
                        <p className="text-gray-500 text-center py-8">No document available</p>
                      )}
                    </div>
                  ) : (
                    <div className="p-4 h-full">
                      {textLoading ? (
                        <div className="flex items-center justify-center py-8">
                          <div className="w-8 h-8 border-4 border-teal-500 border-t-transparent rounded-full animate-spin"></div>
                          <span className="ml-3 text-gray-600">Loading processed text...</span>
                        </div>
                      ) : textError ? (
                        <div className="text-red-600 text-center py-8">
                          <AlertTriangle size={24} className="mx-auto mb-2" />
                          <p>{textError}</p>
                        </div>
                      ) : processedText ? (
                        <div className="prose prose-sm max-w-none">
                          <pre className="text-sm text-slate-700 whitespace-pre-wrap font-sans leading-relaxed">
                            {processedText}
                          </pre>
                        </div>
                      ) : (
                        <p className="text-gray-500 text-center py-8">Click &quot;Extracted Text&quot; to load</p>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Right Column - Details */}
              <div className="w-1/2 p-4 overflow-y-auto space-y-4 min-h-0">
                {/* Score Cards */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gradient-to-br from-orange-50 to-red-50 p-4 rounded-xl border border-orange-200">
                    <p className="text-xs text-orange-600 font-semibold uppercase mb-1">Severity Score</p>
                    <p className="text-3xl font-bold text-orange-700">
                      {selectedClaim.severity_score !== null && selectedClaim.severity_score !== undefined
                        ? `${selectedClaim.severity_score}/100`
                        : 'N/A'}
                    </p>
                  </div>
                  <div className="bg-gradient-to-br from-purple-50 to-violet-50 p-4 rounded-xl border border-purple-200">
                    <p className="text-xs text-purple-600 font-semibold uppercase mb-1">Complexity Score</p>
                    <p className="text-3xl font-bold text-purple-700">
                      {selectedClaim.complexity_score !== null && selectedClaim.complexity_score !== undefined
                        ? `${selectedClaim.complexity_score}/100`
                        : 'N/A'}
                    </p>
                  </div>
                </div>

                {/* Claim Details */}
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                  <h4 className="font-semibold text-sm text-foreground mb-3 flex items-center gap-2">
                    <FileText size={16} className="text-primary" />
                    Claim Details
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Type:</span>
                      <span className="font-medium">{selectedClaim.extracted_data?.incident_type || 'unknown'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Status:</span>
                      <Badge>{selectedClaim.status}</Badge>
                    </div>
                  </div>
                </div>

                {/* Assignment Section - Always Show */}
                <div className={`p-4 rounded-xl border ${
                  selectedClaim.routing_decision?.adjuster_id === 'AUTO_SYSTEM'
                    ? 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-200'
                    : 'bg-gradient-to-br from-teal-50 to-cyan-50 border-teal-200'
                }`}>
                  <h4 className="font-semibold text-sm text-foreground mb-3 flex items-center gap-2">
                    <User size={16} className={selectedClaim.routing_decision?.adjuster_id === 'AUTO_SYSTEM' ? 'text-green-600' : 'text-teal-600'} />
                    Assignment
                  </h4>
                  {selectedClaim.routing_decision && selectedClaim.routing_decision.assigned_to ? (
                    selectedClaim.routing_decision.adjuster_id === 'AUTO_SYSTEM' ? (
                      // Auto-Pilot System
                      <div className="space-y-2">
                        <div className="flex items-center gap-2 bg-green-100 rounded-lg p-3">
                          <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center">
                            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                            </svg>
                          </div>
                          <div className="flex-1">
                            <p className="font-bold text-sm text-green-800">Auto-Pilot System</p>
                            <p className="text-xs text-green-600">Automated Processing</p>
                          </div>
                          <Badge className="bg-green-500 text-white">AUTO</Badge>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Priority</p>
                          <Badge variant="default" className="bg-green-600">{selectedClaim.routing_decision.priority}</Badge>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Auto-Decision</p>
                          <p className="text-xs text-gray-700">{selectedClaim.routing_decision.reason}</p>
                        </div>
                        {selectedClaim.routing_decision.estimated_payout && (
                          <div className="bg-green-100 rounded-lg p-2 mt-2">
                            <p className="text-xs text-green-700 font-medium">
                              Estimated Payout: ${selectedClaim.routing_decision.estimated_payout.toLocaleString()}
                            </p>
                          </div>
                        )}
                      </div>
                    ) : (
                      // Human Adjuster
                      <div className="space-y-2">
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Assigned to</p>
                          <p className="font-bold text-lg text-teal-700">{selectedClaim.routing_decision.assigned_to}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Priority</p>
                          <Badge variant="info">{selectedClaim.routing_decision.priority}</Badge>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Reason</p>
                          <p className="text-xs text-gray-700">{selectedClaim.routing_decision.reason}</p>
                        </div>
                      </div>
                    )
                  ) : (
                    <div className="bg-white/50 rounded-lg p-4 text-center">
                      <User size={32} className="mx-auto text-gray-400 mb-2" />
                      <p className="text-sm font-medium text-gray-600">No assignment yet</p>
                      <p className="text-xs text-gray-500 mt-1">Claim is being processed</p>
                    </div>
                  )}
                </div>

                {/* LandingAI Processed Data */}
                {selectedClaim.extracted_text && (
                  <div className="bg-blue-50 p-4 rounded-xl border border-blue-200">
                    <h4 className="font-semibold text-sm text-blue-800 mb-2 flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                      </svg>
                      Processed by LandingAI
                    </h4>
                    <div className="bg-white rounded-lg p-3 max-h-32 overflow-y-auto">
                      <p className="text-xs text-gray-600 leading-relaxed whitespace-pre-wrap">
                        {selectedClaim.extracted_text.substring(0, 300)}
                        {selectedClaim.extracted_text.length > 300 && '...'}
                      </p>
                    </div>
                    <div className="mt-2 flex items-center gap-2 text-xs text-blue-600">
                      <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
                      </svg>
                      <span>Extracted: {selectedClaim.extracted_text.length} characters</span>
                    </div>
                  </div>
                )}

                {/* Extracted Data - Structured */}
                <div>
                  <h4 className="font-semibold text-sm text-foreground mb-2 flex items-center gap-2">
                    <FileText size={16} className="text-primary" />
                    Structured Data
                  </h4>
                  <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 overflow-x-auto max-h-40 overflow-y-auto">
                    <pre className="text-xs text-slate-700 whitespace-pre-wrap font-mono">
                      {JSON.stringify(selectedClaim.extracted_data, null, 2)}
                    </pre>
                  </div>
                </div>

                {/* Fraud Flags */}
                {selectedClaim.fraud_flags && selectedClaim.fraud_flags.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-sm text-red-700 mb-2 flex items-center gap-2">
                      <AlertTriangle size={16} />
                      Fraud Flags
                    </h4>
                    <div className="space-y-2">
                      {selectedClaim.fraud_flags.map((flag, idx) => (
                        <div
                          key={idx}
                          className="bg-gradient-to-r from-red-50 to-orange-50 border-l-4 border-red-500 p-3 rounded-lg"
                        >
                          <div className="flex justify-between items-start mb-1">
                            <p className="font-bold text-red-800 uppercase text-xs">
                              {flag.type.replace(/_/g, ' ')}
                            </p>
                            <Badge variant="destructive" className="text-xs">{flag.severity}</Badge>
                          </div>
                          <p className="text-xs text-gray-700 mb-2">{flag.evidence}</p>
                          <div className="flex items-center gap-2">
                            <div className="flex-1 bg-white rounded-full h-1.5 overflow-hidden">
                              <div
                                className="h-full bg-gradient-to-r from-red-500 to-orange-500"
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

                {/* Investigation Checklist */}
                {selectedClaim.routing_decision?.investigation_checklist && selectedClaim.routing_decision.investigation_checklist.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-sm text-foreground mb-2 flex items-center gap-2">
                      <CheckCircle size={16} className="text-teal-600" />
                      Investigation Checklist
                    </h4>
                    <div className="bg-slate-50 p-3 rounded-xl border border-slate-200">
                      <ul className="space-y-1.5">
                        {selectedClaim.routing_decision.investigation_checklist.map((item, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-xs text-gray-700">
                            <span className="text-teal-600 mt-0.5">•</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
