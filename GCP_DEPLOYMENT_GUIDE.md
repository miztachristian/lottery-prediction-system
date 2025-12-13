# Hosting on Google Cloud Platform (GCP)

This guide explains how to host your automated lottery system on GCP using **Cloud Run Jobs** and **Cloud Storage**.

## Architecture

1.  **Cloud Storage (GCS):** Stores your "state" (`strategy_state.yaml`, `config.yaml`, history CSVs, and predictions). This acts as the persistent memory.
2.  **Cloud Run Jobs:** Runs your Python scripts in a serverless container.
    *   **Job 1 (Friday):** Runs `production_app_v2.py` (Prediction).
    *   **Job 2 (Sunday):** Runs `auto_optimizer.py` (Analysis & Learning).
3.  **Cloud Scheduler:** Triggers the jobs automatically.

## Prerequisites

1.  GCP Account & Project.
2.  `gcloud` CLI installed.
3.  Docker installed.

## Step 1: Setup Cloud Storage

1.  Create a bucket (e.g., `lotto-bot-data`).
2.  Upload your initial files to the root of the bucket:
    *   `config.yaml`
    *   `strategy_state.yaml`
    *   `nl_lotto_xl_history.csv`

## Step 2: Build & Push Docker Image

1.  Enable Artifact Registry API.
2.  Create a repository (e.g., `lotto-repo`).

```bash
# Authenticate
gcloud auth login
gcloud auth configure-docker region-docker.pkg.dev

# Build
docker build -t region-docker.pkg.dev/PROJECT_ID/lotto-repo/lotto-bot:v1 .

# Push
docker push region-docker.pkg.dev/PROJECT_ID/lotto-repo/lotto-bot:v1
```

## Step 3: Create Cloud Run Jobs

We use `gcp_wrapper.py` to handle the file syncing.

### Job 1: Prediction (Friday)

```bash
gcloud run jobs create lotto-prediction \
  --image region-docker.pkg.dev/PROJECT_ID/lotto-repo/lotto-bot:v1 \
  --command python \
  --args gcp_wrapper.py,production_app_v2.py \
  --set-env-vars GCS_BUCKET_NAME=lotto-bot-data \
  --region us-central1
```

### Job 2: Optimization (Sunday)

```bash
gcloud run jobs create lotto-optimizer \
  --image region-docker.pkg.dev/PROJECT_ID/lotto-repo/lotto-bot:v1 \
  --command python \
  --args gcp_wrapper.py,auto_optimizer.py \
  --set-env-vars GCS_BUCKET_NAME=lotto-bot-data \
  --region us-central1
```

## Step 4: Schedule the Jobs

### Schedule Prediction (e.g., Friday at 18:00)

```bash
gcloud scheduler jobs create http lotto-pred-schedule \
  --location us-central1 \
  --schedule "0 18 * * 5" \
  --uri "https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/PROJECT_ID/jobs/lotto-prediction:run" \
  --http-method POST \
  --oauth-service-account-email PROJECT_NUMBER-compute@developer.gserviceaccount.com
```

### Schedule Optimization (e.g., Sunday at 20:00)

```bash
gcloud scheduler jobs create http lotto-opt-schedule \
  --location us-central1 \
  --schedule "0 20 * * 0" \
  --uri "https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/PROJECT_ID/jobs/lotto-optimizer:run" \
  --http-method POST \
  --oauth-service-account-email PROJECT_NUMBER-compute@developer.gserviceaccount.com
```

## How it Works

1.  **Friday 6PM:** Scheduler triggers `lotto-prediction`.
2.  Container starts. `gcp_wrapper.py` downloads `strategy_state.yaml` from GCS.
3.  `production_app_v2.py` runs, generates tickets, sends email.
4.  `gcp_wrapper.py` uploads the new `predictions/` folder to GCS.
5.  **Sunday 8PM:** Scheduler triggers `lotto-optimizer`.
6.  Container starts. Wrapper downloads state.
7.  `auto_optimizer.py` fetches latest results, runs post-mortem, updates `strategy_state.yaml`.
8.  Wrapper uploads the *updated* `strategy_state.yaml` back to GCS.
9.  **Next Friday:** The cycle repeats with the *new* strategy.

## Alternative: Compute Engine (VM)

If Cloud Run is too complex, you can create a small "e2-micro" VM (often free tier).

1.  Create VM.
2.  SSH into VM.
3.  Clone your code.
4.  Setup cron jobs (`crontab -e`):
    ```bash
    0 18 * * 5 cd /app && python3 production_app_v2.py
    0 20 * * 0 cd /app && python3 auto_optimizer.py
    ```
5.  This is simpler but requires managing the VM.
