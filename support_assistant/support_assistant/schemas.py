"""
Pydantic models for the /ask endpoint.

AskRequest  -> what the client sends in.
AskResponse -> the structured-output contract every graph run must satisfy,
               whether the answer was produced by the mock branch or the
               optional real-LLM branch.
"""

from typing import List

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    query: str


class AskResponse(BaseModel):
    answer: str
    sources: List[str] = Field(
        default_factory=list,
        description="Chunk/document IDs used to ground the answer. Empty for general_question answers.",
    )
    confidence: float = Field(ge=0.0, le=1.0)
