
#!/bin/bash

# Setup Vault secrets for AI Assistant

set -e

VAULT_ADDR=${VAULT_ADDR:-"http://localhost:8200"}
VAULT_TOKEN=${VAULT_TOKEN:-"root"}

echo "🔐 Setting up Vault secrets..."

# Enable KV secrets engine
vault secrets enable -path=secret kv-v2 || echo "KV engine already enabled"

# Set Firebase secrets
echo "Setting Firebase secrets..."
vault kv put secret/firebase \
    project_id="$FIREBASE_PROJECT_ID" \
    private_key="$FIREBASE_PRIVATE_KEY" \
    client_email="$FIREBASE_CLIENT_EMAIL"

# Set AI secrets
echo "Setting AI secrets..."
vault kv put secret/ai \
    openai_key="$OPENAI_API_KEY"

# Set database secrets
echo "Setting database secrets..."
vault kv put secret/database \
    admin_panel_url="$ADMIN_PANEL_DATABASE_URL" \
    source_management_url="$SOURCE_MANAGEMENT_DATABASE_URL" \
    conversation_url="$CONVERSATION_DATABASE_URL"

echo "✅ Vault secrets setup completed!"
echo ""
echo "To verify secrets:"
echo "vault kv get secret/firebase"
echo "vault kv get secret/ai"
echo "vault kv get secret/database"
