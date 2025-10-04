import React, { useState, useEffect } from 'react';
import { Card, CardContent } from './ui/card';
import { Upload, FileText, CheckCircle2, XCircle, Loader2, User, DollarSign, TrendingUp, Shield, Mail } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { EmailPreviewModal } from './EmailPreviewModal';
import type { GmailEmail, GmailStatus } from '../types';

const API_BASE = 'http://localhost:8080';

interface ProcessingStage {
  stage: string;
  message: string;
  completed: boolean;
}

interface RoutingDecision {
  assigned_to?: string;
  adjuster_id?: string;
  priority: string;
  reason: string;
  estimated_workload_hours?: number;
  investigation_checklist: string[];
}

interface ClaimDetails {
  claim_id: string;
  status: string;
  incident_type?: string;
  claim_amount?: number;
  severity_score?: number;
  complexity_score?: number;
  routing_decision?: RoutingDecision;
}

export const UploadClaim: React.FC = () => {
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [processingClaimId, setProcessingClaimId] = useState<string | null>(null);
  const [processingStages, setProcessingStages] = useState<ProcessingStage[]>([]);
  const [claimDetails, setClaimDetails] = useState<ClaimDetails | null>(null);

  // Gmail state
  const [gmailStatus, setGmailStatus] = useState<GmailStatus>({ connected: false });
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [previewEmails, setPreviewEmails] = useState<GmailEmail[]>([]);
  const [fetchingEmails, setFetchingEmails] = useState(false);

  // Auto-fetch state
  const [autoFetchStatus, setAutoFetchStatus] = useState<any>(null);

  // Check Gmail connection status and auto-fetch status on mount
  useEffect(() => {
    checkGmailStatus();
    checkAutoFetchStatus();
    // Check auto-fetch status every 30 seconds
    const interval = setInterval(checkAutoFetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  // Subscribe to SSE events
  useEffect(() => {
    const es = new EventSource(`${API_BASE}/api/events/stream`);

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Only process events for the claim we're tracking
        if (processingClaimId && data.claim_id === processingClaimId) {
          // Update stages based on event type
          if (data.type === 'claim_status_update') {
            const stageName = data.stage || data.status;
            setProcessingStages(prev => {
              const existing = prev.find(s => s.stage === stageName);
              if (existing) {
                return prev.map(s =>
                  s.stage === stageName ? { ...s, completed: true, message: data.message } : s
                );
              } else {
                return [...prev, { stage: stageName, message: data.message, completed: false }];
              }
            });
          } else if (data.type === 'claim_processed') {
            // Final processing complete
            setProcessingStages(prev => prev.map(s => ({ ...s, completed: true })));
            setClaimDetails({
              claim_id: data.claim_id,
              status: data.status,
              incident_type: data.routing_decision?.incident_type,
              claim_amount: data.routing_decision?.claim_amount,
              severity_score: data.severity_score,
              complexity_score: data.complexity_score,
              routing_decision: data.routing_decision,
            });
            setUploading(false);
          }
        }
      } catch (error) {
        console.error('Failed to parse SSE event:', error);
      }
    };

    es.onerror = () => {
      console.error('SSE connection error');
    };

    return () => {
      es.close();
    };
  }, [processingClaimId]);

  const handleFileUpload = async (file: File) => {
    setUploading(true);
    setMessage(null);
    setProcessingStages([]);
    setClaimDetails(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE}/api/claims/upload`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        setMessage({ type: 'success', text: `Claim uploaded: ${data.claim_id}` });
        setProcessingClaimId(data.claim_id);
        setProcessingStages([
          { stage: 'uploaded', message: 'File uploaded successfully', completed: true },
          { stage: 'extracting', message: 'Extracting document data...', completed: false },
          { stage: 'scoring', message: 'Calculating scores...', completed: false },
          { stage: 'fraud_detection', message: 'Running fraud detection...', completed: false },
          { stage: 'routing', message: 'Finding optimal adjuster...', completed: false },
        ]);
      } else {
        setMessage({ type: 'error', text: data.detail || 'Upload failed' });
        setUploading(false);
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Upload failed: ' + (error as Error).message });
      setUploading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileUpload(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFileUpload(file);
  };

  // Gmail functions
  const checkGmailStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/gmail/status`);
      const data = await response.json();
      setGmailStatus(data);
    } catch (error) {
      console.error('Failed to check Gmail status:', error);
    }
  };

  const checkAutoFetchStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/gmail/auto-fetch/status`);
      const data = await response.json();
      setAutoFetchStatus(data);
    } catch (error) {
      console.error('Failed to check auto-fetch status:', error);
    }
  };

  const handleFetchEmails = async () => {
    try {
      setFetchingEmails(true);
      setMessage(null);

      // Check if Gmail is connected
      if (!gmailStatus.connected) {
        setMessage({
          type: 'error',
          text: 'Gmail not connected. Please add credentials.json and token.json to backend directory.'
        });
        setFetchingEmails(false);
        return;
      }

      // Preview emails first
      const response = await fetch(`${API_BASE}/api/gmail/preview?max_results=10&days_back=7`);
      const data = await response.json();

      if (response.ok) {
        setPreviewEmails(data.emails || []);
        setShowPreviewModal(true);
      } else {
        setMessage({ type: 'error', text: data.detail || 'Failed to fetch emails' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to fetch emails: ' + (error as Error).message });
    } finally {
      setFetchingEmails(false);
    }
  };

  const handleProcessEmails = async () => {
    try {
      setFetchingEmails(true);
      setMessage(null);

      const response = await fetch(`${API_BASE}/api/gmail/fetch`, {
        method: 'POST',
      });

      const data = await response.json();

      if (response.ok) {
        setShowPreviewModal(false);
        setMessage({
          type: 'success',
          text: `Successfully processed ${data.emails_processed} of ${data.emails_found} emails`
        });
      } else {
        setMessage({ type: 'error', text: data.detail || 'Failed to process emails' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to process emails: ' + (error as Error).message });
    } finally {
      setFetchingEmails(false);
    }
  };

  return (
    <Card className="border-0 overflow-hidden shadow-lg">
      <CardContent className="p-0">
        <div className="bg-gradient-to-r from-teal-500 to-cyan-500 p-5">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Upload size={24} />
                Upload Claim Document
              </h2>
              <div className="space-y-1">
                <p className="text-teal-100 text-sm">Start the automated triage process</p>
                {autoFetchStatus?.enabled && autoFetchStatus?.running && (
                  <p className="text-white/80 text-xs flex items-center gap-1">
                    <span className="inline-block w-2 h-2 bg-green-300 rounded-full animate-pulse"></span>
                    Auto-fetching emails every {autoFetchStatus.interval_minutes} min
                    {autoFetchStatus.last_fetch_time && (
                      <span className="ml-1">
                        • Last: {new Date(autoFetchStatus.last_fetch_time).toLocaleTimeString()}
                      </span>
                    )}
                  </p>
                )}
              </div>
            </div>
            <Button
              onClick={handleFetchEmails}
              disabled={fetchingEmails || uploading}
              className="bg-white/20 hover:bg-white/30 text-white border-2 border-white/40"
            >
              {fetchingEmails ? (
                <>
                  <Loader2 className="animate-spin mr-2" size={16} />
                  Fetching...
                </>
              ) : (
                <>
                  <Mail size={16} className="mr-2" />
                  Fetch from Gmail
                </>
              )}
            </Button>
          </div>
        </div>

        <div className="p-6 space-y-4">
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`
              relative border-2 border-dashed rounded-xl p-8 text-center
              transition-all duration-300
              ${dragActive
                ? 'border-teal-500 bg-teal-50 scale-105'
                : 'border-gray-300 bg-gradient-to-br from-gray-50 to-white hover:border-teal-400 hover:bg-teal-50'
              }
              ${uploading ? 'opacity-60' : ''}
            `}
          >
            <input
              type="file"
              onChange={handleChange}
              disabled={uploading}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
              id="file-upload"
              accept=".pdf,.jpg,.jpeg,.png"
            />
            <div className="space-y-4 pointer-events-none">
              {uploading ? (
                <Loader2 className="w-16 h-16 text-teal-600 mx-auto animate-spin" />
              ) : (
                <div className="w-16 h-16 bg-gradient-to-br from-teal-500 to-cyan-500 rounded-full flex items-center justify-center mx-auto shadow-lg">
                  <FileText className="text-white" size={32} />
                </div>
              )}
              <div>
                <p className="text-lg font-semibold text-foreground mb-1">
                  {uploading ? 'Uploading...' : dragActive ? 'Drop file here' : 'Click to upload or drag and drop'}
                </p>
                <p className="text-sm text-muted-foreground">
                  PDF, JPG, PNG • ACORD forms, police reports, medical records
                </p>
              </div>
              {!uploading && (
                <div className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-teal-500 to-cyan-500 text-white rounded-lg font-medium shadow-lg">
                  <Upload size={16} />
                  Choose File
                </div>
              )}
            </div>
          </div>

          {message && (
            <div
              className={`
                p-4 rounded-xl border-2 animate-fade-in flex items-start gap-3
                ${message.type === 'success'
                  ? 'bg-gradient-to-r from-green-50 to-emerald-50 border-green-300'
                  : 'bg-gradient-to-r from-red-50 to-orange-50 border-red-300'
                }
              `}
            >
              {message.type === 'success' ? (
                <CheckCircle2 className="text-green-600 flex-shrink-0 mt-0.5" size={20} />
              ) : (
                <XCircle className="text-red-600 flex-shrink-0 mt-0.5" size={20} />
              )}
              <p className={`text-sm font-medium ${
                message.type === 'success' ? 'text-green-800' : 'text-red-800'
              }`}>
                {message.text}
              </p>
            </div>
          )}

          {/* Processing Stages */}
          {processingStages.length > 0 && (
            <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-4 border border-blue-200">
              <p className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
                <Loader2 className={`text-teal-600 ${uploading ? 'animate-spin' : ''}`} size={16} />
                Processing Status
              </p>
              <ul className="space-y-3">
                {processingStages.map((stage, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    {stage.completed ? (
                      <CheckCircle2 className="text-green-600 flex-shrink-0 mt-0.5" size={16} />
                    ) : (
                      <Loader2 className="text-blue-600 flex-shrink-0 mt-0.5 animate-spin" size={16} />
                    )}
                    <div className="flex-1">
                      <p className={`text-sm font-medium ${stage.completed ? 'text-green-800' : 'text-blue-800'}`}>
                        {stage.message}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Assignment Details */}
          {claimDetails && claimDetails.routing_decision && (
            <div className="bg-gradient-to-br from-teal-50 to-cyan-50 rounded-xl p-5 border-2 border-teal-300 animate-fade-in">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-xs text-muted-foreground mb-1">Claim Assigned</p>
                  <h3 className="text-2xl font-bold text-teal-700 flex items-center gap-2">
                    <User size={24} />
                    {claimDetails.routing_decision.assigned_to || 'Unassigned'}
                  </h3>
                </div>
                <Badge variant={claimDetails.routing_decision.priority === 'urgent' ? 'destructive' :
                              claimDetails.routing_decision.priority === 'high' ? 'warning' : 'default'}>
                  {claimDetails.routing_decision.priority}
                </Badge>
              </div>

              <div className="space-y-3 mb-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-white rounded-lg border border-teal-200">
                    <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                      <FileText size={12} />
                      Type
                    </p>
                    <p className="text-sm font-bold text-gray-800 capitalize">{claimDetails.incident_type || 'N/A'}</p>
                  </div>
                  <div className="p-3 bg-white rounded-lg border border-teal-200">
                    <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                      <DollarSign size={12} />
                      Amount
                    </p>
                    <p className="text-sm font-bold text-gray-800">
                      {claimDetails.claim_amount ? `$${claimDetails.claim_amount.toLocaleString()}` : 'N/A'}
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-white rounded-lg border border-orange-200">
                    <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                      <TrendingUp size={12} />
                      Severity
                    </p>
                    <p className="text-sm font-bold text-orange-700">
                      {claimDetails.severity_score?.toFixed(1) || 'N/A'}
                    </p>
                  </div>
                  <div className="p-3 bg-white rounded-lg border border-purple-200">
                    <p className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                      <Shield size={12} />
                      Complexity
                    </p>
                    <p className="text-sm font-bold text-purple-700">
                      {claimDetails.complexity_score?.toFixed(1) || 'N/A'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-3 bg-white rounded-lg border border-teal-200">
                <p className="text-xs text-muted-foreground mb-2 font-semibold">Assignment Reasoning:</p>
                <p className="text-sm text-gray-700">{claimDetails.routing_decision.reason}</p>
              </div>

              {claimDetails.routing_decision.estimated_workload_hours && (
                <div className="mt-3 text-xs text-muted-foreground text-center">
                  Estimated workload: {claimDetails.routing_decision.estimated_workload_hours} hours
                </div>
              )}
            </div>
          )}

          {!processingStages.length && (
            <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-4 border border-blue-200">
              <p className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
                <FileText size={16} className="text-teal-600" />
                Automated Processing Pipeline
              </p>
              <ul className="space-y-2 text-xs text-muted-foreground">
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-teal-500 rounded-full"></div>
                  Extract claim data using LandingAI computer vision
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-teal-500 rounded-full"></div>
                  Calculate severity and complexity scores
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-teal-500 rounded-full"></div>
                  Detect fraud indicators with GPT-4o
                </li>
                <li className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 bg-teal-500 rounded-full"></div>
                  Route to appropriate adjuster via vector search
                </li>
              </ul>
            </div>
          )}
        </div>
      </CardContent>

      {/* Gmail Email Preview Modal */}
      <EmailPreviewModal
        isOpen={showPreviewModal}
        emails={previewEmails}
        onClose={() => setShowPreviewModal(false)}
        onProcess={handleProcessEmails}
        loading={fetchingEmails}
      />
    </Card>
  );
};
