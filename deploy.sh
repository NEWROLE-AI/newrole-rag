#!/bin/bash

# Build and deploy all services to Kubernetes

set -e  # Exit on any error

echo "🚀 Starting deployment of AI Assistant services..."

# Function to check if docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to check if kubectl is available
check_kubectl() {
    if ! command -v kubectl > /dev/null 2>&1; then
        echo "❌ kubectl is not installed. Please install kubectl and try again."
        exit 1
    fi
}

# Check prerequisites
echo "🔍 Checking prerequisites..."
check_docker
check_kubectl

echo "📦 Building Docker images..."

# Build API Gateway
echo "Building API Gateway..."
docker build -f Dockerfile.api_gateway -t ai-assistant/api-gateway:latest . || {
    echo "❌ Failed to build API Gateway image"
    exit 1
}

# Build other services
echo "Building Admin Panel..."
docker build -t ai-assistant/admin-panel:latest ./admin_panel || {
    echo "❌ Failed to build Admin Panel image"
    exit 1
}

echo "Building Source Management..."
docker build -t ai-assistant/source-management:latest ./source_management || {
    echo "❌ Failed to build Source Management image"
    exit 1
}

echo "Building Conversation service..."
docker build -t ai-assistant/conversation:latest ./conversation || {
    echo "❌ Failed to build Conversation image"
    exit 1
}

echo "Building UI..."
docker build -t ai-assistant/ui:latest ./ui || {
    echo "❌ Failed to build UI image"
    exit 1
}

echo "☸️ Applying Kubernetes configurations..."

# Create namespace
echo "Creating namespace..."
kubectl apply -f k8s/namespace.yaml

# Apply secrets (make sure to update with actual values)
echo "⚠️  WARNING: Please update k8s/secrets.yaml with actual base64-encoded values before deploying to production!"
kubectl apply -f k8s/secrets.yaml

# Deploy services
echo "Deploying API Gateway..."
kubectl apply -f k8s/api-gateway-deployment.yaml

echo "Deploying Admin Panel..."
kubectl apply -f k8s/admin-panel-deployment.yaml

echo "Deploying Source Management..."
kubectl apply -f k8s/source-management-deployment.yaml

echo "Deploying Conversation service..."
kubectl apply -f k8s/conversation-deployment.yaml

echo "Deploying UI..."
kubectl apply -f k8s/ui-deployment.yaml

echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/api-gateway -n ai-assistant
kubectl wait --for=condition=available --timeout=300s deployment/admin-panel -n ai-assistant
kubectl wait --for=condition=available --timeout=300s deployment/source-management -n ai-assistant
kubectl wait --for=condition=available --timeout=300s deployment/conversation -n ai-assistant
kubectl wait --for=condition=available --timeout=300s deployment/ui -n ai-assistant

echo "✅ Deployment completed successfully!"
echo ""
echo "📊 Checking deployment status:"
kubectl get pods -n ai-assistant
echo ""
echo "🌐 Getting service URLs:"
kubectl get services -n ai-assistant
echo ""
echo "📝 To check logs, use:"
echo "kubectl logs -f deployment/api-gateway -n ai-assistant"
echo ""
echo "🔧 To update secrets with real values:"
echo "kubectl create secret generic firebase-config --from-literal=project-id='your-project-id' --from-literal=private-key='your-private-key' --from-literal=client-email='your-client-email' -n ai-assistant --dry-run=client -o yaml | kubectl apply -f -"