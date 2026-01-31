# Deploying TrustLayer AI to Google Cloud

The connection error `4003: failed to connect to backend` usually means the application inside the VM crashed or isn't started yet.

To fix this and give you full control, we will use the **"Manual Execution on VM"** method. This allows you to see the logs directly and ensure everything is working before connecting.

## Phase 1: Create a Standard VM
Instead of a container-VM, we will create a standard Linux VM where we have full shell access.

```bash
export PROJECT_ID="trustlayer-ai-suite"

# 1. Create the VM (Standard Ubuntu)
gcloud compute instances create trustlayer-manual-vm \
    --project=$PROJECT_ID \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --tags=trustlayer-secure \
    --metadata=enable-oslogin=TRUE
```

## Phase 2: Open Firewall for IAP
Allow yourself to tunnel into it.
```bash
gcloud compute firewall-rules create allow-iap-tunnel \
    --direction=INGRESS \
    --action=ALLOW \
    --rules=tcp:8000,tcp:8501,tcp:22 \
    --source-ranges=35.235.240.0/20 \
    --target-tags=trustlayer-secure
```

## Phase 3: Setup & Run (Inside the VM)
Now we go inside the VM and run the code manually. This way you see errors immediately.

### 1. SSH into the VM
```bash
gcloud compute ssh trustlayer-manual-vm --zone=us-central1-a
```

### 2. Install Dependencies (Run these inside the VM)
```bash
# Update and Install Docker
sudo apt-get update
sudo apt-get install -y docker.io git

# Clone your code (or pull your docker image)
# Option A: Pull the image you already built (EASIEST)
gcloud auth configure-docker us-central1-docker.pkg.dev
sudo docker pull us-central1-docker.pkg.dev/trustlayer-ai-suite/trustlayer-repo/trustlayer:v1

# Option B: Run it! (Interactive Mode to see logs)
sudo docker run --rm -it \
    -p 8000:8000 \
    -p 8501:8501 \
    --name trustlayer-running \
    us-central1-docker.pkg.dev/trustlayer-ai-suite/trustlayer-repo/trustlayer:v1
```
*Wait until you see "Uvicorn running on http://0.0.0.0:8000"*

## Phase 4: Connect from Local Machine
**Leave the VM terminal open** (so the app keeps running).
Open a **NEW terminal** on your laptop and run the tunnel:

```bash
gcloud compute start-iap-tunnel trustlayer-manual-vm 8000 \
    --local-host-port=localhost:8000 \
    --zone=us-central1-a \
    --project=$PROJECT_ID
```

Now try opening [http://localhost:8000/docs](http://localhost:8000/docs).

## Debugging Tips
- If `docker run` fails, you will see exactly why (e.g., "Address already in use" or "Java not found").
- If the tunnel still fails, ensure your VM's internal firewall (`ufw`) isn't blocking ports, though on GCP Ubuntu images it usually allows internal traffic.
