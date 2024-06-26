from pydantic import BaseModel
from typing import Optional, List, Literal

class cohere_chat_toolcalls(BaseModel):
    name: str
    parameters: dict


class cohere_chat_TOOL_results(BaseModel):
    call: cohere_chat_toolcalls
    output: List[dict]


class cohere_chat_CHATBOT(BaseModel):
    role: str
    message: str
    tool_calls: Optional[List[cohere_chat_toolcalls]] = None


class cohere_chat_SYSTEM(BaseModel):
    role: str
    message: str
    tool_calls: Optional[List[cohere_chat_toolcalls]] = None


class cohere_chat_USER(BaseModel):
    role: str
    message: str
    tool_calls: Optional[List[cohere_chat_toolcalls]] = None


class cohere_chat_TOOL(BaseModel):
    role: str
    tool_results: Optional[List[cohere_chat_TOOL_results]] = None


class cohere_connector_items(BaseModel):
    id: str
    user_access_token: Optional[str] = None
    continue_on_failure: Optional[bool] = None
    options: Optional[dict] = None


class cohereParam(BaseModel):
    message: str
    model: str
    stream: Optional[bool] = None
    preamble: Optional[str] = None
    chat_history: Optional[
        List[
            cohere_chat_SYSTEM
            | cohere_chat_USER
            | cohere_chat_CHATBOT
            | cohere_chat_TOOL
            | None
        ]
    ] = None
    conversation_id: Optional[str] = None
    prompt_truncation: Optional[Literal["AUTO", "AUTO_PRESERVE_ORDER", "OFF"]] = None
    connector: Optional[List[cohere_connector_items]] = None
    search_queries_only: Optional[bool] = None
    documents: Optional[List[dict]] = None
    citation_quality: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    max_input_tokens: Optional[int] = None
    k: Optional[int] = None
    p: Optional[float] = None
    seed: Optional[int] = None
    stop_sequences: Optional[List[str]] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    tools: Optional[List[dict]] = None
    tool_results: Optional[List[dict]] = None