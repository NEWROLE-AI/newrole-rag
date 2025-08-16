
#!/bin/bash

# Скрипт для настройки секретов в Google Cloud

set -e

echo "🔐 Настройка секретов для AI Assistant в Google Cloud"

# Проверяем аргументы
if [ $# -lt 1 ]; then
    echo "Usage: $0 PROJECT_ID"
    echo "Example: $0 my-ai-assistant-project"
    exit 1
fi

PROJECT_ID=$1
gcloud config set project $PROJECT_ID

echo "📋 Настраиваем секреты для проекта: $PROJECT_ID"

# Функция для создания секрета
create_secret() {
    local SECRET_NAME=$1
    local PROMPT_MSG=$2
    
    echo ""
    echo "🔑 Настройка секрета: $SECRET_NAME"
    echo "$PROMPT_MSG"
    read -p "Введите значение: " SECRET_VALUE
    
    if [ -n "$SECRET_VALUE" ]; then
        echo -n "$SECRET_VALUE" | gcloud secrets create $SECRET_NAME --data-file=- || \
        echo -n "$SECRET_VALUE" | gcloud secrets versions add $SECRET_NAME --data-file=-
        echo "✅ Секрет $SECRET_NAME создан/обновлен"
    else
        echo "⚠️ Пропущен секрет $SECRET_NAME"
    fi
}

# Создаем секреты
create_secret "firebase-project-id" "Введите Firebase Project ID (из Firebase Console):"
create_secret "firebase-client-email" "Введите Firebase Client Email (service-account@project.iam.gserviceaccount.com):"
create_secret "openai-api-key" "Введите OpenAI API Key (начинается с sk-):"

echo ""
echo "🔑 Настройка Firebase Private Key"
echo "Для private key создайте файл с ключом и выполните:"
echo "gcloud secrets create firebase-private-key --data-file=path/to/private-key.pem"
echo ""
echo "Или введите ключ прямо сейчас (многострочный, завершите пустой строкой):"
echo "-----BEGIN PRIVATE KEY-----"

PRIVATE_KEY=""
while IFS= read -r line; do
    if [ -z "$line" ]; then
        break
    fi
    PRIVATE_KEY="$PRIVATE_KEY$line\n"
done

if [ -n "$PRIVATE_KEY" ]; then
    printf "$PRIVATE_KEY" | gcloud secrets create firebase-private-key --data-file=- || \
    printf "$PRIVATE_KEY" | gcloud secrets versions add firebase-private-key --data-file=-
    echo "✅ Firebase Private Key создан/обновлен"
fi

echo ""
echo "✅ Настройка секретов завершена!"
echo ""
echo "📝 Созданные секреты:"
gcloud secrets list --format="table(name)"
