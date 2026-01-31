# ☁️ TrustLayer Cloud Deployment Guide (Cloud Shell Edition)

This guide is optimized for **Google Cloud Shell**. You don't need to install anything on your local computer initially.

## Architecture
*   **Code**: Git Repository
*   **Build**: Cloud Build (Serverless Docker Build)
*   **Run**: Compute Engine VM (Standard Ubuntu)
*   **Access**: IAP Tunnel (Secure connection from your laptop)

---

## Step 1: Open Cloud Shell
1.  Go to [console.cloud.google.com](https://console.cloud.google.com).
2.  Click the **Activate Cloud Shell** icon (>_) in the top right.
3.  Set your Project ID:
    ```bash
    export PROJECT_ID="trustlayer-ai-suite"  # CHANGE THIS to your actual Project ID
    gcloud config set project $PROJECT_ID
    ```

## Step 2: Get the Code
In Cloud Shell, clone your repository (or upload it).
```bash
git clone https://github.com/Akaash-S/trustlayer.git
cd trustlayer
```

## Step 3: Build & Push Container
We use Cloud Build to create the Docker image without using local disk space.

```bash
# Enable Services
gcloud services enable artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    compute.googleapis.com

# Create Repository (Run once)
gcloud artifacts repositories create trustlayer-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="TrustLayer Docker Repo"

# Configure Docker auth
gcloud auth configure-docker us-central1-docker.pkg.dev

# BUILD IT (This takes ~2 mins)
gcloud builds submit --tag us-central1-docker.pkg.dev/$PROJECT_ID/trustlayer-repo/trustlayer:v1 .
```

## Step 4: Create the VM
We create a VM that allows IAP tunneling (so we can connect securely).

```bash
# Create the VM
gcloud compute instances create trustlayer-vm \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --tags=trustlayer-allow-iap

# Create Firewall Rule (Allow IAP)
gcloud compute firewall-rules create allow-iap-tunnel \
    --direction=INGRESS \
    --action=ALLOW \
    --rules=tcp:22,tcp:8000,tcp:8080,tcp:8081,tcp:8501 \
    --source-ranges=35.235.240.0/20 \
    --target-tags=trustlayer-allow-iap
```

## Step 5: Run TrustLayer on the VM
Now we SSH into the VM and run the container.

```bash
# SSH into VM
gcloud compute ssh trustlayer-vm --zone=us-central1-a

# --- INSIDE THE VM ---

# Install Docker
sudo apt-get update && sudo apt-get install -y docker.io

# Pull & Run
export PROJECT_ID="trustlayer-ai-suite" # Set this again inside VM
gcloud auth configure-docker us-central1-docker.pkg.dev

sudo docker run -d --rm \
    --name trustlayer \
    -p 8000:8000 \
    -p 8080:8080 \
    -p 8081:8081 \
    -p 8501:8501 \
    us-central1-docker.pkg.dev/$PROJECT_ID/trustlayer-repo/trustlayer:v1

# View Logs (to verify startup)
sudo docker logs -f trustlayer
```

## Step 6: Connect from Your Laptop
Now, go back to **Your Local Computer Terminal** (PowerShell/CMD). You need `gcloud` installed locally for this part.

```bash
# 1. Login locally
gcloud auth login

# 2. Start the Tunnel (Forwarding Proxy Port 8080)
gcloud compute start-iap-tunnel trustlayer-vm 8080 \
    --local-host-port=localhost:8080 \
    --zone=us-central1-a \
    --project=$PROJECT_ID
```
*Keep this terminal open!*

## Step 7: Final Setup
1.  **Configure System Proxy**: Set your Windows/Browser proxy to `localhost:8080`.
2.  **Install Certificate**:
    *   Open `http://mitm.it` (It should load now!).
    *   Install the cert as usual.
3.  **Browse**: Go to ChatGPT.

**Done!** You are now using a Cloud-based AI Firewall.
