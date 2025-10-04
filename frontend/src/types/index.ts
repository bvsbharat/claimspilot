export interface Claim {
  claim_id: string;
  status: string;
  current_stage?: string;
  file_paths?: string[];
  document_types?: string[];
  extracted_data?: ExtractedData;
  extracted_text?: string;
  severity_score?: number;
  complexity_score?: number;
  fraud_flags: FraudFlag[];
  routing_decision?: RoutingDecision;
  processing_time_seconds?: number;
  created_at?: string;
  updated_at?: string;
  task_id?: string;
  review_check_id?: string;
  source?: string; // "upload" or "gmail"
  source_metadata?: {
    source_type?: string;
    filename?: string;
  };
}

export interface ExtractedData {
  claim_number?: string;
  policy_number?: string;
  claim_amount?: number;
  incident_type?: string;
  incident_date?: string;
  report_date?: string;
  parties: Party[];
  location?: Location;
  injuries: Injury[];
  description?: string;
  fault_determination?: string;
  attorney_involved?: boolean;
}

export interface Party {
  name: string;
  role: string;
  contact?: string;
  address?: string;
}

export interface Location {
  city?: string;
  state?: string;
  address?: string;
}

export interface Injury {
  person: string;
  severity: string;
  description: string;
}

export interface FraudFlag {
  type: string;
  confidence: number;
  evidence: string;
  severity: string;
}

export interface RoutingDecision {
  assigned_to?: string;
  adjuster_id?: string;
  priority: string;
  reason: string;
  estimated_workload_hours?: number;
  investigation_checklist: string[];
}

export interface Adjuster {
  adjuster_id: string;
  name: string;
  email: string;
  specializations: string[];
  experience_level: string;
  years_experience: number;
  max_claim_amount: number;
  max_concurrent_claims: number;
  current_workload: number;
  available: boolean;
}

export interface AdjusterWorkload {
  adjuster_id: string;
  adjuster_name: string;
  current_claims: number;
  max_claims: number;
  capacity_percentage: number;
  active_claims: string[];
}

export interface Metrics {
  total_claims: number;
  assigned_claims: number;
  completed_claims: number;
  avg_processing_time_seconds: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  sources?: ChatSource[];
}

export interface ChatSource {
  claim_id: string;
  text_preview: string;
}

export interface ProcessedData {
  claim_id: string;
  raw_text: string;
  structured_data: ExtractedData;
  tables: any[];
  document_type: string;
  char_count: number;
}

export interface RAGQueryResponse {
  answer: string;
  sources: ChatSource[];
  context: any[];
  model?: string;
  error?: string;
}

export interface GmailEmail {
  id: string;
  subject: string;
  from: string;
  date: string;
  snippet: string;
  has_attachments: boolean;
  attachment_count?: number;
}

export interface GmailStatus {
  connected: boolean;
  user_email?: string;
  connected_at?: string;
}

export interface GmailFetchResponse {
  message: string;
  emails_found: number;
  emails_processed: number;
  claim_ids: string[];
  emails: GmailEmail[];
}
