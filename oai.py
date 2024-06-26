import asyncio, json, os, sys, uvicorn

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

load_dotenv()
from pydantic import BaseModel
from typing import List, Optional, Literal

from classes.claudeclass import ClaudeParam
from classes.cohereclass import cohereParam
from fastapi import FastAPI, APIRouter, Request, Header, HTTPException
from fastapi.responses import StreamingResponse, Response
from routers.router_claude import (
    claude_invoke_stream,
    claude_invoke,
    oai_to_claude_params,
    boto_getmodels,
)
from routers.router_cohere import(
    cohere_invoke_stream,
    cohere_invoke,
    oai_to_cohere_params,
    cohere_getmodels   
)

AUTHOR_API_KEY = os.getenv("AUTHOR_API_KEY")




async def main():
    app = FastAPI(title="Remote API Routers", description="For Inference easily")
    router = APIRouter(tags=["Remote API hub"])

    @router.post("/claude/v1/chat/completions")
    async def claude_chat_completions(
        request: Request, authorization: str = Header(None)
    ):
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        elif authorization != f"Bearer {AUTHOR_API_KEY}":
            raise HTTPException(status_code=401, detail="Invalid API key")
        request_data = await request.json()
        request_data = await oai_to_claude_params(request_data)
        # print(request_data)
        params = ClaudeParam(**request_data)
        if params.stream is not None and params.stream is True:
            return StreamingResponse(
                claude_invoke_stream(params), media_type="text/event-stream"
            )
        else:
            return Response(
                content=json.dumps(await claude_invoke(params)),
                media_type="application/json",
            )

    @router.get("/claude/v1/models")
    async def claude_get_models(authorization: str = Header(None)):
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        elif authorization != f"Bearer {AUTHOR_API_KEY}":
            raise HTTPException(status_code=401, detail="Invalid API key")
        return Response(
            content=json.dumps(await boto_getmodels()), media_type="application/json"
        )

    @router.post("/cohere/v1/chat/completions")
    async def cohere_chat_completions(
        request: Request, authorization: str = Header(None)
    ):
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        elif authorization != f"Bearer {AUTHOR_API_KEY}":
            raise HTTPException(status_code=401, detail="Invalid API key")
        request_data = await request.json()
        request_data = await oai_to_cohere_params(request_data)
        params = cohereParam(**request_data)
        if params.stream is not None and params.stream is True:
            return StreamingResponse(
                cohere_invoke_stream(params), media_type="text/event-stream"
            )
        else:
            return Response(
                content=json.dumps(await cohere_invoke(params)),
                media_type="application/json",
            )

    @router.get("/cohere/v1/models")
    async def cohere_get_models(authorization: str = Header(None)):
        if not authorization:
            raise HTTPException(status_code=401, detail="Authorization header missing")
        elif authorization != f"Bearer {AUTHOR_API_KEY}":
            raise HTTPException(status_code=401, detail="Invalid API key")
        return Response(
            content=json.dumps(await cohere_getmodels()), media_type="application/json"
        )

    app.include_router(router)
    config = uvicorn.Config(app, host="0.0.0.0", port=5002, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server has been shut down.")
