import React, { useState } from 'react';
import type { Claim } from '../types';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { ProcessingIndicator } from './ProcessingIndicator';
import { DollarSign, Activity, AlertTriangle, User, Trash2 } from 'lucide-react';

interface ClaimCardProps {
  claim: Claim;
  onClick?: () => void;
  onDelete?: (claimId: string) => void;
}

export const ClaimCard: React.FC<ClaimCardProps> = ({ claim, onClick, onDelete }) => {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const getPriorityVariant = (priority?: string): 'default' | 'destructive' | 'warning' | 'success' => {
    switch (priority) {
      case 'urgent': return 'destructive';
      case 'high': return 'warning';
      case 'medium': return 'default';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getStatusVariant = (status: string): 'default' | 'success' | 'warning' | 'info' => {
    switch (status) {
      case 'assigned': return 'default';
      case 'in_progress': return 'info';
      case 'review': return 'warning';
      case 'completed': return 'success';
      case 'routing': return 'warning';
      default: return 'default';
    }
  };

  const canDelete = true; // Allow deletion of any claim

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowDeleteConfirm(true);
  };

  const confirmDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(claim.claim_id);
    }
    setShowDeleteConfirm(false);
  };

  const cancelDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowDeleteConfirm(false);
  };

  return (
    <Card
      onClick={onClick}
      className="group hover:shadow-2xl hover:scale-[1.02] transition-all duration-300 cursor-pointer border-0 bg-gradient-to-br from-white to-gray-50 overflow-hidden"
    >
      <CardContent className="p-5">
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <h3 className="font-bold text-lg text-foreground mb-1">{claim.claim_id}</h3>
            <p className="text-sm text-muted-foreground flex items-center gap-1 mb-2">
              <Activity size={14} />
              {claim.extracted_data?.incident_type || 'Unknown Type'}
            </p>
            {['uploaded', 'extracting', 'scoring', 'routing'].includes(claim.status) && (
              <ProcessingIndicator status={claim.status} size="sm" />
            )}
          </div>
          <div className="flex flex-col gap-2 items-end">
            {!['uploaded', 'extracting', 'scoring', 'routing'].includes(claim.status) && (
              <Badge variant={getStatusVariant(claim.status)}>
                {claim.status}
              </Badge>
            )}
            {claim.routing_decision?.priority && (
              <Badge variant={getPriorityVariant(claim.routing_decision.priority)}>
                {claim.routing_decision.priority}
              </Badge>
            )}
          </div>
        </div>

        <div className="space-y-3">
          {claim.extracted_data?.claim_amount && (
            <div className="flex justify-between items-center text-sm p-2 rounded-lg bg-blue-50 border border-blue-100">
              <span className="text-muted-foreground flex items-center gap-1">
                <DollarSign size={14} />
                Amount
              </span>
              <span className="font-semibold text-blue-700">
                ${claim.extracted_data.claim_amount.toLocaleString()}
              </span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-2">
            <div className="p-2 rounded-lg bg-orange-50 border border-orange-100">
              <p className="text-xs text-muted-foreground mb-1">Severity</p>
              <p className="font-bold text-orange-700">{claim.severity_score?.toFixed(1) || 'N/A'}</p>
            </div>
            <div className="p-2 rounded-lg bg-purple-50 border border-purple-100">
              <p className="text-xs text-muted-foreground mb-1">Complexity</p>
              <p className="font-bold text-purple-700">{claim.complexity_score?.toFixed(1) || 'N/A'}</p>
            </div>
          </div>

          {claim.fraud_flags && claim.fraud_flags.length > 0 && (
            <div className="p-3 bg-gradient-to-r from-red-50 to-orange-50 border-2 border-red-200 rounded-lg animate-pulse-slow">
              <p className="text-sm font-bold text-red-700 flex items-center gap-2">
                <AlertTriangle size={16} />
                {claim.fraud_flags.length} Fraud Flag{claim.fraud_flags.length > 1 ? 's' : ''}
              </p>
            </div>
          )}

          {claim.review_check_id && (
            <div className="p-3 bg-gradient-to-r from-amber-50 to-yellow-50 border-2 border-amber-300 rounded-lg">
              <p className="text-xs text-muted-foreground mb-1">Check ID</p>
              <p className="text-sm font-bold text-amber-800">{claim.review_check_id}</p>
            </div>
          )}

          {claim.routing_decision?.assigned_to && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <div className="flex items-center gap-2 p-2 rounded-lg bg-teal-50 border border-teal-100">
                <User size={16} className="text-teal-600" />
                <div className="flex-1">
                  <p className="text-xs text-muted-foreground">Assigned to</p>
                  <p className="text-sm font-semibold text-teal-700">{claim.routing_decision.assigned_to}</p>
                </div>
              </div>
            </div>
          )}

          {canDelete && onDelete && !showDeleteConfirm && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <button
                onClick={handleDelete}
                className="w-full flex items-center justify-center gap-2 p-2 rounded-lg bg-red-50 border border-red-200 hover:bg-red-100 transition-colors text-red-700 hover:text-red-800"
              >
                <Trash2 size={16} />
                <span className="text-sm font-semibold">Delete Claim</span>
              </button>
            </div>
          )}

          {showDeleteConfirm && (
            <div className="mt-3 pt-3 border-t border-gray-200">
              <div className="p-3 bg-red-50 border border-red-300 rounded-lg space-y-3">
                <p className="text-sm font-semibold text-red-800">Are you sure you want to delete this claim?</p>
                <div className="flex gap-2">
                  <button
                    onClick={confirmDelete}
                    className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-semibold transition-colors"
                  >
                    Yes, Delete
                  </button>
                  <button
                    onClick={cancelDelete}
                    className="flex-1 px-3 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg text-sm font-semibold transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="absolute inset-0 border-2 border-teal-500 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>
      </CardContent>
    </Card>
  );
};
