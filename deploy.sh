#!/bin/bash
set -e

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT}
REGION="us-central1"
SERVICE_NAME="pii-vault"

if [ -z "$PROJECT_ID" ]; then
  echo "Error: GOOGLE_CLOUD_PROJECT env var is not set."
  echo "Run 'gcloud config set project [YOUR_PROJECT_ID]' or export GOOGLE_CLOUD_PROJECT=[YOUR_PROJECT_ID]"
  exit 1
fi

echo "=================================================="
echo "Deploying to Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "=================================================="

# 1. Enable APIs
echo "[1/5] Enabling required APIs..."
gcloud services enable run.googleapis.com \
    storage.googleapis.com \
    dlp.googleapis.com \
    aiplatform.googleapis.com \
    artifactregistry.googleapis.com

# 2. Create Buckets
QUARANTINE_BUCKET="${PROJECT_ID}-quarantine"
VAULT_BUCKET="${PROJECT_ID}-vault"

echo "[2/5] Ensuring GCS Buckets exist..."
if ! gsutil ls "gs://$QUARANTINE_BUCKET" &>/dev/null; then
  gsutil mb -l $REGION "gs://$QUARANTINE_BUCKET"
  # Set lifecycle to delete after 1 hour (as per spec)
  echo '{"rule": [{"action": {"type": "Delete"}, "condition": {"age": 1}}]}' > lifecycle.json
  gsutil lifecycle set lifecycle.json "gs://$QUARANTINE_BUCKET"
  rm lifecycle.json
else
  echo "Bucket $QUARANTINE_BUCKET already exists."
fi

if ! gsutil ls "gs://$VAULT_BUCKET" &>/dev/null; then
  gsutil mb -l $REGION "gs://$VAULT_BUCKET"
  # Secure bucket (no public access)
  gcloud storage buckets update "gs://$VAULT_BUCKET" --public-access-prevention
else
  echo "Bucket $VAULT_BUCKET already exists."
fi

# 3. IAM Permissions (Least Privilege)
echo "[3/5] Setting up IAM permissions..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
# Cloud Run uses the default Compute Engine service account by default
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo "Granting roles to $SERVICE_ACCOUNT..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/storage.objectAdmin" --condition=None --quiet > /dev/null

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/dlp.user" --condition=None --quiet > /dev/null

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/aiplatform.user" --condition=None --quiet > /dev/null

# 4. Build Frontend
echo "[4/5] Building Frontend..."
cd frontend
npm install
npm run build
cd ..

# 5. Prepare Backend
echo "[5/6] Preparing Backend assets..."
rm -rf backend/app/static
mkdir -p backend/app/static
cp -r frontend/dist/* backend/app/static/

# 6. Deploy to Cloud Run
echo "[6/6] Deploying to Cloud Run..."
cd backend

# Note: We are using local SQLite for the demo to avoid Cloud SQL setup time.
# In prod, set DATABASE_URL to your Cloud SQL instance.
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="PROJECT_ID=$PROJECT_ID,QUARANTINE_BUCKET=$QUARANTINE_BUCKET,VAULT_BUCKET=$VAULT_BUCKET,REGION=$REGION,USE_MOCK_GCP=False,DATABASE_URL=sqlite:///./prod.db"

echo "=================================================="
echo "Deployment Complete!"
echo "Service URL: $(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')"
echo "=================================================="
