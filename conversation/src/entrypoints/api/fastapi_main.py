from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .fastapi_handlers import router

app = FastAPI(title="Conversation API", version="1.0.0")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Conversation API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}