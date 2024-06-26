from classes.cohereclass import cohereParam
import os, time, re, json, asyncio, cohere


# Cohere set up
cohere_api_key = os.getenv("cohere_api_key")
cohere_client = cohere.AsyncClient(cohere_api_key, timeout=120)





async def cohere_getmodels():
    response = await cohere_client.models.list()
    modellist = {"object": "list", "data": []}
    for item in response.models:
        # print(item)
        if "chat" in item.endpoints and item.context_length >= 128000:
            item_data = {"id": item.name, "object": "model", "owned_by": "cohere"}
            modellist["data"].append(item_data)
    return modellist


async def oai_to_cohere_params(request_data: dict):
    data = request_data
    data["chat_history"] = []
    data["p"] = data.pop("top_p", None)
    data["stop_sequences"] = data.pop("stop", None)
    for message in data["messages"]:
        message["role"] = message["role"].upper()
        if message["role"] == "ASSISTANT":
            message["role"] == "CHATBOT"
        elif message["role"] == "SYSTEM":
            data["preamble"] = message["content"]
        message["message"] = message.pop("content")
    data["chat_history"] = [
        item for item in data["messages"] if item.get("role") != "SYSTEM"
    ]
    data["message"] = data["chat_history"].pop()["message"]
    if len(data["chat_history"]) <= 0:
        data.pop("chat_history")
    data.pop("messages")

    return data


async def cohere_invoke_stream(params: cohereParam):
    data = params.model_dump(exclude_none=True)
    model = data["model"]
    if "stream" in data:
        data.pop("stream")
    gen_id = ""
    created_id = int(time.time())
    async for event in cohere_client.chat_stream(**data):
        # print(event)
        if event.event_type == "stream-start":
            gen_id = event.generation_id
            msg_body = (
                "data: "
                + json.dumps(
                    {
                        "id": gen_id,
                        "object": "chat.completion.chunk",
                        "created": created_id,
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"role": "assistant", "content": ""},
                                "finish_reason": None,
                                "logprobs": None,
                            }
                        ],
                    }
                )
                + "\n\n"
            )
            await asyncio.sleep(0.01)
            yield msg_body

        elif event.event_type == "text-generation":
            msg_body = (
                "data: "
                + json.dumps(
                    {
                        "id": gen_id,
                        "object": "chat.completion.chunk",
                        "created": created_id,
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": event.text},
                                "finish_reason": None,
                                "logprobs": None,
                            }
                        ],
                    }
                )
                + "\n\n"
            )
            await asyncio.sleep(0.01)
            yield msg_body
        elif event.event_type == "stream-end":
            prompt_tokens = event.response.meta.tokens.input_tokens
            completion_tokens = event.response.meta.tokens.output_tokens
            total_tokens = prompt_tokens + completion_tokens
            msg_body = (
                "data: "
                + json.dumps(
                    {
                        "id": gen_id,
                        "object": "chat.completion.chunk",
                        "created": created_id,
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {"content": ""},
                                "finish_reason": (
                                    "stop"
                                    if event.finish_reason == "COMPLETE"
                                    else event.finish_reason
                                ),
                                "logprobs": None,
                            }
                        ],
                        "usage": {
                            "prompt_tokens": prompt_tokens,
                            "total_tokens": total_tokens,
                            "completion_tokens": completion_tokens,
                        },
                    }
                )
                + "\n\n"
            )
            await asyncio.sleep(0.01)
            yield msg_body
            break

    yield "data: [DONE]\n\n"


async def cohere_invoke(params: cohereParam):
    data = params.model_dump(exclude_none=True)
    model = data["model"]
    if "stream" in data:
        data.pop("stream")
    created_id = int(time.time())
    resp = await cohere_client.chat(**data)
    gen_id = resp.generation_id
    content = resp.text
    finish_reason = "stop" if resp.finish_reason == "COMPLETE" else resp.finish_reason
    prompt_tokens = resp.meta.tokens.input_tokens
    completion_tokens = resp.meta.tokens.output_tokens
    total_tokens = prompt_tokens + completion_tokens
    msg_body = {
        "id": gen_id,
        "choices": [
            {
                "index": 0,
                "message": {"content": content, "role": "assistant"},
                "finish_reason": finish_reason,
                "logprobs": None,
            }
        ],
        "created": created_id,
        "model": model,
        "object": "chat.completion",
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        },
    }
    return msg_body