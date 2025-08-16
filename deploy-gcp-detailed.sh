
#!/bin/bash

# Подробный скрипт развертывания в Google Cloud

set -e

echo "🚀 Пошаговое развертывание AI Assistant в Google Cloud"

# Конфигурация
PROJECT_ID="${1:-your-gcp-project-id}"
REGION="${2:-us-central1}"

if [ "$PROJECT_ID" = "your-gcp-project-id" ]; then
    echo "❌ Пожалуйста, укажите PROJECT_ID:"
    echo "Usage: ./deploy-gcp-detailed.sh YOUR_PROJECT_ID [REGION]"
    exit 1
fi

echo "📋 Используем PROJECT_ID: $PROJECT_ID"
echo "📋 Используем REGION: $REGION"

# Шаг 1: Проверка аутентификации
echo "🔐 Шаг 1: Проверка аутентификации Google Cloud..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "Выполните аутентификацию:"
    gcloud auth login
fi

# Шаг 2: Установка проекта
echo "🔧 Шаг 2: Установка проекта..."
gcloud config set project $PROJECT_ID

# Шаг 3: Включение API
echo "🔌 Шаг 3: Включение необходимых API..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable firebase.googleapis.com

# Шаг 4: Создание базы данных
echo "🗄️ Шаг 4: Создание Cloud SQL PostgreSQL..."
DB_INSTANCE_NAME="ai-assistant-db"
DB_NAME="ai_assistant"
DB_USER="ai_user"
DB_PASSWORD=$(openssl rand -base64 32)

# Проверяем, существует ли уже инстанс
if ! gcloud sql instances describe $DB_INSTANCE_NAME --quiet &>/dev/null; then
    echo "Создаем Cloud SQL инстанс..."
    gcloud sql instances create $DB_INSTANCE_NAME \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --root-password=$DB_PASSWORD
    
    echo "Создаем базу данных..."
    gcloud sql databases create $DB_NAME --instance=$DB_INSTANCE_NAME
    
    echo "Создаем пользователя базы данных..."
    gcloud sql users create $DB_USER --instance=$DB_INSTANCE_NAME --password=$DB_PASSWORD
else
    echo "Cloud SQL инстанс уже существует"
fi

# Получаем connection name для базы данных
CONNECTION_NAME=$(gcloud sql instances describe $DB_INSTANCE_NAME --format="value(connectionName)")
DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@/$DB_NAME?host=/cloudsql/$CONNECTION_NAME"

# Шаг 5: Создание секретов
echo "🔐 Шаг 5: Создание секретов..."

# Database URL
echo -n "$DATABASE_URL" | gcloud secrets create database-url --data-file=- || \
    echo -n "$DATABASE_URL" | gcloud secrets versions add database-url --data-file=-

echo ""
echo "⚠️  ВАЖНО: Настройте Firebase секреты вручную!"
echo "1. Перейдите в Firebase Console: https://console.firebase.google.com/"
echo "2. Создайте новый проект или используйте существующий"
echo "3. Перейдите в Project Settings > Service Accounts"
echo "4. Сгенерируйте новый private key"
echo "5. Выполните следующие команды с реальными значениями:"
echo ""
echo "gcloud secrets create firebase-project-id --data-file=<(echo 'your-firebase-project-id')"
echo "gcloud secrets create firebase-client-email --data-file=<(echo 'your-service-account@project.iam.gserviceaccount.com')"
echo "gcloud secrets create firebase-private-key --data-file=path/to/private-key.pem"
echo ""
echo "6. Также создайте секрет для OpenAI:"
echo "gcloud secrets create openai-api-key --data-file=<(echo 'your-openai-api-key')"
echo ""
read -p "Нажмите Enter после настройки секретов..."

# Шаг 6: Сборка и развертывание сервисов
echo "🏗️ Шаг 6: Сборка и развертывание сервисов..."

