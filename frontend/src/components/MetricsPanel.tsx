import React, { useEffect, useState } from 'react';
import type { Metrics } from '../types';
import { Card, CardContent } from './ui/card';
import { FileText, CheckCircle2, Clock, TrendingUp } from 'lucide-react';

const API_BASE = 'http://localhost:8080';

export const MetricsPanel: React.FC = () => {
  const [metrics, setMetrics] = useState<Metrics | null>(null);

  const fetchMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/analytics/metrics`);
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
    }
  };

  useEffect(() => {
    let abortController = new AbortController();

    const fetchWithAbort = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/analytics/metrics`, {
          signal: abortController.signal
        });
        const data = await response.json();
        setMetrics(data);
      } catch (error) {
        if (error.name !== 'AbortError') {
          console.error('Failed to fetch metrics:', error);
        }
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

  if (!metrics) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-6">
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-3"></div>
              <div className="h-8 bg-gray-200 rounded w-3/4"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  const avgTimeMinutes = (metrics.avg_processing_time_seconds / 60).toFixed(1);

  const metricCards = [
    {
      title: 'Total Claims',
      value: metrics.total_claims,
      icon: FileText,
      gradient: 'from-blue-500 to-cyan-500',
      bg: 'from-blue-50 to-cyan-50',
    },
    {
      title: 'Assigned',
      value: metrics.assigned_claims,
      icon: TrendingUp,
      gradient: 'from-teal-500 to-emerald-500',
      bg: 'from-teal-50 to-emerald-50',
    },
    {
      title: 'Completed',
      value: metrics.completed_claims,
      icon: CheckCircle2,
      gradient: 'from-green-500 to-lime-500',
      bg: 'from-green-50 to-lime-50',
    },
    {
      title: 'Avg Time',
      value: `${avgTimeMinutes}m`,
      icon: Clock,
      gradient: 'from-purple-500 to-pink-500',
      bg: 'from-purple-50 to-pink-50',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {metricCards.map((metric, index) => {
        const Icon = metric.icon;
        return (
          <Card
            key={metric.title}
            className="overflow-hidden hover:shadow-xl transition-all duration-300 border-0 animate-fade-in"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <CardContent className={`p-6 bg-gradient-to-br ${metric.bg} relative`}>
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-sm font-medium text-muted-foreground mb-2">
                    {metric.title}
                  </p>
                  <p className="text-4xl font-bold text-foreground">
                    {metric.value}
                  </p>
                </div>
                <div className={`p-3 rounded-xl bg-gradient-to-br ${metric.gradient} shadow-lg`}>
                  <Icon className="text-white" size={24} />
                </div>
              </div>
              <div className={`h-1 w-full bg-gradient-to-r ${metric.gradient} rounded-full`}></div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
};
