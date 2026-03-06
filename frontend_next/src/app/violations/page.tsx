"use client";

import { useEffect, useState } from "react";

interface Violation {
  id: number;
  person_name: string;
  timestamp: string;
  image_path: string;
  track_id: number;
  status: string;
}

export default function Violations() {
  const [violations, setViolations] = useState<Violation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchViolations = async () => {
      try {
        const res = await fetch("http://localhost:8085/violations_list");
        if (res.ok) {
          const data = await res.json();
          setViolations(Array.isArray(data) ? data : []);
        }
      } catch (e) {
        console.error("Failed to fetch violations", e);
      } finally {
        setLoading(false);
      }
    };

    fetchViolations();
  }, []);

  return (
    <div className="violations animate-fade-in">
      <header className="dash-header">
        <h2 className="section-title">Violation History</h2>
        <p className="subtitle">Database of non-compliant incidents recorded by AI nodes.</p>
      </header>

      {loading ? (
        <div className="loading">Initializing Secure Fetch...</div>
      ) : (
        <div className="violations-list">
          {violations.length === 0 ? (
            <div className="glass-card empty-state">
              <p>No violations recorded in the current session.</p>
            </div>
          ) : (
            violations.map((v) => (
              <div key={v.id} className="violation-item glass-card">
                <div className="violation-img">
                   <img src={`http://localhost:8085/${v.image_path}`} alt="Violation Crop" />
                </div>
                <div className="violation-details">
                   <div className="violation-top">
                      <span className="name">{v.person_name}</span>
                      <span className="timestamp">{new Date(v.timestamp).toLocaleString()}</span>
                   </div>
                   <div className="violation-meta">
                      <span className="tag tag-danger">NO ID CARD</span>
                      <span className="track-id">Track: #{v.track_id}</span>
                   </div>
                </div>
                <button className="btn-action">VIEW DETAILS</button>
              </div>
            ))
          )}
        </div>
      )}

      <style jsx>{`
        .loading {
          padding: 4rem;
          text-align: center;
          font-weight: 700;
          opacity: 0.5;
          letter-spacing: 1px;
        }
        .violations-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
        .violation-item {
          display: flex;
          align-items: center;
          padding: 1rem;
          gap: 1.5rem;
        }
        .violation-img {
          width: 80px;
          height: 80px;
          border-radius: 8px;
          overflow: hidden;
          background: #000;
          border: 1px solid var(--glass-border);
        }
        .violation-img img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
        .violation-details {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        .violation-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .name {
          font-size: 1.15rem;
          font-weight: 700;
        }
        .timestamp {
          font-size: 0.8rem;
          opacity: 0.5;
          font-family: monospace;
        }
        .violation-meta {
          display: flex;
          gap: 1rem;
          align-items: center;
        }
        .tag {
          font-size: 0.7rem;
          font-weight: 800;
          padding: 0.2rem 0.6rem;
          border-radius: 4px;
        }
        .tag-danger {
          background: rgba(239, 68, 68, 0.1);
          color: var(--danger);
          border: 1px solid rgba(239, 68, 68, 0.2);
        }
        .track-id {
          font-size: 0.75rem;
          opacity: 0.4;
          font-weight: 600;
        }
        .btn-action {
          background: transparent;
          border: 1px solid var(--glass-border);
          color: white;
          padding: 0.5rem 1rem;
          border-radius: 6px;
          font-size: 0.75rem;
          font-weight: 700;
          cursor: pointer;
          transition: all 0.2s;
        }
        .btn-action:hover {
          background: var(--glass-border);
          border-color: rgba(255, 255, 255, 0.2);
        }
        .empty-state {
           padding: 4rem;
           text-align: center;
           opacity: 0.5;
        }
      `}</style>
    </div>
  );
}
