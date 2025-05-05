from fastapi import Depends, APIRouter
from dependency_injector.wiring import Provide, inject

from src.adapters.fasttext_vectorizer import FastTextVectorizer
from src.entrypoints.api.ioc import Container
from aws_lambda_powertools import Logger

from src.entrypoints.api.models.api_models import (
    VectorizeTextRequest,
    VectorizeTextResponse,
)

# Initialize router and logger
router = APIRouter()
logger = Logger(service="VectorizationService")


@router.post("/v1/vectorize_text")
@inject
async def vectorize_text(
    request: VectorizeTextRequest,
    vectorize_service: FastTextVectorizer = Depends(
        Provide[Container.fasttext_vectorizer]
    ),
):
    """
    Vectorize raw text using FastText model.

    This endpoint accepts raw text and returns its vector representation using
    the FastText vectorization service.

    Args:
        request (VectorizeTextRequest): Request containing the text to vectorize
        vectorize_service (FastTextVectorizer): Injected FastText vectorization service

    Returns:
        VectorizeTextResponse: Response containing the vectorized text representation
    """
    logger.info("Received vectorize text request", extra={"request": request})
    vector = await vectorize_service.vectorize_text(request.text)
    logger.info("Vectorization completed successfully")
    return VectorizeTextResponse(vectorized_text=vector)