# API Gateway
echo "Развертывание API Gateway..."
gcloud builds submit ./api_gateway --tag gcr.io/$PROJECT_ID/api-gateway

gcloud run deploy api-gateway \
    --image gcr.io/$PROJECT_ID/api-gateway \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --set-env-vars="ADMIN_PANEL_URL=http://admin-panel,SOURCE_MANAGEMENT_URL=http://source-management,CONVERSATION_URL=http://conversation" \
    --set-secrets="FIREBASE_PROJECT_ID=firebase-project-id:latest,FIREBASE_PRIVATE_KEY=firebase-private-key:latest,FIREBASE_CLIENT_EMAIL=firebase-client-email:latest" \
    --add-cloudsql-instances=$CONNECTION_NAME

# Admin Panel
echo "Развертывание Admin Panel..."
gcloud builds submit ./admin_panel --tag gcr.io/$PROJECT_ID/admin-panel

gcloud run deploy admin-panel \
    --image gcr.io/$PROJECT_ID/admin-panel \
    --platform managed \
    --region $REGION \
    --no-allow-unauthenticated \
    --set-secrets="DATABASE_URL=database-url:latest" \
    --add-cloudsql-instances=$CONNECTION_NAME

# Source Management
echo "Развертывание Source Management..."
gcloud builds submit ./source_management --tag gcr.io/$PROJECT_ID/source-management

gcloud run deploy source-management \
    --image gcr.io/$PROJECT_ID/source-management \
    --platform managed \
    --region $REGION \
    --no-allow-unauthenticated \
    --set-secrets="DATABASE_URL=database-url:latest" \
    --add-cloudsql-instances=$CONNECTION_NAME

# Conversation
echo "Развертывание Conversation..."
gcloud builds submit ./conversation --tag gcr.io/$PROJECT_ID/conversation

gcloud run deploy conversation \
    --image gcr.io/$PROJECT_ID/conversation \
    --platform managed \
    --region $REGION \
    --no-allow-unauthenticated \
    --set-secrets="DATABASE_URL=database-url:latest,OPENAI_API_KEY=openai-api-key:latest" \
    --add-cloudsql-instances=$CONNECTION_NAME

# Получаем URL сервисов
API_GATEWAY_URL=$(gcloud run services describe api-gateway --platform managed --region $REGION --format="value(status.url)")

# Обновляем API Gateway с URL других сервисов
ADMIN_PANEL_URL=$(gcloud run services describe admin-panel --platform managed --region $REGION --format="value(status.url)")
SOURCE_MANAGEMENT_URL=$(gcloud run services describe source-management --platform managed --region $REGION --format="value(status.url)")
CONVERSATION_URL=$(gcloud run services describe conversation --platform managed --region $REGION --format="value(status.url)")

gcloud run services update api-gateway \
    --platform managed \
    --region $REGION \
    --set-env-vars="ADMIN_PANEL_URL=$ADMIN_PANEL_URL,SOURCE_MANAGEMENT_URL=$SOURCE_MANAGEMENT_URL,CONVERSATION_URL=$CONVERSATION_URL"

echo "✅ Развертывание завершено!"
echo ""
echo "🌐 URL сервисов:"
echo "API Gateway: $API_GATEWAY_URL"
echo "Admin Panel: $ADMIN_PANEL_URL"
echo "Source Management: $SOURCE_MANAGEMENT_URL"
echo "Conversation: $CONVERSATION_URL"
echo ""
echo "📝 Следующие шаги:"
echo "1. Обновите Firebase конфигурацию в UI (ui/app.js)"
echo "2. Разверните UI на Firebase Hosting или Cloud Storage"
echo "3. Настройте домен (опционально)"
echo ""
echo "🔒 Важные секреты сохранены в Secret Manager:"
echo "- database-url"
echo "- firebase-project-id (нужно создать вручную)"
echo "- firebase-private-key (нужно создать вручную)"
echo "- firebase-client-email (нужно создать вручную)"
echo "- openai-api-key (нужно создать вручную)"
