
#!/bin/bash

# AWS deployment script for AI Assistant

set -e

# Configuration
AWS_REGION="us-east-1"
CLUSTER_NAME="ai-assistant-cluster"
SERVICE_NAME="ai-assistant"

echo "🚀 Starting AWS deployment..."

# Create ECS cluster
echo "🏗️ Creating ECS cluster..."
aws ecs create-cluster --cluster-name $CLUSTER_NAME

# Build and push images to ECR
echo "🐳 Building and pushing images..."
aws ecr create-repository --repository-name api-gateway --region $AWS_REGION || true
aws ecr create-repository --repository-name admin-panel --region $AWS_REGION || true
aws ecr create-repository --repository-name source-management --region $AWS_REGION || true
aws ecr create-repository --repository-name conversation --region $AWS_REGION || true

# Get ECR login token
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push images
docker build -t $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/api-gateway:latest ./api_gateway
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/api-gateway:latest

docker build -t $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/admin-panel:latest ./admin_panel
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/admin-panel:latest

docker build -t $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/source-management:latest ./source_management
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/source-management:latest

docker build -t $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/conversation:latest ./conversation
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/conversation:latest

echo "✅ AWS deployment completed!"
