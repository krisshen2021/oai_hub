from pydantic import BaseModel
from typing import Optional, List, Literal

class image_source_obj(BaseModel):
    type: Literal["base64"] = "base64"
    media_type: Literal["image/jpeg", "image/png", "image/gif", "image/webp"] = "image/jpeg"
    data: str


class content_multimodel_image(BaseModel):
    type: str = "image"
    source: image_source_obj


class content_multimodel_text(BaseModel):
    type: str = "text"
    text: str


class ClaudeMessage(BaseModel):
    role: str
    content: str | List[content_multimodel_text | content_multimodel_image]
    name: Optional[str] = None


class ClaudeParam(BaseModel):
    anthropic_version: Optional[str] = "bedrock-2023-05-31"
    max_tokens: Optional[int] = 1024
    messages: List[ClaudeMessage]
    system: Optional[str] = None
    stop: Optional[str | List[str]] = None
    temperature: Optional[float] = None
    top_k: Optional[int] = None
    top_p: Optional[float] = None
    stream: Optional[bool] = None
    model: Optional[str] = "anthropic.claude-3-5-sonnet-20240620-v1:0"