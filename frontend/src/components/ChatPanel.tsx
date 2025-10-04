import { useState, useEffect, useRef } from "react";
import {
  X,
  Send,
  MessageSquare,
  FileText,
  Loader2,
  Sparkles,
} from "lucide-react";
import { marked } from "marked";
import type { ChatMessage, ProcessedData } from "../types";
import { useChatAPI } from "../hooks/useChatAPI";
import { DocumentViewer } from "./DocumentViewer";
import { useSSE } from "../hooks/useSSE";

// Configure marked for better formatting
marked.setOptions({
  breaks: true,
  gfm: true,
});

interface ChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
  selectedClaimId?: string | null;
}

export function ChatPanel({
  isOpen,
  onClose,
  selectedClaimId,
}: ChatPanelProps) {
  const [activeTab, setActiveTab] = useState<"chat" | "document">("chat");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [processedData, setProcessedData] = useState<ProcessedData | null>(
    null
  );
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { sendMessage, getProcessedData, loading, error } = useChatAPI();
  const events = useSSE("http://localhost:8080/api/events/stream");

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen && activeTab === "chat") {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen, activeTab]);

  // Load processed data when claim is selected or when panel opens
  useEffect(() => {
    if (selectedClaimId && isOpen && activeTab === "document") {
      loadProcessedData(selectedClaimId);
    }
  }, [selectedClaimId, isOpen, activeTab]);

  // Add welcome message on first load
  useEffect(() => {
    if (messages.length === 0 && isOpen) {
      setMessages([
        {
          id: "welcome",
          role: "assistant",
          content:
            "Hi! I'm your claims assistant. I can answer questions about processed claims, explain extracted data, and provide insights. Ask me anything!",
          timestamp: new Date().toISOString(),
        },
      ]);
    }
  }, [isOpen]);

  // Listen for claim events
  useEffect(() => {
    if (events.length > 0) {
      const latestEvent = events[events.length - 1];
      if (
        latestEvent.type === "claim_processed" ||
        latestEvent.type === "claim_status_update"
      ) {
        const claimId = latestEvent.claim_id;
        const message = latestEvent.message;

        // Add real-time update to chat
        const updateMessage: ChatMessage = {
          id: `event-${Date.now()}`,
          role: "assistant",
          content: `📢 **Real-time Update**: ${message}`,
          timestamp: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, updateMessage]);

        // Reload processed data if it's the selected claim
        if (claimId === selectedClaimId) {
          loadProcessedData(claimId);
        }
      }
    }
  }, [events]);

  const loadProcessedData = async (claimId: string) => {
    const data = await getProcessedData(claimId);
    if (data) {
      setProcessedData(data);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: inputValue,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");

    // Send to RAG service
    const response = await sendMessage(inputValue, selectedClaimId || undefined);

    if (response) {
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: response.answer,
        timestamp: new Date().toISOString(),
        sources: response.sources,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } else if (error) {
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: `Sorry, I encountered an error: ${error}`,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/30 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Panel */}
      <div
        className={`fixed right-0 top-0 bottom-0 w-full md:w-[600px] bg-white shadow-2xl z-50 flex flex-col transform transition-transform duration-300 ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-violet-600 to-purple-600 text-white p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/20 rounded-lg">
              <Sparkles size={20} />
            </div>
            <div>
              <h2 className="text-lg font-bold">Claims AI Assistant</h2>
              <p className="text-xs text-violet-100">
                {selectedClaimId
                  ? `Viewing: ${selectedClaimId}`
                  : "Ask about any claim"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab("chat")}
            className={`flex-1 px-4 py-3 font-medium transition-colors ${
              activeTab === "chat"
                ? "border-b-2 border-violet-600 text-violet-600 bg-violet-50"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <MessageSquare size={18} />
              <span>Chat</span>
            </div>
          </button>
          <button
            onClick={() => setActiveTab("document")}
            className={`flex-1 px-4 py-3 font-medium transition-colors ${
              activeTab === "document"
                ? "border-b-2 border-violet-600 text-violet-600 bg-violet-50"
                : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
            }`}
          >
            <div className="flex items-center justify-center gap-2">
              <FileText size={18} />
              <span>Document</span>
            </div>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {activeTab === "chat" ? (
            <div className="flex flex-col h-full">
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${
                      message.role === "user" ? "justify-end" : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-[80%] rounded-lg p-4 shadow-sm ${
                        message.role === "user"
                          ? "bg-violet-600 text-white"
                          : "bg-white text-gray-900 border border-gray-200"
                      }`}
                    >
                      <div
                        className={`prose prose-sm max-w-none ${
                          message.role === "user"
                            ? "prose-invert"
                            : ""
                        }`}
                        dangerouslySetInnerHTML={{
                          __html: marked.parse(message.content),
                        }}
                      />
                      {message.sources && message.sources.length > 0 && (
                        <div className={`mt-3 pt-3 border-t ${
                          message.role === "user" ? "border-violet-400" : "border-gray-200"
                        }`}>
                          <p className="text-xs font-semibold mb-2">📌 Sources:</p>
                          {message.sources.map((source, idx) => (
                            <div
                              key={idx}
                              className={`text-xs rounded p-2 mb-1 ${
                                message.role === "user"
                                  ? "bg-violet-700"
                                  : "bg-gray-50"
                              }`}
                            >
                              <span className="font-mono font-medium">
                                {source.claim_id}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                      <div className={`text-xs mt-2 ${
                        message.role === "user" ? "opacity-70" : "text-gray-500"
                      }`}>
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))}

                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 rounded-lg p-3">
                      <Loader2 className="animate-spin text-violet-600" size={20} />
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <div className="border-t border-gray-200 p-4">
                <div className="flex gap-2">
                  <input
                    ref={inputRef}
                    type="text"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask a question about claims..."
                    disabled={loading}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-violet-500 disabled:bg-gray-100"
                  />
                  <button
                    onClick={handleSendMessage}
                    disabled={!inputValue.trim() || loading}
                    className="px-4 py-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
                  >
                    <Send size={20} />
                  </button>
                </div>
                {error && (
                  <p className="text-sm text-red-600 mt-2">Error: {error}</p>
                )}
                <p className="text-xs text-gray-500 mt-2">
                  Press Enter to send • Shift+L to close
                </p>
              </div>
            </div>
          ) : (
            <div className="h-full p-4">
              {selectedClaimId ? (
                <DocumentViewer data={processedData} loading={loading} claimId={selectedClaimId} />
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <FileText size={48} className="mb-4 opacity-50" />
                  <p className="text-lg font-medium">No Claim Selected</p>
                  <p className="text-sm mt-2">Select a claim from the board to view its documents</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
