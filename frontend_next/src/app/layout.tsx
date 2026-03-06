import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "ID Guard | ID Card Compliance System",
  description: "Advanced real-time ID card detection and compliance monitoring.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <nav className="navbar glass-card">
          <div className="container nav-content">
            <h1 className="logo gradient-text">ID GUARD 3.0</h1>
            <ul className="nav-links">
              <li><a href="/">Dashboard</a></li>
              <li><a href="/violations">History</a></li>
              <li><a href="/video-upload">Video Analysis</a></li>
            </ul>
            <div className="status-badge">
              <span className="pulse"></span> LIVE
            </div>
          </div>
        </nav>
        <main className="container main-content">
          {children}
        </main>
        <style dangerouslySetInnerHTML={{ __html: `
          .navbar {
            position: sticky;
            top: 1rem;
            margin: 1rem 2rem;
            padding: 1rem 2rem;
            z-index: 1000;
          }
          .nav-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
          }
          .logo {
            font-size: 1.5rem;
            font-weight: 800;
            letter-spacing: -1px;
          }
          .nav-links {
            display: flex;
            gap: 2rem;
            list-style: none;
          }
          .nav-links a {
            font-size: 0.95rem;
            font-weight: 500;
            opacity: 0.7;
            transition: all 0.2s;
          }
          .nav-links a:hover {
            opacity: 1;
            color: var(--primary);
          }
          .status-badge {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.75rem;
            font-weight: 700;
            background: rgba(16, 185, 129, 0.1);
            color: var(--success);
            padding: 0.35rem 0.75rem;
            border-radius: 20px;
            border: 1px solid rgba(16, 185, 129, 0.2);
          }
          .pulse {
            width: 8px;
            height: 8px;
            background: var(--success);
            border-radius: 50%;
            box-shadow: 0 0 0 rgba(16, 185, 129, 0.4);
            animation: pulse 2s infinite;
          }
          @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
            70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
            100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
          }
          .main-content {
            padding-top: 2rem;
            padding-bottom: 4rem;
          }
        `}} />
      </body>
    </html>
  );
}
