# Presentation Pose Tracking Assistant

A web-based application to help you practice and improve your presentation body language using real-time pose tracking powered by AI.

## Features

- **Full Body Pose Tracking:** Uses your device's webcam and AI (MediaPipe) to analyze your posture and body language in real time.
- **Presentation Feedback:** Instantly see feedback on your posture and body language while practicing.
- **Correctness Analysis:** Every 5 minutes, view a pie chart and stats showing the percentage of time you maintained correct vs. incorrect body language.
- **Session History:** Track your progress and total practice time across sessions.
- **Presentation Tips:** Helpful tips for effective body language during presentations.
- **Runs Anywhere:** Works on laptops and phones, no installation required for users.

## How It Works

- The app uses your webcam (with your permission) and runs pose detection in your browser.
- It checks for correct body language (upright posture, arms visible, head forward, etc.)
- Feedback and stats are displayed live as you practice.

## Quick Start (Local)

1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd pose-tracking
   ```
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
3. **Run the app:**
   ```sh
   uvicorn main:app --reload
   ```
4. **Open in your browser:**
   - Go to [http://localhost:8000](http://localhost:8000)

## Docker Usage

1. **Build the Docker image:**
   ```sh
   docker build -t pose-tracking-app .
   ```
2. **Run the container:**
   ```sh
   docker run -p 8000:8000 pose-tracking-app
   ```
3. **Open in your browser:**
   - Go to [http://localhost:8000](http://localhost:8000)

## Deployed on Google Cloud

## Technologies Used

- [FastAPI](https://fastapi.tiangolo.com/) (Python backend)
- [MediaPipe Pose](https://google.github.io/mediapipe/solutions/pose.html) (browser-based pose detection)
- [Chart.js](https://www.chartjs.org/) (pie chart visualization)
- [Docker](https://www.docker.com/) (containerization)
- [Google Cloud Run](https://cloud.google.com/run) (cloud deployment)

## Screenshots

![Live Feedback Example](docs/screenshot-live-feedback.png)
![Pie Chart Example](docs/screenshot-pie-chart.png)

## License

MIT License

---

**Practice your presentation. Improve your body language. Succeed with confidence!**
