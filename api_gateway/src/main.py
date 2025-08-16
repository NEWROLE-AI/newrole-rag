
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import firebase_admin
from firebase_admin import credentials, auth
import httpx
import os
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": "service_account",
        "project_id": os.getenv("FIREBASE_PROJECT_ID"),
        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
        "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
        "client_id": os.getenv("FIREBASE_CLIENT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
    })
    firebase_admin.initialize_app(cred)

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
logger = logging.getLogger(__name__)

# Service URLs
ADMIN_PANEL_URL = os.getenv("ADMIN_PANEL_URL", "http://admin-panel:8000")
SOURCE_MANAGEMENT_URL = os.getenv("SOURCE_MANAGEMENT_URL", "http://source-management:8000")
CONVERSATION_URL = os.getenv("CONVERSATION_URL", "http://conversation:8000")

async def verify_firebase_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify Firebase ID token and return user info"""
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
        return response.json()

@app.get("/api/v1/chatbots")
async def get_chatbots(user: dict = Depends(verify_firebase_token)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{ADMIN_PANEL_URL}/api/v1/chatbots",
            headers={"X-User-ID": user["uid"]}
        )
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
        return response.json()

# Source Management endpoints
@app.get("/api/v1/knowledge-bases")
async def get_knowledge_bases(user: dict = Depends(verify_firebase_token)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SOURCE_MANAGEMENT_URL}/api/v1/knowledge-bases",
            headers={"X-User-ID": user["uid"]}
        )
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
        return response.json()

@app.post("/api/v1/data/retrieve")
async def retrieve_data(data_request: dict, user: dict = Depends(verify_firebase_token)):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SOURCE_MANAGEMENT_URL}/api/v1/data/retrieve",
            json=data_request,
            headers={"X-User-ID": user["uid"]}
        )
        return response.json()

# Conversation endpoints
@app.get("/api/v1/conversations")
async def get_conversations(user: dict = Depends(verify_firebase_token)):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CONVERSATION_URL}/api/v1/conversations",
            headers={"X-User-ID": user["uid"]}
        )
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

@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
