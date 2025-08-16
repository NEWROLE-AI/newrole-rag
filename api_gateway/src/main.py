import os
import json
import uvicorn
import logging
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import firebase_admin
from firebase_admin import credentials, auth
from dotenv import load_dotenv
import base64

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

# Firebase configuration
try:
    firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")
    firebase_private_key = os.getenv("FIREBASE_PRIVATE_KEY")
    firebase_client_email = os.getenv("FIREBASE_CLIENT_EMAIL")

    if firebase_project_id and firebase_private_key and firebase_client_email:
        # Clean private key format
        private_key = firebase_private_key.replace('\\n', '\n')
        if not private_key.startswith('-----BEGIN'):
            # If it's base64 encoded, decode it
            try:
                private_key = base64.b64decode(firebase_private_key).decode('utf-8')
            except Exception as e:
                logger.warning(f"Failed to decode private key: {e}")


        firebase_config = {
            "type": "service_account",
            "project_id": firebase_project_id,
            "private_key": private_key,
            "client_email": firebase_client_email,
            "client_id": "", # Client ID is not strictly required for service account authentication
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{firebase_client_email}"
        }

        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully")
        FIREBASE_ENABLED = True
    else:
        logger.warning("Firebase credentials not found, continuing without Firebase authentication")
        FIREBASE_ENABLED = False
except Exception as e:
    logger.error(f"Failed to initialize Firebase: {e}")
    logger.warning("Continuing without Firebase authentication")
    FIREBASE_ENABLED = False

app = FastAPI(title="AI Assistant API Gateway", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Service URLs
ADMIN_PANEL_URL = os.getenv("ADMIN_PANEL_URL", "http://admin-panel:8000")
SOURCE_MANAGEMENT_URL = os.getenv("SOURCE_MANAGEMENT_URL", "http://source-management:8000")
CONVERSATION_URL = os.getenv("CONVERSATION_URL", "http://conversation:8000")

async def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify Firebase ID token and return user info"""
    if not FIREBASE_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase is not enabled or initialized"
        )
    try:
        decoded_token = auth.verify_id_token(credentials.credentials)
        return decoded_token
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

@app.post("/api/v1/auth/register")
async def register_user(user_data: dict):
    """Register a new user"""
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

# Admin Panel endpoints
@app.get("/api/v1/prompts")
async def get_prompts(user: dict = Depends(verify_firebase_token)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ADMIN_PANEL_URL}/api/v1/prompts",
            headers={"X-User-ID": user["uid"]}
        )
        response.raise_for_status()
        return response.json()

@app.post("/api/v1/prompts")
async def create_prompt(prompt_data: dict, user: dict = Depends(verify_firebase_token)):
    prompt_data["user_id"] = user["uid"]
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ADMIN_PANEL_URL}/api/v1/prompts",
            json=prompt_data,
            headers={"X-User-ID": user["uid"]}
        )
        response.raise_for_status()
        return response.json()

@app.get("/api/v1/chatbots")
async def get_chatbots(user: dict = Depends(verify_firebase_token)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ADMIN_PANEL_URL}/api/v1/chatbots",
            headers={"X-User-ID": user["uid"]}
        )
        response.raise_for_status()
        return response.json()

@app.post("/api/v1/chatbots")
async def create_chatbot(chatbot_data: dict, user: dict = Depends(verify_firebase_token)):
    chatbot_data["user_id"] = user["uid"]
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{ADMIN_PANEL_URL}/api/v1/chatbots",
            json=chatbot_data,
            headers={"X-User-ID": user["uid"]}
        )
        response.raise_for_status()
        return response.json()

# Source Management endpoints
@app.get("/api/v1/knowledge-bases")
async def get_knowledge_bases(user: dict = Depends(verify_firebase_token)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SOURCE_MANAGEMENT_URL}/api/v1/knowledge-bases",
            headers={"X-User-ID": user["uid"]}
        )
        response.raise_for_status()
        return response.json()

@app.post("/api/v1/knowledge-bases")
async def create_knowledge_base(kb_data: dict, user: dict = Depends(verify_firebase_token)):
    kb_data["user_id"] = user["uid"]
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SOURCE_MANAGEMENT_URL}/api/v1/knowledge-bases",
            json=kb_data,
            headers={"X-User-ID": user["uid"]}
        )
        response.raise_for_status()
        return response.json()

@app.post("/api/v1/resources")
async def create_resource(resource_data: dict, user: dict = Depends(verify_firebase_token)):
    resource_data["user_id"] = user["uid"]
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SOURCE_MANAGEMENT_URL}/api/v1/resources",
            json=resource_data,
            headers={"X-User-ID": user["uid"]}
        )
        response.raise_for_status()
        return response.json()

@app.post("/api/v1/data/retrieve")
async def retrieve_data(data_request: dict, user: dict = Depends(verify_firebase_token)):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SOURCE_MANAGEMENT_URL}/api/v1/data/retrieve",
            json=data_request,
            headers={"X-User-ID": user["uid"]}
        )
        response.raise_for_status()
        return response.json()

# Conversation endpoints
@app.get("/api/v1/conversations")
async def get_conversations(user: dict = Depends(verify_firebase_token)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CONVERSATION_URL}/api/v1/conversations",
            headers={"X-User-ID": user["uid"]}
        )
        response.raise_for_status()
        return response.json()

@app.post("/api/v1/conversations")
async def create_conversation(conv_data: dict, user: dict = Depends(verify_firebase_token)):
    conv_data["user_id"] = user["uid"]
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CONVERSATION_URL}/api/v1/conversations",
            json=conv_data,
            headers={"X-User-ID": user["uid"]}
        )
        response.raise_for_status()
        return response.json()

@app.post("/api/v1/conversations/{conversation_id}/messages")
async def send_message(conversation_id: str, message_data: dict, user: dict = Depends(verify_firebase_token)):
    message_data["user_id"] = user["uid"]
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{CONVERSATION_URL}/api/v1/conversations/{conversation_id}/messages",
                json=message_data,
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except httpx.RequestError as e:
        logger.error(f"Request to conversation service failed: {e}")
        raise HTTPException(status_code=503, detail="Conversation service unavailable")
    except httpx.HTTPStatusError as e:
        logger.error(f"Conversation service returned error: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))

@app.get("/api/v1/users/profile")
async def get_user_profile(user: dict = Depends(verify_firebase_token)):
    """Get current user profile"""
    return {
        "user_id": user["uid"],
        "email": user.get("email"),
        "display_name": user.get("name", ""),
        "email_verified": user.get("email_verified", False)
    }

@app.put("/api/v1/prompts/{prompt_id}")
async def update_prompt(prompt_id: str, prompt_data: dict, user: dict = Depends(verify_firebase_token)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{ADMIN_PANEL_URL}/api/v1/prompts",
                json={"prompt_id": prompt_id, **prompt_data},
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Admin panel service unavailable")
    except httpx.HTTPStatusError as e:
        logger.error(f"Admin panel service returned error: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))

@app.get("/api/v1/resources/{knowledge_base_id}")
async def get_resources_by_kb(knowledge_base_id: str, user: dict = Depends(verify_firebase_token)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SOURCE_MANAGEMENT_URL}/api/v1/resources/{knowledge_base_id}",
                headers={"X-User-ID": user["uid"]}
            )
            response.raise_for_status()
            return response.json()
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Source management service unavailable")
    except httpx.HTTPStatusError as e:
        logger.error(f"Source management service returned error: {e}")
        raise HTTPException(status_code=e.response.status_code, detail=str(e))

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)