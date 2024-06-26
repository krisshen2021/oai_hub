from pydantic import BaseModel
from typing import Optional, List, Literal

# classes for oai messages <start>
class function_obj(BaseModel):
    name: str
    arguments: str


class tool_calls_obj(BaseModel):
    id: str
    type: str
    function: function_obj


class AssistantMessage(BaseModel):
    role: str
    content: Optional[str] = None
    tool_calls: Optional[List[tool_calls_obj]] = None
    function_call: Optional[function_obj] = None

class UserSystemMessage(BaseModel):
    role: str
    content: str
    name: Optional[str] = None


class ToolMessage(BaseModel):
    role: str
    content: str
    tool_call_id: str


# <end>


class response_format_obj(BaseModel):
    type: str


class stream_options_obj(BaseModel):
    include_usage: bool


class function_for_tools_obj(BaseModel):
    description: Optional[str] = None
    name: str
    parameters: Optional[dict] = None


class tools_obj(BaseModel):
    type: str
    function: function_for_tools_obj


class function_for_toolchoice(BaseModel):
    name: str


class tool_choice_obj(BaseModel):
    type: str
    function: function_for_toolchoice


class OAIParam(BaseModel):
    messages: List[UserSystemMessage | AssistantMessage | ToolMessage]
    model: str
    frequency_penalty: Optional[float] = None
    logit_bias: Optional[dict] = None
    logprobs: Optional[bool] = None
    top_logprobs: Optional[int] = None
    max_tokens: Optional[int] = None
    n: Optional[int] = None
    presence_penalty: Optional[float] = None
    response_format: Optional[response_format_obj] = None
    seed: Optional[int] = None
    service_tier: Optional[str] = None
    stop: Optional[str | List[str]] = None
    stream: Optional[bool] = None
    stream_options: Optional[stream_options_obj] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    tools: Optional[List[tools_obj]] = None
    tool_choice: Optional[str | dict] = None
    parallel_tool_calls: Optional[bool] = None
    user: Optional[str] = None
    function_call: Optional[str | dict] = None
    functions: Optional[List[dict]] = None