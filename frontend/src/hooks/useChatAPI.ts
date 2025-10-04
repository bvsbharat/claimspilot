import { useState } from "react";
import type {
  ProcessedData,
  RAGQueryResponse,
} from "../types";

const API_BASE = "http://localhost:8080";

export function useChatAPI() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async (
    query: string,
    claimId?: string
  ): Promise<RAGQueryResponse | null> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/chat/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query, claim_id: claimId }),
      });

      if (!response.ok) {
        throw new Error(`Query failed: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "An error occurred";
      setError(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const getProcessedData = async (
    claimId: string
  ): Promise<ProcessedData | null> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_BASE}/api/chat/processed-data/${claimId}`
      );

      if (!response.ok) {
        if (response.status === 404) {
          throw new Error("No processed data found for this claim");
        }
        throw new Error(`Failed to fetch processed data: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "An error occurred";
      setError(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const getClaimContext = async (claimId: string): Promise<any | null> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/chat/context/${claimId}`);

      if (!response.ok) {
        throw new Error(`Failed to fetch claim context: ${response.statusText}`);
      }

      const data = await response.json();
      return data;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "An error occurred";
      setError(errorMessage);
      return null;
    } finally {
      setLoading(false);
    }
  };

  return {
    sendMessage,
    getProcessedData,
    getClaimContext,
    loading,
    error,
  };
}
