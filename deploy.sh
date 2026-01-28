#!/bin/bash
set -e
set -x

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
# gcloud services enable run.googleapis.com \
#     storage.googleapis.com \
#     dlp.googleapis.com \
#     aiplatform.googleapis.com \
#     sqladmin.googleapis.com \
#     secretmanager.googleapis.com \
#     artifactregistry.googleapis.com

# 2. Create Buckets
QUARANTINE_BUCKET="${PROJECT_ID}-quarantine"
VAULT_BUCKET="${PROJECT_ID}-vault"

# echo "[2/5] Ensuring GCS Buckets exist..."
# if ! gsutil ls "gs://$QUARANTINE_BUCKET" &>/dev/null; then
#   gsutil mb -l $REGION "gs://$QUARANTINE_BUCKET"
#   # Set lifecycle to delete after 1 hour (as per spec)
#   echo '{"rule": [{"action": {"type": "Delete"}, "condition": {"age": 1}}]}' > lifecycle.json
#   gsutil lifecycle set lifecycle.json "gs://$QUARANTINE_BUCKET"
#   rm lifecycle.json
# else
#   echo "Bucket $QUARANTINE_BUCKET already exists."
# fi

# if ! gsutil ls "gs://$VAULT_BUCKET" &>/dev/null; then
#   gsutil mb -l $REGION "gs://$VAULT_BUCKET"
#   # Secure bucket (no public access)
#   gcloud storage buckets update "gs://$VAULT_BUCKET" --public-access-prevention
# else
#   echo "Bucket $VAULT_BUCKET already exists."
# fi

# 3. IAM Permissions (Least Privilege)
echo "[3/5] Setting up IAM permissions..."
# PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
PROJECT_NUMBER="469352939749"
# Cloud Run uses the default Compute Engine service account by default
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# echo "Granting roles to $SERVICE_ACCOUNT..."
# gcloud projects add-iam-policy-binding $PROJECT_ID \
#     --member="serviceAccount:${SERVICE_ACCOUNT}" \
#     --role="roles/storage.objectAdmin" --condition=None --quiet > /dev/null

# gcloud projects add-iam-policy-binding $PROJECT_ID \
#     --member="serviceAccount:${SERVICE_ACCOUNT}" \
#     --role="roles/dlp.user" --condition=None --quiet > /dev/null

# gcloud projects add-iam-policy-binding $PROJECT_ID \
#     --member="serviceAccount:${SERVICE_ACCOUNT}" \
#     --role="roles/aiplatform.user" --condition=None --quiet > /dev/null

# gcloud projects add-iam-policy-binding $PROJECT_ID \
#     --member="serviceAccount:${SERVICE_ACCOUNT}" \
#     --role="roles/iam.serviceAccountTokenCreator" --condition=None --quiet > /dev/null

# 3.5. Setup Cloud SQL & Secrets
echo "[3.5/5] Setting up Cloud SQL & Secrets..."
DB_INSTANCE="pii-vault-db"
DB_NAME="pii_vault"
DB_USER="pii_user"
SECRET_NAME="PII_VAULT_DB_URL"

# Check if instance exists
if ! gcloud sql instances describe $DB_INSTANCE &>/dev/null; then
    echo "Creating Cloud SQL instance (this takes ~10-15 mins)..."
    gcloud sql instances create $DB_INSTANCE \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --root-password=temporary_root_pass
else
    echo "Cloud SQL instance $DB_INSTANCE already exists."
fi

# Create DB and User
# (Ignoring errors if they exist)
gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE --quiet || true
# Generate random password
DB_PASS=$(openssl rand -base64 12 | tr -dc 'a-zA-Z0-9')
gcloud sql users create $DB_USER --instance=$DB_INSTANCE --password=$DB_PASS --quiet || true

# Construct Connection String
# Cloud Run Unix Socket format: postgresql://USER:PASS@/DB_NAME?host=/cloudsql/PROJECT:REGION:INSTANCE
CONNECTION_NAME="${PROJECT_ID}:${REGION}:${DB_INSTANCE}"
DB_URL="postgresql://${DB_USER}:${DB_PASS}@/${DB_NAME}?host=/cloudsql/${CONNECTION_NAME}"

# Store in Secret Manager
if ! gcloud secrets describe $SECRET_NAME &>/dev/null; then
    echo -n "$DB_URL" | gcloud secrets create $SECRET_NAME --data-file=-
else
    echo "Updating secret $SECRET_NAME..."
    echo -n "$DB_URL" | gcloud secrets versions add $SECRET_NAME --data-file=-
fi

# Grant Access to Secret
gcloud secrets add-iam-policy-binding $SECRET_NAME \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" --quiet > /dev/null

# Grant Cloud SQL Client role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/cloudsql.client" --condition=None --quiet > /dev/null


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
    --add-cloudsql-instances="${PROJECT_ID}:${REGION}:${DB_INSTANCE}" \
    --set-secrets="DATABASE_URL=${SECRET_NAME}:latest" \
    --set-env-vars="PROJECT_ID=$PROJECT_ID,QUARANTINE_BUCKET=$QUARANTINE_BUCKET,VAULT_BUCKET=$VAULT_BUCKET,REGION=$REGION,USE_MOCK_GCP=False,SERVICE_ACCOUNT_EMAIL=$SERVICE_ACCOUNT"

echo "=================================================="
echo "Deployment Complete!"
echo "Service URL: $(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')"
echo "=================================================="
