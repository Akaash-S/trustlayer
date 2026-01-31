# Deploying TrustLayer AI to Google Cloud Compute Engine

Yes, using **Compute Engine** is a great, flexible way to host this. Since we have a VPC, we can ensure the VM is secured.

## Option 1: Container-Optimized OS (Recommended)
This is the easiest way. You tell GCP to run a Docker container on the VM.

### 1. Build & Push Image
First, you need to put your code in a container.
(Run these commands in your local terminal or Cloud Shell)

```bash
# Set your Project ID
export PROJECT_ID="your-gcp-project-id"

# 1. Enable Artifact Registry
gcloud services enable artifactregistry.googleapis.com

# 2. Create a repository
gcloud artifacts repositories create trustlayer-repo \
    --repository-format=docker \
    --location=us-central1 \
    --description="TrustLayer AI Repository"

# 3. Build and Push (using Google Cloud Build is easiest)
gcloud builds submit --tag us-central1-docker.pkg.dev/$PROJECT_ID/trustlayer-repo/trustlayer:v1 .
```

### 2. Create the VM
Now create the VM that pulls this image.

```bash
gcloud compute instances create-with-container trustlayer-vm \
    --project=$PROJECT_ID \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --container-image=us-central1-docker.pkg.dev/$PROJECT_ID/trustlayer-repo/trustlayer:v1 \
    --tags=http-server,https-server,trustlayer-allow \
    --network-interface=network-tier=PREMIUM,subnet=default
```

### 3. Open Firewall Ports
By default, custom ports (8000, 8501) are blocked. You must allow them.

```bash
gcloud compute firewall-rules create allow-trustlayer \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:8000,tcp:8501 \
    --source-ranges=0.0.0.0/0 \
    --target-tags=trustlayer-allow
```

*Note: In a real VPC production environment, change `0.0.0.0/0` to your specific corporate IP range or VPN cidr.*

---

## Option 2: Standard VM (Ubuntu/Debian)
If you just want a raw Linux VM and run manually:

1.  **Create VM**: Go to Console -> Compute Engine -> Create Instance (Ubuntu 22.04 LTS).
2.  **SSH into VM**:
    ```bash
    gcloud compute ssh trustlayer-vm
    ```
3.  **Install Deps**:
    ```bash
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-venv openjdk-17-jre-headless git
    ```
4.  **Clone & Run**:
    ```bash
    git clone https://github.com/Akaash-S/trustlayer.git
    cd trustlayer
    pip install -r requirements.txt
    python -m spacy download en_core_web_lg
    
    # Run in background (simple nohup example)
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    nohup streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 &
    ```
