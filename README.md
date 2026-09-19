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

---

## 🩺 Troubleshooting

### The dashboard says "Failed to load targets"

The API now explains itself instead of returning a bare `500`. Two endpoints tell you what broke:

| Endpoint | What it does |
| --- | --- |
| `/api/health` | Liveness only — never touches BigQuery. If this fails, the container is down. |
| `/api/diagnostics` | Probes every pipeline layer in order and names the **first** one that fails, with the real BigQuery message and a suggested fix. |

Open `https://<your-cloud-run-url>/api/diagnostics` first — `first_failure.layer` is the root cause; everything downstream of it fails for the same reason. Full tracebacks are in Cloud Run → Logs.

### Common causes

**`source_google_sheet` fails with "Permission denied while getting Drive credentials"**

Cloud Run's metadata server only ever issues `cloud-platform` tokens, and Drive is *not* covered by that scope — so asking `google.auth` for `drive.readonly` does not actually grant it. The service account has to impersonate itself to mint a Drive-scoped token (the API does this automatically once IAM allows it):

```bash
SA=$(gcloud run services describe fitness-optimax --region europe-west2 \
  --project gen-lang-client-0937519537 --format='value(spec.template.spec.serviceAccountName)')

# Let the service account mint Drive-scoped tokens for itself
gcloud iam service-accounts add-iam-policy-binding "$SA" \
  --member="serviceAccount:$SA" \
  --role="roles/iam.serviceAccountTokenCreator" \
  --project gen-lang-client-0937519537
```

Then share the source Google Sheet with `$SA` (Viewer is enough).

**A view is missing, or a query fails after a schema change** — redeploy the SQL layer:

```bash
python deploy_views.py
```

**A malformed row in the Google Sheet** — no longer fatal. `stg_workouts` parses every column with `SAFE.` casts and drops rows without a usable date, exercise group, or weight, so one bad row can no longer take the dashboard down.

### After changing any file in `sql/`

The views live in BigQuery, not in the container — a Cloud Run deploy does **not** update them. Run `python deploy_views.py` as well.
