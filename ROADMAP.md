# Project Roadmap & Recommendations

## 1. Flutter vs. Next.js: The Verdict

**Stick with Flutter.**

*   **Why?** Your application is primarily a **"Kiosk" or "Utility" app** intended to run on a specific machine (like a security desk or entrance gate). Flutter behaves like a native desktop app, giving you better control over windowing, hardware (cameras), and performance without browser limitations.
*   **When to use Next.js?** Only if you need a "Management Dashboard" that the Principal or Admins verify from *their own laptops* via a web browser. But even then, you can just build a logical Flutter Web build.
*   **Recommendation:** Don't rewrite. The cost is too high. Polish the Flutter app to perfection.

## 2. "Wow" Features to Add

To make the project really impress ("Wow factor"):

### A. Real-Time "Live Feed" Dashboard
*   **Feature:** Instead of just uploading videos, have a "Live Camera" mode.
*   **Visuals:** Draw bounding boxes *live* on the screen in Flutter. Green box for valid, Red box for violation.
*   **Tech:** Stream MJPEG from Python to Flutter, or send coordinates via WebSocket.

### B. Voice Announcements (TTS)
*   **Feature:** When a violation is detected, the computer speaks: *"Warning: ID Card not detected for [Name]."*
*   **Why:** It makes the system feel "active" and intelligent.

### C. Automated Email/WhatsApp Alerts
*   **Feature:** If a specific person (e.g., a repeat offender) is detected, send an email to the admin automatically.
*   **Tech:** Simple Python `smtplib` or Twilio integration in `server.py`.

### D. Analytics Charts
*   **Feature:** A beautiful line chart showing "Violations per Hour" or a Pie Chart of "Compliance Rate".
*   **UI:** Use `fl_chart` in Flutter. It looks very professional.

## 3. Improvements & Bug Fixes

### A. Performance (Critical)
*   **Issue:** The `analyze_video` function in Python is "CPU-bound". Even though it says `async`, it blocks the server while processing. If two people upload videos, the server might freeze.
*   **Fix:** Use `FastAPI BackgroundTasks` or run the processing in a separate thread/process using `asyncio.to_thread`.

### B. Database Robustness
*   **Issue:** SQLite is great for dev, but can lock if multiple writes happen (e.g., tracking + uploading + analyzing).
*   **Fix:** Switch to **PostgreSQL** (easy change with SQLModel) or optimize SQLite usage.

### C. UI Polish
*   **Glassmorphism:** You have some, but make it consistent. Ensure all lists (Violations) have the same glass effect.
*   **Hero Animations:** When clicking a violation image to view full screen, animate it expanding (Hero widget in Flutter).

## 4. Immediate Next Steps (Proposed)

1.  **Refactor Backend:** Move the heavy video processing to a background thread so the UI doesn't freeze or timeout.
2.  **Visual Polish:** Add `fl_chart` for a "Compliance Statistics" dashboard widget.
3.  **Live Mode:** Prototype a basic Real-Time detection stream.
