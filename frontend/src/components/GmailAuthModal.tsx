import React, { useState } from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { X, Mail, Shield, CheckCircle2, AlertCircle } from 'lucide-react';

const API_BASE = 'http://localhost:8080';

interface GmailAuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export const GmailAuthModal: React.FC<GmailAuthModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleConnect = async () => {
    try {
      setLoading(true);
      setError(null);

      // Get authorization URL from backend
      const response = await fetch(`${API_BASE}/api/gmail/auth-url`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to get authorization URL');
      }

      // Open OAuth popup
      const width = 600;
      const height = 700;
      const left = window.screenX + (window.outerWidth - width) / 2;
      const top = window.screenY + (window.outerHeight - height) / 2;

      const popup = window.open(
        data.auth_url,
        'Gmail Authorization',
        `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
      );

      if (!popup) {
        throw new Error('Popup blocked. Please allow popups for this site.');
      }

      // Poll for popup close and check connection status
      const pollInterval = setInterval(async () => {
        if (popup.closed) {
          clearInterval(pollInterval);
          setLoading(false);

          // Check if authentication was successful
          try {
            const statusResponse = await fetch(`${API_BASE}/api/gmail/status`);
            const statusData = await statusResponse.json();

            if (statusData.connected) {
              onSuccess();
              onClose();
            } else {
              setError('Authentication was cancelled or failed.');
            }
          } catch (err) {
            setError('Failed to verify connection status.');
          }
        }
      }, 1000);

    } catch (err) {
      setError((err as Error).message);
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md mx-4 shadow-2xl">
        <CardContent className="p-0">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-500 to-cyan-500 p-6 relative">
            <button
              onClick={onClose}
              className="absolute top-4 right-4 text-white hover:bg-white/20 rounded-full p-1 transition-colors"
              disabled={loading}
            >
              <X size={20} />
            </button>
            <div className="flex items-center gap-3 text-white">
              <div className="bg-white/20 p-3 rounded-lg">
                <Mail size={32} />
              </div>
              <div>
                <h2 className="text-2xl font-bold">Connect Gmail</h2>
                <p className="text-blue-100 text-sm">Import claim emails automatically</p>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 space-y-4">
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="text-green-600 flex-shrink-0 mt-0.5" size={20} />
                <div>
                  <p className="font-medium text-sm">Automatic Claim Detection</p>
                  <p className="text-xs text-muted-foreground">
                    We'll scan your inbox for claim-related emails using keywords like "claim," "insurance," "accident," and more.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <CheckCircle2 className="text-green-600 flex-shrink-0 mt-0.5" size={20} />
                <div>
                  <p className="font-medium text-sm">Email & Attachment Processing</p>
                  <p className="text-xs text-muted-foreground">
                    Email content and attachments are converted to PDF and processed through our AI pipeline.
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Shield className="text-blue-600 flex-shrink-0 mt-0.5" size={20} />
                <div>
                  <p className="font-medium text-sm">Secure & Private</p>
                  <p className="text-xs text-muted-foreground">
                    We only read emails from your primary inbox. Your credentials are encrypted and stored securely.
                  </p>
                </div>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border-2 border-red-200 rounded-lg p-3 flex items-start gap-2">
                <AlertCircle className="text-red-600 flex-shrink-0 mt-0.5" size={18} />
                <div>
                  <p className="text-sm font-medium text-red-800">Connection Failed</p>
                  <p className="text-xs text-red-700">{error}</p>
                </div>
              </div>
            )}

            <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
              <p className="text-xs text-muted-foreground">
                <strong>Required Permissions:</strong> Read-only access to Gmail messages and ability to modify labels.
              </p>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-2">
              <Button
                onClick={onClose}
                variant="outline"
                className="flex-1"
                disabled={loading}
              >
                Cancel
              </Button>
              <Button
                onClick={handleConnect}
                className="flex-1 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
                    Connecting...
                  </>
                ) : (
                  <>
                    <Mail size={16} className="mr-2" />
                    Connect Gmail
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
