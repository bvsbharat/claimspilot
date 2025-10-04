import { useState } from "react";
import type { ProcessedData } from "../types";
import { FileText, Code2, Copy, Check } from "lucide-react";

interface DocumentViewerProps {
  data: ProcessedData | null;
  loading: boolean;
  claimId: string;
}

export function DocumentViewer({ data, loading, claimId }: DocumentViewerProps) {
  const [viewMode, setViewMode] = useState<"parsed" | "details">("parsed");
  const [copied, setCopied] = useState(false);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-violet-600" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-12 text-gray-500">
        <FileText className="mx-auto h-12 w-12 mb-3 opacity-50" />
        <p>No document data available</p>
        <p className="text-sm mt-2">Select a claim to view its processed data</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* View Mode Tabs */}
      <div className="flex border-b border-gray-200 mb-4">
        <button
          onClick={() => setViewMode("parsed")}
          className={`px-4 py-2 font-medium transition-colors ${
            viewMode === "parsed"
              ? "border-b-2 border-violet-600 text-violet-600"
              : "text-gray-600 hover:text-gray-900"
          }`}
        >
          <div className="flex items-center gap-2">
            <FileText size={18} />
            <span>Parsed Data</span>
          </div>
        </button>
        <button
          onClick={() => setViewMode("details")}
          className={`px-4 py-2 font-medium transition-colors ${
            viewMode === "details"
              ? "border-b-2 border-violet-600 text-violet-600"
              : "text-gray-600 hover:text-gray-900"
          }`}
        >
          <div className="flex items-center gap-2">
            <Code2 size={18} />
            <span>Details</span>
          </div>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {viewMode === "parsed" ? (
          <div className="space-y-4">
            {/* Document Info */}
            <div className="bg-gradient-to-r from-violet-50 to-purple-50 border border-violet-200 rounded-lg p-4 shadow-sm">
              <h3 className="font-bold text-violet-900 mb-3 text-lg flex items-center gap-2">
                <FileText size={20} />
                Document Information
              </h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="bg-white rounded p-2">
                  <span className="text-gray-600 text-xs">Claim ID:</span>
                  <div className="font-mono text-violet-700 font-semibold mt-1">
                    {data.claim_id}
                  </div>
                </div>
                <div className="bg-white rounded p-2">
                  <span className="text-gray-600 text-xs">Type:</span>
                  <div className="font-semibold text-violet-700 mt-1 capitalize">
                    {data.document_type}
                  </div>
                </div>
                <div className="bg-white rounded p-2">
                  <span className="text-gray-600 text-xs">Characters:</span>
                  <div className="font-semibold text-violet-700 mt-1">
                    {data.char_count.toLocaleString()}
                  </div>
                </div>
                <div className="bg-white rounded p-2">
                  <span className="text-gray-600 text-xs">Tables:</span>
                  <div className="font-semibold text-violet-700 mt-1">
                    {data.tables.length}
                  </div>
                </div>
              </div>
            </div>

            {/* Raw Text */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 relative">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900">
                  Extracted Text
                </h3>
                <button
                  onClick={() => handleCopy(data.raw_text)}
                  className="flex items-center gap-2 px-3 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors"
                >
                  {copied ? (
                    <>
                      <Check size={14} className="text-green-600" />
                      <span className="text-green-600">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy size={14} />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>
              <div className="bg-white border border-gray-200 rounded p-3 max-h-96 overflow-auto">
                <pre className="text-sm text-gray-800 whitespace-pre-wrap font-mono">
                  {data.raw_text}
                </pre>
              </div>
            </div>

            {/* Tables */}
            {data.tables.length > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-3">
                  Extracted Tables ({data.tables.length})
                </h3>
                <div className="space-y-4">
                  {data.tables.map((table, idx) => (
                    <div key={idx} className="bg-white rounded border border-blue-200 p-3">
                      <p className="text-sm font-medium text-blue-800 mb-2">
                        Table {idx + 1}
                      </p>
                      <div className="overflow-auto">
                        <pre className="text-xs text-gray-700">
                          {JSON.stringify(table, null, 2)}
                        </pre>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {/* Structured Data JSON */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 relative">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900">
                  Structured Data (JSON)
                </h3>
                <button
                  onClick={() =>
                    handleCopy(JSON.stringify(data.structured_data, null, 2))
                  }
                  className="flex items-center gap-2 px-3 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors"
                >
                  {copied ? (
                    <>
                      <Check size={14} className="text-green-600" />
                      <span className="text-green-600">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy size={14} />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>
              <div className="bg-white border border-gray-200 rounded p-3 max-h-[600px] overflow-auto">
                <pre className="text-sm text-gray-800 font-mono">
                  {JSON.stringify(data.structured_data, null, 2)}
                </pre>
              </div>
            </div>

            {/* Key Fields */}
            <div className="bg-violet-50 border border-violet-200 rounded-lg p-4">
              <h3 className="font-semibold text-violet-900 mb-3">Key Fields</h3>
              <div className="space-y-2">
                {Object.entries(data.structured_data).map(([key, value]) => (
                  <div key={key} className="flex flex-col">
                    <span className="text-sm font-medium text-violet-700">
                      {key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase())}:
                    </span>
                    <span className="text-sm text-gray-700 ml-4 mt-1">
                      {typeof value === "object"
                        ? JSON.stringify(value)
                        : String(value || "N/A")}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
