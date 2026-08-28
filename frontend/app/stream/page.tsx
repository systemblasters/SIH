"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";

interface StreamResult {
  overall_probability: number;
  risk_level: "low" | "medium" | "high";
  per_model_scores: {
    aasist: number;
    wav2vec: number;
    spectro_cnn: number;
  };
  timestamp: number;
}

export default function Stream() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [history, setHistory] = useState<StreamResult[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const startStream = () => {
    setIsStreaming(true);
    setHistory([]);

    const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL?.replace("http", "ws") || "ws://localhost:8000";
    wsRef.current = new WebSocket(`${baseUrl}/analyze-stream`);

    wsRef.current.onmessage = (event) => {
      const data: StreamResult = JSON.parse(event.data);
      setHistory((prev) => {
        const newHistory = [...prev, data];
        if (newHistory.length > 20) newHistory.shift(); // Keep last 20 chunks
        return newHistory;
      });
    };

    // Simulate sending audio chunks every 500ms
    intervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        // Send a dummy byte array representing an audio chunk
        const dummyChunk = new Uint8Array(1024);
        crypto.getRandomValues(dummyChunk);
        wsRef.current.send(dummyChunk);
      }
    }, 500);
  };

  const stopStream = () => {
    setIsStreaming(false);
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (wsRef.current) wsRef.current.close();
  };

  useEffect(() => {
    return () => {
      stopStream();
    };
  }, []);

  const latestResult = history[history.length - 1];

  return (
    <main className="min-h-screen p-8 md:p-24 flex flex-col items-center">
      <div className="w-full max-w-4xl flex justify-between items-center mb-12">
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-cyan-400">
          Real-Time Monitoring
        </h1>
        <Link 
          href="/" 
          className="px-4 py-2 rounded-lg bg-surface border border-border hover:bg-surface-hover transition-colors font-medium"
        >
          ← Back to Upload
        </Link>
      </div>

      <div className="w-full max-w-4xl glass-panel p-8">
        <div className="flex justify-between items-center mb-8 border-b border-border pb-6">
          <div>
            <h2 className="text-xl font-semibold">Live Call Interception</h2>
            <p className="text-sm text-gray-400 mt-1">Simulating continuous chunk analysis</p>
          </div>
          
          <button
            onClick={isStreaming ? stopStream : startStream}
            className={`px-6 py-3 rounded-lg font-bold transition-all shadow-lg ${
              isStreaming 
                ? "bg-danger hover:bg-red-600 text-white shadow-red-500/20 animate-pulse" 
                : "bg-success hover:bg-emerald-600 text-white shadow-emerald-500/20"
            }`}
          >
            {isStreaming ? "Stop Monitoring" : "Start Monitoring"}
          </button>
        </div>

        {/* Dashboard */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Current Status */}
          <div className="col-span-1 md:col-span-2 bg-surface p-6 rounded-xl border border-border flex flex-col justify-center">
            <p className="text-gray-400 mb-2">Live Deepfake Probability</p>
            {latestResult ? (
              <div className="flex items-end gap-4">
                <span className={`text-6xl font-black ${
                  latestResult.risk_level === 'high' ? 'text-danger' :
                  latestResult.risk_level === 'medium' ? 'text-warning' :
                  'text-success'
                }`}>
                  {(latestResult.overall_probability * 100).toFixed(1)}%
                </span>
                <span className="text-xl pb-2 text-gray-400 uppercase tracking-widest">{latestResult.risk_level}</span>
              </div>
            ) : (
              <p className="text-3xl text-gray-500 font-mono">--.-%</p>
            )}
          </div>

          {/* Model Metrics */}
          <div className="col-span-1 flex flex-col gap-3">
            {['aasist', 'wav2vec', 'spectro_cnn'].map((model) => (
              <div key={model} className="bg-surface/50 p-3 rounded-lg border border-border flex justify-between items-center">
                <span className="text-xs uppercase text-gray-400">{model}</span>
                <span className="font-mono text-sm">
                  {latestResult ? latestResult.per_model_scores[model as keyof typeof latestResult.per_model_scores].toFixed(3) : '0.000'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Timeline Chart Visualization */}
        <div className="w-full h-48 bg-surface rounded-xl border border-border p-4 flex items-end gap-1 relative overflow-hidden">
          {history.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center text-gray-500">
              Awaiting stream data...
            </div>
          )}
          {history.map((res, i) => (
            <div 
              key={i}
              className={`flex-1 rounded-t-sm transition-all duration-300 ease-in-out ${
                res.risk_level === 'high' ? 'bg-danger' :
                res.risk_level === 'medium' ? 'bg-warning' :
                'bg-success'
              }`}
              style={{ 
                height: `${res.overall_probability * 100}%`,
                opacity: 0.3 + (i / history.length) * 0.7 // fade out older chunks
              }}
            ></div>
          ))}
        </div>
      </div>
    </main>
  );
}
