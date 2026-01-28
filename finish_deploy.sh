#!/bin/bash
set -e
set -x

PROJECT_ID="profitscout-lx6bb"
REGION="us-central1"
DB_INSTANCE="pii-vault-db"
DB_NAME="pii_vault"
DB_USER="pii_user"
SECRET_NAME="PII_VAULT_DB_URL"
SERVICE_ACCOUNT="469352939749-compute@developer.gserviceaccount.com"

# 1. Reset Password & Get Connection String
echo "Resetting DB Password..."
DB_PASS=$(openssl rand -base64 12 | tr -dc 'a-zA-Z0-9')
gcloud sql users set-password $DB_USER --instance=$DB_INSTANCE --password=$DB_PASS

CONNECTION_NAME="${PROJECT_ID}:${REGION}:${DB_INSTANCE}"
DB_URL="postgresql://${DB_USER}:${DB_PASS}@/${DB_NAME}?host=/cloudsql/${CONNECTION_NAME}"

# 2. Create/Update Secret
echo "Handling Secret..."
if ! gcloud secrets describe $SECRET_NAME &>/dev/null; then
    echo -n "$DB_URL" | gcloud secrets create $SECRET_NAME --data-file=-
else
    echo -n "$DB_URL" | gcloud secrets versions add $SECRET_NAME --data-file=-
fi

# 3. Grant IAM
echo "Granting IAM..."
gcloud secrets add-iam-policy-binding $SECRET_NAME \
    --member=\"serviceAccount:${SERVICE_ACCOUNT}\" \
    --role=\"roles/secretmanager.secretAccessor\" --quiet

# 4. Deploy
echo "Deploying..."
cd backend
gcloud run deploy pii-vault \
    --source . \
    --region $REGION \
    --allow-unauthenticated \
    --add-cloudsql-instances="${CONNECTION_NAME}" \
    --set-secrets="DATABASE_URL=${SECRET_NAME}:latest" \
    --set-env-vars="PROJECT_ID=$PROJECT_ID,QUARANTINE_BUCKET=${PROJECT_ID}-quarantine,VAULT_BUCKET=${PROJECT_ID}-vault,REGION=$REGION,USE_MOCK_GCP=False,SERVICE_ACCOUNT_EMAIL=$SERVICE_ACCOUNT"
