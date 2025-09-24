import base64
import logging
import os
from typing import Optional, Dict, Any

import firebase_admin
import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from firebase_admin import credentials, auth

# Импорт моделей из файлов models
from admin_panel.src.entrypoints.api.models.api_models import (
    CreatePromptRequest, CreatePromptResponse,
    CreateAgentChatBotRequest, CreateAgentChatBotResponse,
    GetPromptsResponse, GetChatbotsResponse
)
from conversation.src.entrypoints.api.models.api_models import (
    CreateConversationRequest, CreateConversationResponse,
    ConversationRequest, ConversationResponse, GetConversationResponse, GetMessagesResponse
)
from source_management.src.entrypoints.api.models.api_models import (
    CreateKnowledgeBaseRequest, CreateKnowledgeBaseResponse,
    CreateResourceRequest, CreateResourceResponse,
    GetKnowledgeBasesResponse, GetAllResourcesResponse
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

try:
    from vault_client import get_vault_secrets
    vault_available = True
except ImportError:
    logger.info("Vault client not available, using environment variables")
    vault_available = False

# Try to get secrets from Vault, fallback to environment variables
if vault_available:
    try:
        vault_secrets = get_vault_secrets()
        os.environ.update({k: v for k, v in vault_secrets.items() if v})
        logger.info("Using secrets from Vault")
    except Exception as e:
        logger.warning(f"Failed to get secrets from Vault: {e}, using environment variables")

# Environment check
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
DEV_MODE = ENVIRONMENT == "dev"

# Firebase configuration - работает в обоих режимах
FIREBASE_ENABLED = False

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    global FIREBASE_ENABLED
    try:
        firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")
        firebase_private_key = os.getenv("FIREBASE_PRIVATE_KEY")
        firebase_client_email = os.getenv("FIREBASE_CLIENT_EMAIL")

        # Проверяем наличие обязательных переменных
        if not all([firebase_project_id, firebase_private_key, firebase_client_email]):
            logger.warning("Firebase credentials not found, running without Firebase Auth")
            return False

        # Clean private key format
        private_key = firebase_private_key.replace('\\n', '\n')
        if not private_key.startswith('-----BEGIN'):
            try:
                private_key = base64.b64decode(firebase_private_key).decode('utf-8')
            except Exception as e:
                logger.warning(f"Failed to decode private key: {e}")

        firebase_config = {
            "type": "service_account",
            "project_id": firebase_project_id,
            "private_key": private_key,
            "client_email": firebase_client_email,
            "client_id": "",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{firebase_client_email}"
        }

        # Проверяем, не инициализирован ли уже Firebase
        if firebase_admin._apps:
            logger.info("Firebase Admin SDK already initialized")
            FIREBASE_ENABLED = True
            return True

        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
        logger.info(f"Firebase Admin SDK initialized successfully (Environment: {ENVIRONMENT})")
        FIREBASE_ENABLED = True
        return True

    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        logger.warning("Continuing without Firebase authentication")
        FIREBASE_ENABLED = False
        return False

# Инициализируем Firebase при запуске
initialize_firebase()

app = FastAPI(title="AI Assistant API Gateway", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer(auto_error=False)

# Service URLs
ADMIN_PANEL_URL = os.getenv("ADMIN_PANEL_URL", "http://admin-panel:8000")
SOURCE_MANAGEMENT_URL = os.getenv("SOURCE_MANAGEMENT_URL", "http://source-management:8000")
CONVERSATION_URL = os.getenv("CONVERSATION_URL", "http://conversation:8000")

async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """Get current user - Firebase or dev mode fallback"""

    # Сначала пытаемся Firebase аутентификацию если доступна
    if FIREBASE_ENABLED and credentials:
        try:
            decoded_token = auth.verify_id_token(credentials.credentials)
            logger.info(f"Firebase auth successful for user: {decoded_token.get('email', decoded_token['uid'])}")
            return decoded_token
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            if not DEV_MODE:
                # В продакшне это ошибка
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Firebase authentication token"
                )

    # В dev режиме продолжаем к fallback логике
    # В production режиме требуем Firebase аутентификацию
    logger.warning(f"Authentication failed - Firebase not available or invalid token")
    logger.info(f"Environment: {ENVIRONMENT}, Firebase enabled: {FIREBASE_ENABLED}")

    # Production mode без Firebase - ошибка
    if not FIREBASE_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase authentication is not available"
        )

    # Нет учетных данных в продакшне
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.post("/api/v1/auth/register")
async def register_user(user_data: dict):
    """Register a new user"""
    if DEV_MODE:
        return {"message": "Registration simulated in dev mode", "user_id": "demo-user"}

    if not FIREBASE_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase is not enabled or initialized"
        )

    try:
        # Create user in Firebase
        user = auth.create_user(
            email=user_data["email"],
            password=user_data["password"],
            display_name=user_data.get("display_name", "")
        )

        # Create user in our services
        user_payload = {
            "user_id": user.uid,
            "email": user.email,
            "display_name": user.display_name or "",
            "created_at": user.user_metadata.creation_timestamp
        }

        # Create user in admin panel
        async with httpx.AsyncClient() as client:
            await client.post(f"{ADMIN_PANEL_URL}/api/v1/users", json=user_payload)
            await client.post(f"{SOURCE_MANAGEMENT_URL}/api/v1/users", json=user_payload)
            await client.post(f"{CONVERSATION_URL}/api/v1/users", json=user_payload)

        return {"message": "User registered successfully", "user_id": user.uid}
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ========== ADMIN PANEL ENDPOINTS ==========

