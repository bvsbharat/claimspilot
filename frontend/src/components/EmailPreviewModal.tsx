import React from 'react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { X, Mail, Paperclip, Clock, User, AlertCircle } from 'lucide-react';
import type { GmailEmail } from '../types';

interface EmailPreviewModalProps {
  isOpen: boolean;
  emails: GmailEmail[];
  onClose: () => void;
  onProcess: () => void;
  loading?: boolean;
}

export const EmailPreviewModal: React.FC<EmailPreviewModalProps> = ({
  isOpen,
  emails,
  onClose,
  onProcess,
  loading = false
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-3xl max-h-[80vh] flex flex-col shadow-2xl">
        <CardContent className="p-0 flex flex-col max-h-[80vh]">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-500 to-cyan-500 p-6 relative flex-shrink-0">
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
                <h2 className="text-2xl font-bold">Claim Emails Found</h2>
                <p className="text-blue-100 text-sm">
                  {emails.length} email{emails.length !== 1 ? 's' : ''} ready to process
                </p>
              </div>
            </div>
          </div>

          {/* Email List */}
          <div className="flex-1 overflow-y-auto p-6 space-y-3">
            {emails.length === 0 ? (
              <div className="text-center py-12">
                <AlertCircle className="mx-auto text-gray-400 mb-3" size={48} />
                <p className="text-lg font-semibold text-gray-600">No Emails Found</p>
                <p className="text-sm text-muted-foreground mt-1">
                  No claim-related emails were found in your inbox.
                </p>
              </div>
            ) : (
              emails.map((email, index) => (
                <div
                  key={email.id}
                  className="border-2 border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors bg-white"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      {/* Subject */}
                      <h3 className="font-semibold text-sm text-gray-900 truncate">
                        {email.subject}
                      </h3>

                      {/* From */}
                      <div className="flex items-center gap-2 mt-1">
                        <User size={14} className="text-gray-400 flex-shrink-0" />
                        <p className="text-xs text-muted-foreground truncate">
                          {email.from}
                        </p>
                      </div>

                      {/* Date */}
                      <div className="flex items-center gap-2 mt-1">
                        <Clock size={14} className="text-gray-400 flex-shrink-0" />
                        <p className="text-xs text-muted-foreground">
                          {new Date(email.date).toLocaleString()}
                        </p>
                      </div>

                      {/* Snippet */}
                      <p className="text-xs text-gray-600 mt-2 line-clamp-2">
                        {email.snippet}
                      </p>

                      {/* Attachments Badge */}
                      {email.has_attachments && (
                        <div className="flex items-center gap-1 mt-2">
                          <Paperclip size={14} className="text-blue-600" />
                          <span className="text-xs text-blue-600 font-medium">
                            {email.attachment_count || 0} attachment{email.attachment_count !== 1 ? 's' : ''}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Index Badge */}
                    <Badge variant="outline" className="flex-shrink-0">
                      #{index + 1}
                    </Badge>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Info Banner */}
          {emails.length > 0 && (
            <div className="flex-shrink-0 bg-blue-50 border-t-2 border-blue-200 p-4">
              <div className="flex items-start gap-2">
                <AlertCircle className="text-blue-600 flex-shrink-0 mt-0.5" size={16} />
                <p className="text-xs text-blue-800">
                  <strong>What happens next:</strong> Each email and its attachments will be converted to a PDF
                  and processed through our automated claims triage system. Emails will be marked as read and
                  labeled "CLAIM_PROCESSED" in your Gmail.
                </p>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex-shrink-0 p-6 border-t border-gray-200 flex gap-3">
            <Button
              onClick={onClose}
              variant="outline"
              className="flex-1"
              disabled={loading}
            >
              Cancel
            </Button>
            <Button
              onClick={onProcess}
              className="flex-1 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600"
              disabled={loading || emails.length === 0}
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
                  Processing...
                </>
              ) : (
                <>
                  <Mail size={16} className="mr-2" />
                  Process {emails.length} Email{emails.length !== 1 ? 's' : ''}
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
