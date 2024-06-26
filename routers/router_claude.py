from classes.claudeclass import ClaudeParam
import boto3,re,json,time,os,asyncio

#Boto3 set up
boto3_aws_access_key_id = os.getenv("boto3_aws_access_key_id")
boto3_aws_secret_access_key = os.getenv("boto3_aws_secret_access_key")
boto3_aws_region_name = os.getenv("boto3_aws_region_name")

aws_bedrock_config = {
    "region_name": boto3_aws_region_name,
    "aws_access_key_id": boto3_aws_access_key_id,
    "aws_secret_access_key": boto3_aws_secret_access_key,
}
bedrock_runtime_client = boto3.client(
    service_name="bedrock-runtime", **aws_bedrock_config
)
bedrock_client = boto3.client(service_name="bedrock", **aws_bedrock_config)

async def claude_invoke_stream(params: ClaudeParam):
    body, modelId = await claude_data_preprocess(params)
    gen_id = ""
    created_id = int(time.time())
    finish_reason = ""
    for event in bedrock_runtime_client.invoke_model_with_response_stream(
        modelId=modelId, body=body
    ).get("body"):
        chunk = event.get("chunk")
        if chunk:
            resp_item = json.loads(chunk.get("bytes").decode())
            if resp_item["type"] == "message_start":
                gen_id = resp_item["message"]["id"]
                msg_body = (
                    "data: "
                    + json.dumps(
                        {
                            "id": gen_id,
                            "object": "chat.completion.chunk",
                            "created": created_id,
                            "model": modelId,
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
            elif resp_item["type"] == "content_block_delta":
                msg_body = (
                    "data: "
                    + json.dumps(
                        {
                            "id": gen_id,
                            "object": "chat.completion.chunk",
                            "created": created_id,
                            "model": modelId,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": resp_item["delta"]["text"]},
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
            elif resp_item["type"] == "message_delta":
                finish_reason = (
                    "stop"
                    if resp_item["delta"]["stop_reason"] == "end_turn"
                    else resp_item["delta"]["stop_reason"]
                )
                continue
            elif resp_item["type"] == "message_stop":
                prompt_tokens = resp_item["amazon-bedrock-invocationMetrics"][
                    "inputTokenCount"
                ]
                completion_tokens = resp_item["amazon-bedrock-invocationMetrics"][
                    "outputTokenCount"
                ]
                total_tokens = prompt_tokens + completion_tokens
                msg_body = (
                    "data: "
                    + json.dumps(
                        {
                            "id": gen_id,
                            "object": "chat.completion.chunk",
                            "created": created_id,
                            "model": modelId,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": ""},
                                    "finish_reason": finish_reason,
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


async def claude_invoke(params: ClaudeParam):
    body, modelId = await claude_data_preprocess(params)
    response = bedrock_runtime_client.invoke_model(body=body, modelId=modelId)
    resp_item = json.loads(response.get("body").read())
    created_id = int(time.time())
    gen_id = resp_item["id"]
    content = ""
    for content_item in resp_item["content"]:
        content += content_item["text"]
    finish_reason = (
        "stop" if resp_item["stop_reason"] == "end_turn" else resp_item["stop_reason"]
    )
    prompt_tokens = resp_item["usage"]["input_tokens"]
    completion_tokens = resp_item["usage"]["output_tokens"]
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
        "model": modelId,
        "object": "chat.completion",
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        },
    }
    return msg_body


async def claude_data_preprocess(params: ClaudeParam):
    data = params.model_dump(exclude_none=True)
    modelId = data.pop("model")
    if "stop" in data:
        data["stop_sequences"] = data.pop("stop")

    for message in data["messages"]:
        if message["role"] == "system":
            data["system"] = message["content"]
    data["messages"] = [
        message for message in data["messages"] if message["role"] != "system"
    ]

    if "stream" in data:
        data.pop("stream")
    body = json.dumps(data)
    return (body, modelId)


async def oai_to_claude_params(request_data: dict):
    data = request_data
    for message in data["messages"]:
        if message["role"] == "user":
            if type(message["content"]) == list:
                for content_item in message["content"]:
                    if content_item["type"] == "image_url":
                        content_item["type"] = "image"
                        image_url = content_item.pop("image_url")
                        media_type = re.search(r"^data:(.*?);", image_url["url"]).group(
                            1
                        )
                        base64_data = re.sub(r"^data:.*?;base64,", "", image_url["url"])
                        content_item["source"] = {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64_data,
                        }
    return data


async def boto_getmodels():
    modellist = {"object": "list", "data": []}
    response = bedrock_client.list_foundation_models(
        byProvider="Anthropic", byOutputModality="TEXT"
    )
    models = response["modelSummaries"]
    for model in models:
        model_item = {
            "id": f"{model['modelId']}",
            "object": "model",
            "owned_by": "anthropic",
        }
        modellist["data"].append(model_item)
    return modellist