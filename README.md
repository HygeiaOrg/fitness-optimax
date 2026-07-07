# 🏋️‍♂️ Fitness OptiMax

**Fitness OptiMax** is a premium, data-driven workout application that uses Statistical Process Control (SPC) to track and optimize athletic performance. 

By analyzing historical workout data, Fitness OptiMax mathematically identifies whether your progressive overload is effectively driving adaptation (momentum signals, golden crosses) or if you are stagnating (plateaus).

The application is themed around the Washington Commanders design language (burgundy, gold, and sleek dark mode).

---

## 🏗 Architecture

The system is built on a 3-tier architecture:

1. **Frontend**: React + Vite single-page application.
   - Built with pure CSS (`index.css`, `App.css`) and responsive components.
   - Visualizations powered by Apache ECharts.
2. **Backend**: FastAPI (Python).
   - Serves the unified API layer (`/api/targets`, `/api/charts`, `/api/goals`, `/api/workouts`).
   - Dynamically mounts and serves the compiled React frontend for unified deployment.
3. **Database**: Google BigQuery.
   - A multi-layered SQL pipeline containing views for metric calculation, SPC control limits (Zone A/B), and actionable alert generation.

---

## 🚀 Setup and Local Development

### 1. Database (BigQuery)
1. Ensure you have a Google Cloud project with BigQuery enabled and a Billing Account attached.
2. Create a dataset named `Optimmax`.
3. Run the deployment script to create the views and tables:
   ```bash
   python deploy_views.py
   ```

### 2. Backend (FastAPI)
1. Set up a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Start the local server:
   ```bash
   uvicorn api.main:app --reload
   ```

### 3. Frontend (React)
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   npm install
   ```
2. Start the Vite development server:
   ```bash
   npm run dev
   ```

---

## 🌐 Production Deployment (Google Cloud Run)

The application is containerized using Docker, serving both the React SPA and the FastAPI backend through a single unified container.

1. Submit the build to Cloud Run:
   ```bash
   gcloud run deploy fitness-optimax \
     --source . \
     --project gen-lang-client-0937519537 \
     --region europe-west2 \
     --allow-unauthenticated
   ```

*(Ensure your Cloud Run service account has the necessary IAM permissions to query BigQuery `roles/bigquery.dataViewer`, `roles/bigquery.dataEditor`, and `roles/bigquery.user`).*

---

## 📊 Features

- **Progressive Overload Targets**: Auto-generated next-workout targets (Sets, Reps, Weight) based on your rolling averages.
- **SPC I-Charts**: Beautiful, Interactive Statistical Process Control charts highlighting exactly when your performance breaks outside standard variation limits.
- **Native Data Entry**: Log your workouts directly from the mobile-responsive UI straight to BigQuery.
- **RPE Calibration**: Workouts are weighted by your Rate of Perceived Exertion.
