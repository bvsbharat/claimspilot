import React, { useEffect, useState } from 'react';
import type { Claim } from '../types';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { AlertTriangle, ShieldAlert, Shield } from 'lucide-react';

const API_BASE = 'http://localhost:8080';

export const FraudAlerts: React.FC = () => {
  const [claimsWithFlags, setClaimsWithFlags] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchFraudFlags = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/analytics/fraud-flags`);
      const data = await response.json();
      setClaimsWithFlags(data.fraud_flags || []);
    } catch (error) {
      console.error('Failed to fetch fraud flags:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let abortController = new AbortController();

    const fetchWithAbort = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/analytics/fraud-flags`, {
          signal: abortController.signal
        });
        const data = await response.json();
        setClaimsWithFlags(data.fraud_flags || []);
      } catch (error) {
        if (error.name !== 'AbortError') {
          console.error('Failed to fetch fraud flags:', error);
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
    }, 30000); // Increased from 10s to 30s

    return () => {
      clearInterval(interval);
      abortController.abort();
    };
  }, []);

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
      case 'high':
        return 'from-red-500 to-rose-500';
      case 'medium':
        return 'from-orange-500 to-amber-500';
      case 'low':
        return 'from-yellow-500 to-orange-500';
      default:
        return 'from-red-500 to-rose-500';
    }
  };

  const getSeverityBadge = (severity: string): 'destructive' | 'warning' | 'default' => {
    switch (severity.toLowerCase()) {
      case 'critical':
      case 'high':
        return 'destructive';
      case 'medium':
        return 'warning';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          <p className="text-muted-foreground">Loading fraud alerts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-foreground flex items-center gap-2">
            <ShieldAlert size={28} className="text-red-600" />
            Fraud Alerts
          </h2>
          <p className="text-sm text-muted-foreground mt-1">High-priority fraud detection results</p>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-red-50 to-orange-50 border-2 border-red-300">
          <AlertTriangle size={20} className="text-red-600" />
          <span className="text-2xl font-bold text-red-700">{claimsWithFlags.length}</span>
          <span className="text-sm text-muted-foreground">Alert{claimsWithFlags.length !== 1 ? 's' : ''}</span>
        </div>
      </div>

      <div className="space-y-4">
        {claimsWithFlags.map((claim, index) => (
          <Card
            key={claim.claim_id}
            className="overflow-hidden border-0 animate-fade-in hover:shadow-2xl transition-all duration-300"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <CardContent className="p-0">
              <div className="bg-gradient-to-r from-red-500 to-rose-500 p-4 flex justify-between items-center">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                    <AlertTriangle className="text-white" size={24} />
                  </div>
                  <div>
                    <h3 className="font-bold text-lg text-white">{claim.claim_id}</h3>
                    <p className="text-sm text-red-100">
                      {claim.extracted_data?.incident_type || 'Unknown Type'}
                    </p>
                  </div>
                </div>
                <Badge variant="destructive" className="bg-white/20 border-white/30 text-white">
                  {claim.fraud_flags.length} Flag{claim.fraud_flags.length > 1 ? 's' : ''}
                </Badge>
              </div>

              <div className="p-5 space-y-3 bg-gradient-to-br from-white to-red-50">
                {claim.fraud_flags.map((flag, idx) => (
                  <div
                    key={idx}
                    className="bg-white border-l-4 border-red-500 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <p className="font-bold text-red-800 uppercase text-sm mb-1">
                          {flag.type.replace(/_/g, ' ')}
                        </p>
                        <Badge variant={getSeverityBadge(flag.severity)} className="text-xs">
                          {flag.severity}
                        </Badge>
                      </div>
                    </div>
                    <p className="text-sm text-gray-700 mb-3 leading-relaxed">{flag.evidence}</p>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center text-xs text-muted-foreground">
                        <span>Confidence Level</span>
                        <span className="font-bold text-red-700">
                          {(flag.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="relative">
                        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                          <div
                            className={`h-full bg-gradient-to-r ${getSeverityColor(flag.severity)} transition-all duration-500 rounded-full`}
                            style={{ width: `${flag.confidence * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {claimsWithFlags.length === 0 && (
        <Card className="border-0 overflow-hidden">
          <CardContent className="p-0">
            <div className="bg-gradient-to-br from-green-50 to-emerald-50 border-2 border-green-200 p-12 text-center">
              <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-emerald-500 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
                <Shield className="text-white" size={40} />
              </div>
              <p className="text-2xl font-bold text-green-700 mb-2">All Clear!</p>
              <p className="text-sm text-muted-foreground">No fraud alerts detected. All claims appear legitimate.</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
