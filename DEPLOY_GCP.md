# Deploying TrustLayer AI to Google Cloud Compute Engine

## Phase 1: Build Image (Already Done)
*You have successfully built the image: `us-central1-docker.pkg.dev/trustlayer-ai-suite/trustlayer-repo/trustlayer:v1`*

---

## Phase 2: Deploy the Secure Gateway
We will create a VM that runs this image. To make it "unbypassable" and secure, we will **NOT** give it a public IP address (or we will blocking incoming traffic) and connect via **Google Identity-Aware Proxy (IAP)**. This simulates a secure corporate VPN.

### 1. Create the VM
Run this command in your Cloud Shell or Terminal:

```bash
# Set your Project ID
export PROJECT_ID="trustlayer-ai-suite"

# Create the VM (Container Optimized)
# We add 'no-address' to prevent public internet access if you have a Cloud NAT enabled.
# If you don't have Cloud NAT, remove '--no-address' but we will rely on IAP for access.
gcloud compute instances create-with-container trustlayer-vm \
    --project=$PROJECT_ID \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --container-image=us-central1-docker.pkg.dev/$PROJECT_ID/trustlayer-repo/trustlayer:v1 \
    --tags=trustlayer-secure \
    --network-interface=network-tier=PREMIUM,subnet=default \
    --metadata=google-logging-enabled=true
```

### 2. Configure Firewall for IAP
Allow Google's IAP range to reach your VM.

```bash
gcloud compute firewall-rules create allow-iap-tunnel \
    --direction=INGRESS \
    --action=ALLOW \
    --rules=tcp:8000,tcp:8501,tcp:22 \
    --source-ranges=35.235.240.0/20 \
    --target-tags=trustlayer-secure
```

---

## Phase 3: Connect Securely (The "VPN" Experience)
Now, instead of accessing a public URL (which anyone could attack), you will create a secure "tunnel" from your local laptop to the TrustLayer VPC.

### 1. Start the Secure Tunnel
Run this command on your **Local Machine**:

```bash
gcloud compute start-iap-tunnel trustlayer-vm 8000 \
    --local-host-port=localhost:8000 \
    --zone=us-central1-a \
    --project=$PROJECT_ID
```
*Keep this terminal window open!*

### 2. Verify Connection
Now, your **Localhost:8000** is magically forwarded to the **Cloud VM**.

1.  Open your browser to: [http://localhost:8000/docs](http://localhost:8000/docs)
2.  You are now securely connected to the VPC!

### 3. Connect the Dashboard (Optional)
Open a **second terminal** and create a tunnel for the dashboard:

```bash
gcloud compute start-iap-tunnel trustlayer-vm 8501 \
    --local-host-port=localhost:8501 \
    --zone=us-central1-a \
    --project=$PROJECT_ID
```
Now access dashboard at: [http://localhost:8501](http://localhost:8501)

---

## Phase 4: Enforce Usage (The "Unbypassable" Part)
To make this truly unbypassable in an enterprise setting, you would:
1.  **Block OpenAI**: On your corporate firewall, BLOCK `api.openai.com` for all employees.
2.  **Allow TrustLayer**: Only allow the `trustlayer-vm` (via its Service Account) to reach `api.openai.com`.
3.  **Result**: Employees *must* use your localhost tunnel (TrustLayer) to get answers. They cannot go direct.
