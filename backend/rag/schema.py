from typing import List, Literal
from langchain_core.pydantic_v1 import BaseModel, Field

class QAResponse(BaseModel):
    summary: str = Field(description="Short, direct answer grounded in the logs")
    severity: Literal["Low","Medium","High"] = "Low"
    findings: List[str] = Field(default_factory=list, description="Key findings from retrieved logs")
    recommendations: List[str] = Field(default_factory=list, description="Actionable steps")
    citations: List[str] = Field(default_factory=list, description="Short log snippets used as evidence")
