#!/bin/bash
set -x

PROJECT_ID="profitscout-lx6bb"
REGION="us-central1"
DB_INSTANCE="pii-vault-db"
DB_NAME="pii_vault"
DB_USER="pii_user"
SECRET_NAME="PII_VAULT_DB_URL"
SERVICE_ACCOUNT="469352939749-compute@developer.gserviceaccount.com"

echo "Creating Cloud SQL instance..."
# gcloud sql instances create $DB_INSTANCE \
#     --database-version=POSTGRES_15 \
#     --tier=db-f1-micro \
#     --region=$REGION \
#     --root-password=temporary_root_pass || echo "Instance creation failed or already exists"

echo "Creating DB..."
gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE --quiet || echo "DB exists"

echo "Creating User..."
DB_PASS=$(openssl rand -base64 12 | tr -dc 'a-zA-Z0-9')
gcloud sql users create $DB_USER --instance=$DB_INSTANCE --password=$DB_PASS --quiet || echo "User exists"

echo "Creating Secret..."
CONNECTION_NAME="${PROJECT_ID}:${REGION}:${DB_INSTANCE}"
DB_URL="postgresql://${DB_USER}:${DB_PASS}@/${DB_NAME}?host=/cloudsql/${CONNECTION_NAME}"

if ! gcloud secrets describe $SECRET_NAME &>/dev/null; then
    echo -n "$DB_URL" | gcloud secrets create $SECRET_NAME --data-file=-
else
    echo "Updating secret..."
    echo -n "$DB_URL" | gcloud secrets versions add $SECRET_NAME --data-file=-
fi

echo "Granting permissions..."
gcloud secrets add-iam-policy-binding $SECRET_NAME \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/cloudsql.client" --condition=None --quiet

echo "DB Setup Complete!"
