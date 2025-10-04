import React from 'react';
import { useSSE } from '../hooks/useSSE';
import type { SSEEvent } from '../hooks/useSSE';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Activity, Upload, CheckCircle2, XCircle, Zap } from 'lucide-react';

const API_BASE = 'http://localhost:8080';

export const LiveFeed: React.FC = () => {
  const { events, connected } = useSSE(`${API_BASE}/api/events/stream`);

  const recentEvents = events.slice(-10).reverse();

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'claim_uploaded':
        return <Upload size={18} className="text-blue-600" />;
      case 'claim_processed':
        return <CheckCircle2 size={18} className="text-green-600" />;
      case 'claim_processing':
        return <Zap size={18} className="text-orange-600 animate-pulse" />;
      case 'document_error':
        return <XCircle size={18} className="text-red-600" />;
      case 'heartbeat':
        return <Activity size={18} className="text-gray-400" />;
      default:
        return <Zap size={18} className="text-teal-600" />;
    }
  };

  const getEventColor = (type: string) => {
    switch (type) {
      case 'claim_uploaded':
        return 'from-blue-50 to-cyan-50 border-blue-200';
      case 'claim_processed':
        return 'from-green-50 to-emerald-50 border-green-200';
      case 'claim_processing':
        return 'from-orange-50 to-yellow-50 border-orange-200';
      case 'document_error':
        return 'from-red-50 to-orange-50 border-red-200';
      default:
        return 'from-gray-50 to-slate-50 border-gray-200';
    }
  };

  return (
    <Card className="border-0 overflow-hidden shadow-lg h-full">
      <CardContent className="p-0 flex flex-col h-full">
        <div className="bg-gradient-to-r from-purple-500 to-pink-500 p-5">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                <Activity size={24} />
                Live Feed
              </h2>
              <p className="text-purple-100 text-sm mt-1">Real-time system events</p>
            </div>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-white/20 rounded-full backdrop-blur-sm">
              <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
              <span className="text-xs font-medium text-white">
                {connected ? 'Live' : 'Offline'}
              </span>
            </div>
          </div>
        </div>

        <div className="p-4 flex-1 overflow-y-auto space-y-2 max-h-[500px] bg-gradient-to-b from-white to-gray-50">
          {recentEvents.map((event: SSEEvent, idx: number) => (
            event.type !== 'heartbeat' && (
              <div
                key={idx}
                className={`
                  p-3 rounded-lg border bg-gradient-to-r
                  ${getEventColor(event.type)}
                  animate-fade-in hover:shadow-md transition-all
                `}
                style={{ animationDelay: `${idx * 50}ms` }}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 p-1.5 bg-white rounded-lg shadow-sm">
                    {getEventIcon(event.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm text-foreground leading-tight">
                      {event.message}
                    </p>
                    {event.processing_time && (
                      <div className="flex items-center gap-2 mt-1.5">
                        <Badge variant="secondary" className="text-xs">
                          {event.processing_time.toFixed(1)}s
                        </Badge>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )
          ))}

          {recentEvents.filter(e => e.type !== 'heartbeat').length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-purple-100 to-pink-100 rounded-full flex items-center justify-center mb-3">
                <Activity size={32} className="text-purple-600" />
              </div>
              <p className="text-sm font-semibold text-foreground">No events yet</p>
              <p className="text-xs text-muted-foreground mt-1">
                Upload a claim to see live updates
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
