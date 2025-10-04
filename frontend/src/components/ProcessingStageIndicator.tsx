import React from 'react';
import { Loader2, DollarSign, Shield, CheckCircle2 } from 'lucide-react';

interface ProcessingStageIndicatorProps {
  stage?: string;
  compact?: boolean;
}

const STAGE_CONFIG = {
  extraction: {
    label: 'Processing',
    icon: Loader2,
    color: 'bg-blue-500',
    textColor: 'text-blue-700',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-300',
    step: 1
  },
  scoring: {
    label: 'Processing',
    icon: Loader2,
    color: 'bg-blue-500',
    textColor: 'text-blue-700',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-300',
    step: 1
  },
  auto_processing: {
    label: 'Estimating',
    icon: DollarSign,
    color: 'bg-yellow-500',
    textColor: 'text-yellow-700',
    bgColor: 'bg-yellow-50',
    borderColor: 'border-yellow-300',
    step: 2
  },
  fraud_detection: {
    label: 'Reviewing',
    icon: Shield,
    color: 'bg-orange-500',
    textColor: 'text-orange-700',
    bgColor: 'bg-orange-50',
    borderColor: 'border-orange-300',
    step: 3
  },
  routing: {
    label: 'Finalizing',
    icon: CheckCircle2,
    color: 'bg-green-500',
    textColor: 'text-green-700',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-300',
    step: 4
  }
};

export const ProcessingStageIndicator: React.FC<ProcessingStageIndicatorProps> = ({ stage, compact = false }) => {
  if (!stage || !STAGE_CONFIG[stage as keyof typeof STAGE_CONFIG]) {
    return null;
  }

  const config = STAGE_CONFIG[stage as keyof typeof STAGE_CONFIG];
  const Icon = config.icon;

  if (compact) {
    return (
      <div className={`flex items-center gap-1.5 px-2 py-1 rounded ${config.bgColor} border ${config.borderColor}`}>
        <Icon size={12} className={`${config.textColor} animate-spin`} />
        <span className={`text-xs font-semibold ${config.textColor}`}>
          {config.label}
        </span>
      </div>
    );
  }

  return (
    <div className={`flex flex-col gap-2 p-2 rounded-lg ${config.bgColor} border ${config.borderColor}`}>
      {/* Current Stage */}
      <div className="flex items-center gap-2">
        <Icon size={16} className={`${config.textColor} animate-spin`} />
        <span className={`text-sm font-bold ${config.textColor}`}>
          {config.label}...
        </span>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4].map((step) => (
          <div
            key={step}
            className={`h-1.5 flex-1 rounded-full transition-all duration-300 ${
              step < config.step
                ? 'bg-green-500'
                : step === config.step
                ? `${config.color} animate-pulse`
                : 'bg-gray-300'
            }`}
          />
        ))}
      </div>

      {/* Stage Labels */}
      <div className="flex justify-between text-[9px] text-gray-600 font-medium">
        <span className={config.step >= 1 ? 'text-green-600' : ''}>Process</span>
        <span className={config.step >= 2 ? 'text-green-600' : ''}>Estimate</span>
        <span className={config.step >= 3 ? 'text-green-600' : ''}>Review</span>
        <span className={config.step >= 4 ? 'text-green-600' : ''}>Finalize</span>
      </div>
    </div>
  );
};
