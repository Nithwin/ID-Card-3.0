"use client";

import { useEffect, useState } from "react";

export default function Dashboard() {
  const [stats, setStats] = useState({
    total_detections: 0,
    compliance_rate: "100%",
    violations: 0,
    active_cameras: 1,
    system_status: "stable"
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch("http://localhost:8085/stats");
        if (res.ok) {
          const data = await res.json();
          setStats({
            total_detections: data.total_detections || 0,
            compliance_rate: data.compliance_rate || "100%",
            violations: data.violations || 0,
            active_cameras: data.active_cameras || 1,
            system_status: data.system_status || "stable"
          });
        }
      } catch (e) {
        console.error("Failed to fetch stats", e);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard animate-fade-in">
      <header className="dash-header">
        <h2 className="section-title">Operational Dashboard</h2>
        <p className="subtitle">Real-time compliance monitoring and threat detection.</p>
      </header>

      <div className="stats-grid">
        <div className="stat-card glass-card">
          <span className="stat-label">Total Detections</span>
          <span className="stat-value">{stats.total_detections}</span>
          <div className="stat-trend trend-up">↑ 12% from last hour</div>
        </div>
        <div className="stat-card glass-card">
          <span className="stat-label">Compliance Rate</span>
          <span className="stat-value gradient-text">{stats.compliance_rate}</span>
          <div className="progress-bar"><div className="progress" style={{width: stats.compliance_rate}}></div></div>
        </div>
        <div className="stat-card glass-card">
          <span className="stat-label">Violations</span>
          <span className="stat-value text-danger">{stats.violations}</span>
          <div className="stat-trend text-danger">Alert: Action Required</div>
        </div>
        <div className="stat-card glass-card">
          <span className="stat-label">Active Nodes</span>
          <span className="stat-value">{stats.active_cameras}</span>
          <div className="stat-trend text-success">All systems healthy</div>
        </div>
      </div>

      <div className="monitoring-area">
        <div className="video-feed-container glass-card">
          <div className="feed-header">
            <h3>Camera Feed: Entrance_West_01</h3>
            <span className="feed-meta">HD • 30FPS • AI ACTIVE</span>
          </div>
          <div className="video-placeholder">
             <div className="scan-line"></div>
             <p>AWAITING LIVE STREAM CONNECTION</p>
          </div>
        </div>

        <div className="recent-activity glass-card">
           <div className="feed-header">
            <h3>Security Log</h3>
          </div>
          <div className="log-entries">
             <div className="log-entry">
                <span className="log-time">23:45:12</span>
                <span className="log-msg">Person detected: SHADOW (Compliant)</span>
             </div>
             <div className="log-entry log-warning">
                <span className="log-time">23:42:05</span>
                <span className="log-msg">VIOLATION: Unknown Person (No ID)</span>
             </div>
             <div className="log-entry">
                <span className="log-time">23:40:55</span>
                <span className="log-msg">System calibration check: PASS</span>
             </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .dash-header {
          margin-bottom: 2rem;
        }
        .section-title {
          font-size: 2rem;
          font-weight: 800;
        }
        .subtitle {
          opacity: 0.6;
          font-size: 1rem;
        }
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
          gap: 1.5rem;
          margin-bottom: 3rem;
        }
        .stat-card {
          padding: 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }
        .stat-label {
          font-size: 0.85rem;
          font-weight: 600;
          opacity: 0.5;
          text-transform: uppercase;
          letter-spacing: 1px;
        }
        .stat-value {
          font-size: 2.5rem;
          font-weight: 800;
        }
        .stat-trend {
          font-size: 0.75rem;
          font-weight: 600;
        }
        .text-danger { color: var(--danger); }
        .text-success { color: var(--success); }
        .progress-bar {
          height: 4px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 2px;
          margin-top: 0.5rem;
        }
        .progress {
          height: 100%;
          background: var(--primary);
          border-radius: 2px;
        }
        .monitoring-area {
          display: grid;
          grid-template-columns: 2fr 1fr;
          gap: 1.5rem;
        }
        .feed-header {
          padding: 1.25rem;
          border-bottom: 1px solid var(--glass-border);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .feed-meta {
          font-size: 0.7rem;
          font-weight: 800;
          opacity: 0.4;
        }
        .video-placeholder {
          aspect-ratio: 16/9;
          background: #000;
          display: flex;
          align-items: center;
          justify-content: center;
          position: relative;
          overflow: hidden;
          color: rgba(255, 255, 255, 0.2);
          font-weight: 700;
          letter-spacing: 2px;
        }
        .scan-line {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 2px;
          background: rgba(79, 70, 229, 0.2);
          animation: scan 4s linear infinite;
        }
        @keyframes scan {
          0% { top: 0; }
          100% { top: 100%; }
        }
        .log-entries {
          padding: 1rem;
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }
        .log-entry {
          font-size: 0.85rem;
          display: flex;
          gap: 1rem;
          padding: 0.5rem;
          border-radius: 6px;
          transition: background 0.2s;
        }
        .log-entry:hover { background: rgba(255, 255, 255, 0.03); }
        .log-time { opacity: 0.4; font-family: monospace; }
        .log-warning { color: var(--warning); background: rgba(245, 158, 11, 0.05); }
      `}</style>
    </div>
  );
}
