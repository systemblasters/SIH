"use client";

import { useState } from "react";
import Link from "next/link";

interface AnalysisResult {
  job_id: string;
  overall_deepfake_probability: number;
  risk_level: "low" | "medium" | "high";
  per_model_scores: {
    aasist: number;
    wav2vec: number;
    spectro_cnn: number;
  };
  report:
  | string
  | {
    case_details: {
      job_id: string;
      timestamp: string;
      filename: string;
    };
    risk_assessment: {
      risk_level: string;
      deepfake_probability: number;
      verdict: string;
    };
    model_results: Record<string, number>;
    technical_findings: Record<string, string>;
    interpretation: string;
    recommended_actions: string[];
    disclaimer: string;
  };
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      // /api is forwarded by Next.js to the FastAPI backend inside the same Render container.
      const res = await fetch("/api/analyze-file", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        throw new Error("Failed to analyze file");
      }

      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-8 md:p-24 flex flex-col items-center">
      <div className="w-full max-w-4xl flex justify-between items-center mb-12">
        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
          AI Voice Detector
        </h1>
        <Link
          href="/stream"
          className="px-4 py-2 rounded-lg bg-surface border border-border hover:bg-surface-hover transition-colors font-medium"
        >
          Live Stream Mode →
        </Link>
      </div>

