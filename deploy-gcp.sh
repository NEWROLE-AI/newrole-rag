
#!/bin/bash

# Google Cloud deployment script for AI Assistant

set -e

# Configuration
PROJECT_ID="your-gcp-project-id"
REGION="us-central1"
SERVICE_NAME="ai-assistant"

echo "🚀 Starting Google Cloud deployment..."

# Authenticate with Google Cloud (if not already done)
echo "📋 Checking Google Cloud authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Please authenticate with Google Cloud:"
    gcloud auth login
fi

# Set project
echo "🔧 Setting project: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔌 Enabling required Google Cloud APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable firebase.googleapis.com

# Create secrets
echo "🔐 Creating secrets..."
echo "Please create the following secrets in Google Cloud Secret Manager:"
echo "1. firebase-project-id"
echo "2. firebase-private-key"
echo "3. firebase-client-email"
echo "4. openai-api-key"
echo "5. database-url"

echo "Example commands:"
echo "gcloud secrets create firebase-project-id --data-file=<(echo 'your-project-id')"
echo "gcloud secrets create firebase-private-key --data-file=private-key.txt"
echo "gcloud secrets create firebase-client-email --data-file=<(echo 'your-email@project.iam.gserviceaccount.com')"

# Build and deploy API Gateway
echo "🏗️ Building and deploying API Gateway..."
gcloud builds submit ./api_gateway --tag gcr.io/$PROJECT_ID/api-gateway

gcloud run deploy api-gateway \
    --image gcr.io/$PROJECT_ID/api-gateway \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="ADMIN_PANEL_URL=https://admin-panel-service-url,SOURCE_MANAGEMENT_URL=https://source-management-service-url,CONVERSATION_URL=https://conversation-service-url" \
    --set-secrets="FIREBASE_PROJECT_ID=firebase-project-id:latest,FIREBASE_PRIVATE_KEY=firebase-private-key:latest,FIREBASE_CLIENT_EMAIL=firebase-client-email:latest"

# Build and deploy other services
echo "🏗️ Building and deploying Admin Panel..."
gcloud builds submit ./admin_panel --tag gcr.io/$PROJECT_ID/admin-panel
gcloud run deploy admin-panel \
    --image gcr.io/$PROJECT_ID/admin-panel \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-secrets="DATABASE_URL=database-url:latest"

echo "🏗️ Building and deploying Source Management..."
gcloud builds submit ./source_management --tag gcr.io/$PROJECT_ID/source-management
gcloud run deploy source-management \
    --image gcr.io/$PROJECT_ID/source-management \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-secrets="DATABASE_URL=database-url:latest"

echo "🏗️ Building and deploying Conversation..."
gcloud builds submit ./conversation --tag gcr.io/$PROJECT_ID/conversation
gcloud run deploy conversation \
    --image gcr.io/$PROJECT_ID/conversation \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-secrets="DATABASE_URL=database-url:latest,OPENAI_API_KEY=openai-api-key:latest"

echo "✅ Deployment completed!"
echo "🌐 Your services are now running on Google Cloud Run"
echo "📋 Get service URLs with: gcloud run services list"
