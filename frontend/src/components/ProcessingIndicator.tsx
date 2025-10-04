import React from 'react';
import { Loader2, CheckCircle, AlertCircle } from 'lucide-react';

interface ProcessingIndicatorProps {
  status: string;
  stage?: string;
  size?: 'sm' | 'md' | 'lg';
}

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  uploaded: {
    label: 'Uploaded',
    color: 'text-blue-600 bg-blue-50 border-blue-200',
    icon: <Loader2 className="animate-spin" size={16} />
  },
  extracting: {
    label: 'Extracting Data',
    color: 'text-purple-600 bg-purple-50 border-purple-200',
    icon: <Loader2 className="animate-spin" size={16} />
  },
  scoring: {
    label: 'Analyzing Severity',
    color: 'text-orange-600 bg-orange-50 border-orange-200',
    icon: <Loader2 className="animate-spin" size={16} />
  },
  routing: {
    label: 'Finding Adjuster',
    color: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    icon: <Loader2 className="animate-spin" size={16} />
  },
  assigned: {
    label: 'Assigned',
    color: 'text-teal-600 bg-teal-50 border-teal-200',
    icon: <CheckCircle size={16} />
  },
  auto_approved: {
    label: 'Auto-Approved',
    color: 'text-green-600 bg-green-50 border-green-200',
    icon: <CheckCircle size={16} />
  },
  in_progress: {
    label: 'In Progress',
    color: 'text-cyan-600 bg-cyan-50 border-cyan-200',
    icon: <Loader2 className="animate-spin" size={16} />
  },
  completed: {
    label: 'Completed',
    color: 'text-green-700 bg-green-100 border-green-300',
    icon: <CheckCircle size={16} />
  },
  rejected: {
    label: 'Rejected',
    color: 'text-red-600 bg-red-50 border-red-200',
    icon: <AlertCircle size={16} />
  }
};

const STAGE_LABELS: Record<string, string> = {
  extraction: 'Extracting document data...',
  scoring: 'Calculating severity & complexity...',
  fraud_detection: 'Running fraud analysis...',
  routing: 'Matching to adjuster...',
  auto_processing: 'Auto-processing claim...'
};

export const ProcessingIndicator: React.FC<ProcessingIndicatorProps> = ({
  status,
  stage,
  size = 'md'
}) => {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG['uploaded'];
  const displayLabel = stage ? STAGE_LABELS[stage] || config.label : config.label;

  const sizeClasses = {
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-3 py-2',
    lg: 'text-base px-4 py-3'
  };

  return (
    <div className={`inline-flex items-center gap-2 rounded-lg border-2 font-semibold ${config.color} ${sizeClasses[size]}`}>
      {config.icon}
      <span>{displayLabel}</span>
    </div>
  );
};
