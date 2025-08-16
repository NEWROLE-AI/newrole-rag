
# Руководство по развертыванию AI Assistant в Google Cloud

## Предварительные требования

1. **Google Cloud Account** - зарегистрируйтесь на https://cloud.google.com/
2. **Google Cloud CLI** - установите gcloud CLI: https://cloud.google.com/sdk/docs/install
3. **Firebase Account** - создайте проект на https://firebase.google.com/
4. **OpenAI API Key** - получите ключ на https://openai.com/api/

## Быстрое развертывание

### Шаг 1: Подготовка
```bash
# Аутентификация в Google Cloud
gcloud auth login

# Создайте новый проект или используйте существующий
gcloud projects create your-ai-assistant-project --name="AI Assistant"
gcloud config set project your-ai-assistant-project

# Включите биллинг для проекта в Google Cloud Console
```

### Шаг 2: Настройка секретов
```bash
# Сделайте скрипт исполняемым и запустите
chmod +x setup-gcp-secrets.sh
./setup-gcp-secrets.sh your-ai-assistant-project
```

### Шаг 3: Развертывание
```bash
# Сделайте скрипт исполняемым и запустите
chmod +x deploy-gcp-detailed.sh
./deploy-gcp-detailed.sh your-ai-assistant-project us-central1
```

## Подробная настройка Firebase

### 1. Создание Firebase проекта
1. Перейдите на https://console.firebase.google.com/
2. Создайте новый проект или выберите существующий Google Cloud проект
3. Включите Authentication с Email/Password provider

### 2. Получение Service Account Key
1. В Firebase Console перейдите в Project Settings
2. Перейдите на вкладку "Service accounts"
3. Нажмите "Generate new private key"
4. Сохраните JSON файл

### 3. Настройка секретов
```bash
# Из JSON файла извлеките значения:
PROJECT_ID="your-project-id"
CLIENT_EMAIL="firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com"
PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"

# Создайте секреты
echo "$PROJECT_ID" | gcloud secrets create firebase-project-id --data-file=-
echo "$CLIENT_EMAIL" | gcloud secrets create firebase-client-email --data-file=-
echo "$PRIVATE_KEY" | gcloud secrets create firebase-private-key --data-file=-
```

## После развертывания

### 1. Настройка UI
Обновите `ui/app.js` с реальными Firebase настройками:
```javascript
const firebaseConfig = {
    apiKey: "your-api-key",
    authDomain: "your-project.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project.appspot.com",
    messagingSenderId: "123456789",
    appId: "your-app-id"
};
```

### 2. Развертывание UI
```bash
# Опция 1: Firebase Hosting
npm install -g firebase-tools
firebase init hosting
firebase deploy

# Опция 2: Cloud Storage Static Website
gsutil mb gs://your-ui-bucket
gsutil cp -r ui/* gs://your-ui-bucket
gsutil web set -m index.html gs://your-ui-bucket
```

### 3. Настройка доменов (опционально)
```bash
# Для Cloud Run сервисов
gcloud run domain-mappings create --service api-gateway --domain api.yourdomain.com
```

## Мониторинг и логи

```bash
# Просмотр логов
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=api-gateway" --limit 50

# Мониторинг в Cloud Console
# https://console.cloud.google.com/run
```

## Стоимость

Примерные затраты для малой нагрузки:
- Cloud Run: $0 (в рамках free tier)
- Cloud SQL: ~$7/месяц (db-f1-micro)
- Secret Manager: ~$0.06/месяц за секрет
- Firebase: $0 (в рамках free tier)

## Устранение проблем

### Проблемы с аутентификацией
- Проверьте правильность Firebase секретов
- Убедитесь, что enabled Authentication в Firebase Console

### Проблемы с базой данных
- Проверьте Cloud SQL instance статус
- Убедитесь, что database URL секрет корректен

### Проблемы с сетью
- Проверьте firewall правила
- Убедитесь, что сервисы могут общаться друг с другом
