# GCP Cost Estimate for Lottery System

Good news: **This system will likely cost you $0.00 per month** (Free) or just a few cents, provided you stay within the Google Cloud Free Tier limits.

Here is the detailed breakdown based on the proposed architecture.

## 1. Cloud Run Jobs (Compute)
*Runs your Python scripts (Prediction & Optimization).*

*   **Usage:**
    *   **Frequency:** 2 runs per week (8 runs/month).
    *   **Duration:** ~5-10 minutes per run (generous estimate).
    *   **Total:** ~80 minutes (4,800 seconds) per month.
    *   **Specs:** 1 vCPU, 2GB RAM.
*   **Free Tier Limit:**
    *   First 180,000 vCPU-seconds per month (you need ~4,800).
    *   First 360,000 GiB-seconds of memory (you need ~9,600).
*   **Estimated Cost:** **$0.00**

## 2. Cloud Storage (GCS)
*Stores your strategy files, history CSVs, and predictions.*

*   **Usage:**
    *   **Size:** Less than 100 MB (text files are small).
    *   **Operations:** A few reads/writes per week.
*   **Free Tier Limit:**
    *   5 GB of Standard Storage (US regions).
    *   5,000 Class A Operations (writes).
    *   50,000 Class B Operations (reads).
*   **Estimated Cost:** **$0.00**

## 3. Cloud Scheduler
*Triggers the jobs automatically.*

*   **Usage:** 2 jobs defined (Prediction Schedule, Optimization Schedule).
*   **Free Tier Limit:** 3 free jobs per billing account.
*   **Estimated Cost:** **$0.00**

## 4. Artifact Registry
*Stores your Docker container image.*

*   **Usage:** One Docker image containing Python + TensorFlow.
    *   Size: ~500MB - 1GB (depending on base image).
*   **Free Tier Limit:** 0.5 GB storage per month.
*   **Potential Cost:**
    *   If your image is > 0.5 GB, you pay ~$0.10 per GB/month.
    *   **Estimated:** **$0.00 - $0.10 per month**.

## 5. Cloud Build
*Builds your Docker image (only happens when you update code).*

*   **Usage:** Building the image takes ~2-3 minutes.
*   **Free Tier Limit:** 120 build-minutes per day.
*   **Estimated Cost:** **$0.00**

---

## 💰 Total Estimated Monthly Bill: $0.00 - $0.10

### ⚠️ Important Requirements for Free Tier
To ensure you stay in the free tier:
1.  **Region:** Use **`us-central1`**, `us-west1`, or `us-east1`. (Other regions may not have free tier).
2.  **Clean Up:** If you deploy multiple versions of your Docker image, delete old ones in Artifact Registry to save space.
3.  **Budget Alert:** Set up a GCP Budget Alert for $1.00. Google will email you if you ever cross this threshold, preventing surprise bills.

### Alternative: "Always Free" VM
If you prefer a Virtual Machine (Compute Engine) over Cloud Run:
*   **Instance Type:** `e2-micro`
*   **Region:** `us-central1`, `us-west1`, or `us-east1`.
*   **Cost:** Free (1 instance per month).
*   **Pros:** Simpler to debug (you can SSH in).
*   **Cons:** You have to manage the OS updates yourself.

**Recommendation:** Stick with **Cloud Run Jobs** (the architecture I designed). It's maintenance-free and fits easily into the free tier for this workload.