      <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Upload Section */}
        <div className="glass-panel p-8 flex flex-col items-center justify-center space-y-6">
          <h2 className="text-xl font-semibold w-full text-left border-b border-border pb-4">Audio Upload</h2>

          <label className="flex flex-col items-center justify-center w-full h-64 border-2 border-border border-dashed rounded-xl cursor-pointer bg-surface/50 hover:bg-surface transition-colors">
            <div className="flex flex-col items-center justify-center pt-5 pb-6">
              <svg className="w-10 h-10 mb-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
              </svg>
              <p className="mb-2 text-sm text-gray-400"><span className="font-semibold">Click to upload</span> or drag and drop</p>
              <p className="text-xs text-gray-500">WAV, MP3, or OGG</p>
            </div>
            <input type="file" className="hidden" accept="audio/*" onChange={handleFileChange} />
          </label>

          {file && (
            <div className="w-full text-sm text-center truncate px-4 py-2 bg-surface rounded-md border border-border">
              Selected: {file.name}
            </div>
          )}

          <button
            onClick={handleAnalyze}
            disabled={!file || loading}
            className={`w-full py-3 rounded-lg font-bold transition-all ${!file || loading
              ? "bg-surface-hover text-gray-400 cursor-not-allowed"
              : "bg-brand hover:bg-brand-hover text-white shadow-lg shadow-blue-500/20"
              }`}
          >
            {loading ? "Analyzing..." : "Analyze Audio"}
          </button>

          {error && <p className="text-danger text-sm">{error}</p>}
        </div>

        {/* Results Section */}
        <div className="glass-panel p-8 flex flex-col space-y-6">
          <h2 className="text-xl font-semibold border-b border-border pb-4">Analysis Results</h2>

          {!result && !loading && (
            <div className="flex-1 flex items-center justify-center text-gray-400 italic">
              Upload an audio file to see results.
            </div>
          )}

          {loading && (
            <div className="flex-1 flex flex-col items-center justify-center space-y-4">
              <div className="w-12 h-12 border-4 border-brand border-t-transparent rounded-full animate-spin"></div>
              <p className="text-gray-400 animate-pulse">Running forensic models...</p>
            </div>
          )}

          {result && !loading && (
            <div className="flex-1 flex flex-col space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

              {/* Overall Score & Badge */}
              <div className="flex items-center justify-between bg-surface p-4 rounded-lg border border-border">
                <div>
                  <p className="text-sm text-gray-400 mb-1">Overall Deepfake Probability</p>
                  <p className="text-3xl font-bold">{(result.overall_deepfake_probability * 100).toFixed(1)}%</p>
                </div>
                <div className={`px-4 py-2 rounded-full font-bold uppercase tracking-wider text-sm ${result.risk_level === 'high' ? 'bg-danger/20 text-danger border border-danger/50' :
                  result.risk_level === 'medium' ? 'bg-warning/20 text-warning border border-warning/50' :
                    'bg-success/20 text-success border border-success/50'
                  }`}>
                  {result.risk_level} Risk
                </div>
              </div>

              {/* Progress Bar */}
              <div className="w-full h-3 bg-surface rounded-full overflow-hidden border border-border">
                <div
                  className={`h-full transition-all duration-1000 ${result.risk_level === 'high' ? 'bg-danger' :
                    result.risk_level === 'medium' ? 'bg-warning' :
                      'bg-success'
                    }`}
                  style={{ width: `${result.overall_deepfake_probability * 100}%` }}
                ></div>
              </div>

              {/* Model Scores Grid */}
              <div>
                <p className="text-sm font-semibold mb-3 text-gray-300">Model Diagnostics</p>
                <div className="grid grid-cols-3 gap-3">
                  {Object.entries(result.per_model_scores).map(([model, score]) => (
                    <div key={model} className="bg-surface/50 p-3 rounded border border-border flex flex-col items-center justify-center">
                      <p className="text-xs text-gray-400 uppercase">{model}</p>
                      <p className="text-lg font-mono mt-1">{(score as number).toFixed(2)}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Gemini AI Report */}
              <div className="flex-1">
                <p className="text-sm font-semibold mb-2 text-gray-300 flex items-center gap-2">
                  <svg
                    className="w-4 h-4 text-brand"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                      clipRule="evenodd"
                    />
                  </svg>
                  AI Forensic Report
                </p>

                <div className="bg-surface/80 p-4 rounded-lg border border-border text-sm leading-relaxed text-gray-300 h-full whitespace-pre-wrap break-words text-left">
                  {typeof result.report === "string" ? (
                    <p className="whitespace-pre-wrap break-words">{result.report}</p>
                  ) : (
                    <div className="space-y-5 text-left text-gray-200">
                      {/* Case details */}
                      <section className="border-b border-border pb-4">
                        <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-gray-400">
                          Case details
                        </h3>

                        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                          <div className="min-w-0">
                            <p className="mb-1 text-xs text-gray-500">Job ID</p>
                            <p className="break-all text-sm text-gray-200">
                              {result.report.case_details?.job_id || "N/A"}
                            </p>
                          </div>

                          <div className="min-w-0">
                            <p className="mb-1 text-xs text-gray-500">Analysis time</p>
                            <p className="break-words text-sm text-gray-200">
                              {result.report.case_details?.timestamp || "N/A"}
                            </p>
                          </div>

                          <div className="min-w-0">
                            <p className="mb-1 text-xs text-gray-500">Audio file</p>
                            <p className="break-all text-sm text-gray-200">
                              {result.report.case_details?.filename || "N/A"}
                            </p>
                          </div>
                        </div>
                      </section>

                      {/* Risk assessment */}
                      <section className="border-b border-border pb-4">
                        <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-gray-400">
                          Risk assessment
                        </h3>

                        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                          <span
                            className={`w-fit rounded-full px-3 py-1 text-xs font-bold ${result.risk_level === "high"
                              ? "bg-red-500/20 text-red-300"
                              : result.risk_level === "medium"
                                ? "bg-yellow-500/20 text-yellow-300"
                                : "bg-green-500/20 text-green-300"
                              }`}
                          >
                            {result.report.risk_assessment?.risk_level || result.risk_level?.toUpperCase()}
                          </span>

                          <p className="text-sm font-semibold text-gray-100">
                            {result.report.risk_assessment?.deepfake_probability ?? 0}% deepfake probability
                          </p>
                        </div>

                        <p className="mt-3 leading-6 text-gray-300">
                          {result.report.risk_assessment?.verdict}
                        </p>
                      </section>

                      {/* Model results */}
                      <section className="border-b border-border pb-4">
                        <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-gray-400">
                          Model results
                        </h3>

                        <div className="space-y-2">
                          {Object.entries(result.report.model_results || {}).map(([modelName, score]) => (
                            <div
                              className="flex items-center justify-between gap-4 rounded-md bg-white/[0.03] px-3 py-2"
                              key={modelName}
                            >
                              <span className="text-sm text-gray-300">{modelName}</span>
                              <strong className="text-sm text-gray-100">{String(score)}%</strong>
                            </div>
                          ))}
                        </div>
                      </section>

                      {/* Technical findings */}
                      <section className="border-b border-border pb-4">
                        <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-gray-400">
                          Technical findings
                        </h3>

                        <div className="space-y-2">
                          {Object.entries(result.report.technical_findings || {}).map(([finding, value]) => (
                            <div
                              className="flex flex-col gap-1 rounded-md bg-white/[0.03] px-3 py-2 sm:flex-row sm:items-center sm:justify-between sm:gap-4"
                              key={finding}
                            >
                              <span className="text-sm text-gray-300">✓ {finding}</span>
                              <strong className="text-sm font-medium text-gray-100">{String(value)}</strong>
                            </div>
                          ))}
                        </div>
                      </section>

                      {/* Interpretation */}
                      <section className="border-b border-border pb-4">
                        <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-gray-400">
                          Interpretation
                        </h3>

                        <p className="leading-7 text-gray-300">
                          {result.report.interpretation}
                        </p>
                      </section>

                      {/* Recommended actions */}
                      <section className="border-b border-border pb-4">
                        <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-gray-400">
                          Recommended actions
                        </h3>

                        <ul className="list-disc space-y-2 pl-5 leading-6 text-gray-300">
                          {(result.report.recommended_actions || []).map((action: string) => (
                            <li key={action}>{action}</li>
                          ))}
                        </ul>
                      </section>

                      {/* Disclaimer */}
                      <section className="rounded-lg border border-amber-400/20 bg-amber-400/10 p-4">
                        <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-amber-200">
                          Disclaimer
                        </h3>

                        <p className="text-sm leading-6 text-amber-100/90">
                          {result.report.disclaimer}
                        </p>
                      </section>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
