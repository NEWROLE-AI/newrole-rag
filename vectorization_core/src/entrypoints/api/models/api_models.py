from pydantic import BaseModel


class VectorizeTextRequest(BaseModel):
    text: str


class VectorizeTextResponse(BaseModel):
    vectorized_text: list[float]
