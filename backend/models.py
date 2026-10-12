from typing import Any
from typing_extensions import TypedDict
from pydantic import BaseModel, Field, ConfigDict, HttpUrl


class QueryInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    drug: str = Field(min_length=2, max_length=120)
    disease: str = Field(min_length=2, max_length=160)
    top_k: int = Field(default=5, ge=1, le=10)
    source: str = Field(default='all', pattern='^(all|demo|uploaded)$')


class PaperInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    title: str = Field(min_length=5, max_length=500)
    abstract: str = Field(min_length=30, max_length=30000)
    link: HttpUrl | None = None


class IngestInput(BaseModel):
    papers: list[PaperInput] = Field(min_length=1, max_length=100)


class GraphState(TypedDict, total=False):
    drug: str
    disease: str
    top_k: int
    source: str
    papers: list[dict[str, Any]]
    summaries: list[dict[str, Any]]
    final_report: str
    generation_mode: str
    warnings: list[str]
    trace: list[dict[str, Any]]