@app.get("/api/v1/prompts", response_model=GetPromptsResponse)
async def get_prompts(user: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ADMIN_PANEL_URL}/api/v1/prompts",
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error getting prompts: {e}")
        # В dev режиме возвращаем пустой ответ вместо ошибки
        if DEV_MODE:
            return {"prompts": []}
        raise HTTPException(status_code=503, detail="Admin panel service unavailable")

@app.post("/api/v1/prompts", response_model=CreatePromptResponse)
async def create_prompt(prompt_data: CreatePromptRequest, user: dict = Depends(get_current_user)):
    # Преобразуем модель в dict для отправки в сервис
    prompt_dict = prompt_data.model_dump()
    prompt_dict["user_id"] = user["uid"]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ADMIN_PANEL_URL}/api/v1/prompts",
                json=prompt_dict,
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error creating prompt: {e}")
        if DEV_MODE:
            return {"prompt_id": "demo-id", "message": "Prompt created (dev mode)"}
        raise HTTPException(status_code=503, detail="Admin panel service unavailable")

@app.delete("/api/v1/prompts/{prompt_id}")
async def delete_prompt(prompt_id: str, user: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{ADMIN_PANEL_URL}/api/v1/prompts/{prompt_id}",
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error deleting prompt: {e}")
        if DEV_MODE:
            return {"message": "Prompt deleted (dev mode)"}
        raise HTTPException(status_code=503, detail="Admin panel service unavailable")

@app.get("/api/v1/chatbots", response_model=GetChatbotsResponse)
async def get_chatbots(user: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ADMIN_PANEL_URL}/api/v1/agent_chat_bots",
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error getting chatbots: {e}")
        if DEV_MODE:
            return {"chatbots": []}
        raise HTTPException(status_code=503, detail="Admin panel service unavailable")

@app.post("/api/v1/chatbots", response_model=CreateAgentChatBotResponse)
async def create_chatbot(chatbot_data: CreateAgentChatBotRequest, user: dict = Depends(get_current_user)):
    # Преобразуем модель в dict и добавляем user_id
    chatbot_dict = chatbot_data.model_dump()
    chatbot_dict["user_id"] = user["uid"]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{ADMIN_PANEL_URL}/api/v1/agent_chat_bots",
                json=chatbot_dict,
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error creating chatbot: {e}")
        if DEV_MODE:
            return {"agent_chat_bot_id": "demo-chatbot-id", "message": "Chatbot created (dev mode)"}
        raise HTTPException(status_code=503, detail="Admin panel service unavailable")

@app.delete("/api/v1/chatbots/{chatbot_id}")
async def delete_chatbot(chatbot_id: str, user: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{ADMIN_PANEL_URL}/api/v1/chatbots/{chatbot_id}",
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error deleting chatbot: {e}")
        if DEV_MODE:
            return {"message": "Chatbot deleted (dev mode)"}
        raise HTTPException(status_code=503, detail="Admin panel service unavailable")

# ========== SOURCE MANAGEMENT ENDPOINTS ==========

@app.get("/api/v1/knowledge-bases", response_model=GetKnowledgeBasesResponse)
async def get_knowledge_bases(user: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SOURCE_MANAGEMENT_URL}/api/v1/knowledge-bases",
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error getting knowledge bases: {e}")
        if DEV_MODE:
            return {"knowledge_bases": []}
        raise HTTPException(status_code=503, detail="Source management service unavailable")

@app.post("/api/v1/knowledge-bases", response_model=CreateKnowledgeBaseResponse)
async def create_knowledge_base(kb_data: CreateKnowledgeBaseRequest, user: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SOURCE_MANAGEMENT_URL}/api/v1/knowledge-bases",
                json=kb_data.model_dump(),  # Используем всю модель
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error creating knowledge base: {e}")
        if DEV_MODE:
            return {"knowledge_base_id": "demo-kb-id", "message": "Knowledge base created (dev mode)"}
        raise HTTPException(status_code=503, detail="Source management service unavailable")

@app.delete("/api/v1/knowledge-bases/{kb_id}")
async def delete_knowledge_base(kb_id: str, user: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{SOURCE_MANAGEMENT_URL}/api/v1/knowledge-bases/{kb_id}",
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error deleting knowledge base: {e}")
        if DEV_MODE:
            return {"message": "Knowledge base deleted (dev mode)"}
        raise HTTPException(status_code=503, detail="Source management service unavailable")

@app.get("/api/v1/resources", response_model=GetAllResourcesResponse)
async def get_resources(user: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SOURCE_MANAGEMENT_URL}/api/v1/resources",
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error getting resources: {e}")
        if DEV_MODE:
            return {"resources": []}
        raise HTTPException(status_code=503, detail="Source management service unavailable")

@app.post("/api/v1/resources", response_model=CreateResourceResponse)
async def create_resource(resource_data: CreateResourceRequest, user: dict = Depends(get_current_user)):
    # Добавляем user_id в модель перед отправкой
    resource_dict = resource_data.model_dump()
    resource_dict["user_id"] = user["uid"]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SOURCE_MANAGEMENT_URL}/api/v1/resources",
                json=resource_dict,
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error creating resource: {e}")
        if DEV_MODE:
            return {"resource_id": "demo-resource-id", "message": "Resource created (dev mode)"}
        raise HTTPException(status_code=503, detail="Source management service unavailable")

@app.delete("/api/v1/resources/{resource_id}")
async def delete_resource(resource_id: str, user: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{SOURCE_MANAGEMENT_URL}/api/v1/resources/{resource_id}",
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error deleting resource: {e}")
        if DEV_MODE:
            return {"message": "Resource deleted (dev mode)"}
        raise HTTPException(status_code=503, detail="Source management service unavailable")

# ========== CONVERSATION ENDPOINTS ==========

@app.get("/api/v1/conversations", response_model=GetConversationResponse)
async def get_conversations(user: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{CONVERSATION_URL}/api/v1/conversations",
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        if DEV_MODE:
            return {"conversations": []}
        raise HTTPException(status_code=503, detail="Conversation service unavailable")

@app.post("/api/v1/conversations", response_model=CreateConversationResponse)
async def create_conversation(conv_data: CreateConversationRequest, user: dict = Depends(get_current_user)):
    # Преобразуем модель в dict и добавляем user_id
    conv_dict = conv_data.model_dump()
    conv_dict["user_id"] = user["uid"]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CONVERSATION_URL}/api/v1/conversations",
                json=conv_dict,
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        if DEV_MODE:
            return {"conversation_id": "demo-conv-id", "message": "Conversation created (dev mode)"}
        raise HTTPException(status_code=503, detail="Conversation service unavailable")

@app.delete("/api/v1/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{CONVERSATION_URL}/api/v1/conversations/{conversation_id}",
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        if DEV_MODE:
            return {"message": "Conversation deleted (dev mode)"}
        raise HTTPException(status_code=503, detail="Conversation service unavailable")

@app.get("/api/v1/conversations/{conversation_id}/messages", response_model=GetMessagesResponse)
async def get_messages(conversation_id: str, user: dict = Depends(get_current_user)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{CONVERSATION_URL}/api/v1/conversations/{conversation_id}/messages",
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        if DEV_MODE:
            return {"messages": []}
        raise HTTPException(status_code=503, detail="Conversation service unavailable")

@app.post("/api/v1/conversations/{conversation_id}/messages", response_model=ConversationResponse)
async def send_message(conversation_id: str, message_data: ConversationRequest, user: dict = Depends(get_current_user)):
    # Преобразуем модель в dict и добавляем user_id
    message_dict = message_data.model_dump()
    message_dict["user_id"] = user["uid"]

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CONVERSATION_URL}/api/v1/conversations/{conversation_id}/messages",
                json=message_dict,
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        if DEV_MODE:
            return {"conversation_id": conversation_id, "message": "Message sent (dev mode)"}
        raise HTTPException(status_code=503, detail="Conversation service unavailable")

@app.get("/api/v1/users/profile")
async def get_user_profile(user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return {
        "user_id": user["uid"],
        "email": user.get("email"),
        "display_name": user.get("name", ""),
        "email_verified": user.get("email_verified", False)
    }

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
