
#!/bin/bash

# Build and deploy script for Kubernetes

echo "Building Docker images..."

# Build API Gateway
docker build -t ai-assistant/api-gateway:latest ./api_gateway

# Build Admin Panel
docker build -t ai-assistant/admin-panel:latest ./admin_panel

# Build Source Management
docker build -t ai-assistant/source-management:latest ./source_management

# Build Conversation Service
docker build -t ai-assistant/conversation:latest ./conversation

echo "Applying Kubernetes configurations..."

# Apply namespace
kubectl apply -f k8s/namespace.yaml

# Apply secrets (you need to fill these with actual values)
kubectl apply -f k8s/secrets.yaml

# Deploy services
kubectl apply -f k8s/api-gateway-deployment.yaml
kubectl apply -f k8s/admin-panel-deployment.yaml
kubectl apply -f k8s/source-management-deployment.yaml
kubectl apply -f k8s/conversation-deployment.yaml
kubectl apply -f k8s/ui-deployment.yaml

echo "Waiting for deployments to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/api-gateway -n ai-assistant
kubectl wait --for=condition=available --timeout=300s deployment/admin-panel -n ai-assistant
kubectl wait --for=condition=available --timeout=300s deployment/source-management -n ai-assistant
kubectl wait --for=condition=available --timeout=300s deployment/conversation -n ai-assistant
kubectl wait --for=condition=available --timeout=300s deployment/ui -n ai-assistant

echo "Getting service endpoints..."
kubectl get services -n ai-assistant

echo "Deployment complete!"
