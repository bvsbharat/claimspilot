import React, { useEffect, useState } from 'react';
import type { Adjuster } from '../types';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Users, Mail, Award, DollarSign, TrendingUp } from 'lucide-react';

const API_BASE = 'http://localhost:8080';

export const AdjusterPanel: React.FC = () => {
  const [adjusters, setAdjusters] = useState<Adjuster[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAdjusters = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/adjusters/list`);
      const data = await response.json();
      setAdjusters(data.adjusters || []);
    } catch (error) {
      console.error('Failed to fetch adjusters:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let abortController = new AbortController();

    const fetchWithAbort = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/adjusters/list`, {
          signal: abortController.signal
        });
        const data = await response.json();
        setAdjusters(data.adjusters || []);
      } catch (error) {
        if (error.name !== 'AbortError') {
          console.error('Failed to fetch adjusters:', error);
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

  const getCapacityColor = (percentage: number) => {
    if (percentage >= 90) return 'from-red-500 to-rose-500';
    if (percentage >= 70) return 'from-orange-500 to-amber-500';
    if (percentage >= 50) return 'from-yellow-500 to-orange-500';
    return 'from-green-500 to-emerald-500';
  };

  const getCapacityBgColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-red-100 border-red-200';
    if (percentage >= 70) return 'bg-orange-100 border-orange-200';
    if (percentage >= 50) return 'bg-yellow-100 border-yellow-200';
    return 'bg-green-100 border-green-200';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
          <p className="text-muted-foreground">Loading adjusters...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-foreground flex items-center gap-2">
          <Users size={28} className="text-primary" />
          Adjusters
        </h2>
        <p className="text-sm text-muted-foreground mt-1">Team capacity and specialization overview</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {adjusters.map((adjuster, index) => {
          const capacityPercentage = (adjuster.current_workload / adjuster.max_concurrent_claims) * 100;

          return (
            <Card
              key={adjuster.adjuster_id}
              className="overflow-hidden hover:shadow-xl transition-all duration-300 border-0 animate-fade-in"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <CardContent className="p-0">
                <div className={`p-5 bg-gradient-to-br from-teal-50 to-cyan-50 border-b-2 border-teal-200`}>
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-4">
                      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-teal-500 to-cyan-500 flex items-center justify-center text-white font-bold text-2xl shadow-lg ring-4 ring-teal-100">
                        {adjuster.name.split(' ').map(n => n[0]).join('')}
                      </div>
                      <div>
                        <h3 className="font-bold text-2xl text-foreground tracking-tight">{adjuster.name}</h3>
                        <p className="text-sm text-muted-foreground flex items-center gap-1.5 mt-1">
                          <Mail size={14} />
                          {adjuster.email}
                        </p>
                      </div>
                    </div>
                    <Badge variant={adjuster.available ? 'success' : 'destructive'} className="text-xs px-3 py-1">
                      {adjuster.available ? 'Available' : 'Unavailable'}
                    </Badge>
                  </div>
                </div>

                <div className="p-5 space-y-4">
                  <div className="flex flex-wrap gap-2">
                    {adjuster.specializations.map(spec => (
                      <Badge key={spec} variant="default" className="text-xs">
                        {spec}
                      </Badge>
                    ))}
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 rounded-lg bg-gradient-to-br from-purple-50 to-pink-50 border border-purple-200">
                      <div className="flex items-center gap-2 mb-1">
                        <Award size={14} className="text-purple-600" />
                        <p className="text-xs text-muted-foreground">Experience</p>
                      </div>
                      <p className="font-bold text-purple-700 capitalize">
                        {adjuster.experience_level}
                      </p>
                      <p className="text-xs text-muted-foreground">{adjuster.years_experience} years</p>
                    </div>

                    <div className="p-3 rounded-lg bg-gradient-to-br from-blue-50 to-cyan-50 border border-blue-200">
                      <div className="flex items-center gap-2 mb-1">
                        <DollarSign size={14} className="text-blue-600" />
                        <p className="text-xs text-muted-foreground">Max Claim</p>
                      </div>
                      <p className="font-bold text-blue-700">
                        ${(adjuster.max_claim_amount / 1000).toFixed(0)}K
                      </p>
                    </div>
                  </div>

                  <div className={`p-4 rounded-xl border-2 ${getCapacityBgColor(capacityPercentage)}`}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <TrendingUp size={16} className="text-foreground" />
                        <span className="text-sm font-semibold text-foreground">Workload</span>
                      </div>
                      <span className="font-bold text-foreground">
                        {adjuster.current_workload} / {adjuster.max_concurrent_claims}
                      </span>
                    </div>
                    <div className="relative">
                      <div className="w-full bg-white/50 rounded-full h-3 overflow-hidden">
                        <div
                          className={`h-full bg-gradient-to-r ${getCapacityColor(capacityPercentage)} transition-all duration-500 rounded-full`}
                          style={{ width: `${capacityPercentage}%` }}
                        ></div>
                      </div>
                    </div>
                    <p className="text-xs font-semibold text-foreground mt-2 text-center">
                      {capacityPercentage.toFixed(0)}% capacity
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {adjusters.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="w-20 h-20 bg-gradient-to-br from-teal-100 to-cyan-100 rounded-full flex items-center justify-center mb-4">
            <Users size={40} className="text-teal-600" />
          </div>
          <p className="text-xl font-semibold text-foreground">No adjusters found</p>
          <p className="text-sm text-muted-foreground mt-2">Add adjusters to start routing claims</p>
        </div>
      )}
    </div>
  );
};
