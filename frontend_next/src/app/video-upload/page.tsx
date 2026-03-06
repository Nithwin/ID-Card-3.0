"use client";

import { useState } from "react";

interface AnalysisResult {
  violations_found: number;
  total_frames: number;
}

export default function VideoUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("idle"); // idle, uploading, processing, complete
  const [results, setResults] = useState<AnalysisResult | null>(null);

  const handleUpload = async () => {
    if (!file) return;

    setStatus("uploading");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8085/analyze_video", {
        method: "POST",
        body: formData,
      });

      const body = response.body;
      if (!body) throw new Error("No response body");
      const reader = body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (!line.trim()) continue;
          const data = JSON.parse(line);

          if (data.status === "processing") {
            setStatus("processing");
            setProgress(data.progress);
          } else if (data.status === "complete") {
            setStatus("complete");
            setResults(data);
          }
        }
      }
    } catch (e) {
      console.error("Upload failed", e);
      setStatus("error");
    }
  };

  return (
    <div className="video-upload animate-fade-in">
      <header className="dash-header">
        <h2 className="section-title">Video Forensics</h2>
        <p className="subtitle">Process recorded surveillance footage for retroactive compliance audits.</p>
      </header>

      <div className="upload-container glass-card">
        {status === "idle" && (
          <div className="upload-zone">
            <input 
              type="file" 
              id="file-input" 
              className="hidden" 
              onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
            />
            <label htmlFor="file-input" className="drop-area">
              <div className="upload-icon">📂</div>
              <h3>{file ? file.name : "Select Video File"}</h3>
              <p>Drag and drop or click to browse</p>
            </label>
            {file && (
              <button className="btn-primary" onClick={handleUpload}>
                START AI ANALYSIS
              </button>
            )}
          </div>
        )}

        {(status === "uploading" || status === "processing") && (
          <div className="processing-state">
            <div className="loader-container">
               <div className="loader"></div>
            </div>
            <h3>{status === "uploading" ? "Broadcasting Stream..." : "AI Nucleus Processing..."}</h3>
            <div className="progress-wrapper">
               <div className="progress-bar-large">
                  <div className="progress-fill" style={{width: `${progress}%`}}></div>
               </div>
               <span className="progress-text">{progress}% COMPLETE</span>
            </div>
          </div>
        )}

        {status === "complete" && results && (
          <div className="results-state">
            <div className="results-header">
               <div className="result-icon success">✓</div>
               <h3>Analysis Complete</h3>
            </div>
            
            <div className="results-summary-grid">
               <div className="res-card">
                  <span className="res-label">Violations Found</span>
                  <span className="res-val text-danger">{results.violations_found}</span>
               </div>
               <div className="res-card">
                  <span className="res-label">Frames Audited</span>
                  <span className="res-val">{results.total_frames}</span>
               </div>
            </div>

            <button className="btn-primary" onClick={() => setStatus("idle")}>
               PROCESS ANOTHER FILE
            </button>
          </div>
        )}
      </div>

      <style jsx>{`
        .upload-container {
          max-width: 600px;
          margin: 0 auto;
          padding: 3rem;
          min-height: 400px;
          display: flex;
          align-items: center;
          justify-content: center;
          text-align: center;
        }
        .upload-zone {
          display: flex;
          flex-direction: column;
          gap: 2rem;
          width: 100%;
        }
        .hidden { display: none; }
        .drop-area {
          border: 2px dashed var(--glass-border);
          padding: 3rem;
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.2s;
        }
        .drop-area:hover {
          border-color: var(--primary);
          background: rgba(79, 70, 229, 0.05);
        }
        .upload-icon {
          font-size: 3rem;
          margin-bottom: 1rem;
        }
        .processing-state {
          width: 100%;
          display: flex;
          flex-direction: column;
          gap: 2rem;
        }
        .loader-container {
           margin: 0 auto;
        }
        .loader {
          width: 60px;
          height: 60px;
          border: 4px solid var(--glass-border);
          border-top: 4px solid var(--primary);
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        .progress-wrapper {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }
        .progress-bar-large {
          height: 8px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
          overflow: hidden;
        }
        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, var(--primary), var(--accent));
          transition: width 0.3s ease;
        }
        .progress-text {
          font-size: 0.8rem;
          font-weight: 800;
          opacity: 0.6;
        }
        .results-state {
           width: 100%;
           display: flex;
           flex-direction: column;
           gap: 2.5rem;
        }
        .results-header {
           display: flex;
           flex-direction: column;
           gap: 1rem;
           align-items: center;
        }
        .result-icon {
           width: 50px;
           height: 50px;
           border-radius: 50%;
           display: flex;
           align-items: center;
           justify-content: center;
           font-size: 1.5rem;
           font-weight: 800;
        }
        .result-icon.success {
           background: rgba(16, 185, 129, 0.1);
           color: var(--success);
           border: 2px solid var(--success);
        }
        .results-summary-grid {
           display: grid;
           grid-template-columns: 1fr 1fr;
           gap: 1rem;
        }
        .res-card {
           padding: 1.5rem;
           background: rgba(255, 255, 255, 0.03);
           border-radius: 8px;
           display: flex;
           flex-direction: column;
           gap: 0.5rem;
        }
        .res-label {
           font-size: 0.7rem;
           font-weight: 700;
           opacity: 0.5;
           text-transform: uppercase;
        }
        .res-val {
           font-size: 1.75rem;
           font-weight: 800;
        }
      `}</style>
    </div>
  );
}
