from fastapi import APIRouter, HTTPException
from univy.rag.models import QueryRequest, QueryResponse
from univy.lightrag_utils import initialize_lightrag
from lightrag import QueryParam
from ascii_colors import trace_exception
from loguru import logger
import json


router = APIRouter(prefix="/rag", tags=["rag"])


@router.post(
    "/query", response_model=QueryResponse,
)
async def query_text(request: QueryRequest):
    """
    Handle a POST request at the /query endpoint to process user queries using RAG capabilities.

    Parameters:
        request (QueryRequest): The request object containing the query parameters.
    Returns:
        QueryResponse: A Pydantic model containing the result of the query processing.
                    If a string is returned (e.g., cache hit), it's directly returned.
                    Otherwise, an async generator may be used to build the response.

    Raises:
        HTTPException: Raised when an error occurs during the request handling process,
                    with status code 500 and detail containing the exception message.
    """
    try:
        rag = await initialize_lightrag()
        param = request.to_query_params(False)
        response = await rag.aquery(request.query, param=param)

        # If response is a string (e.g. cache hit), return directly
        if isinstance(response, str):
            return QueryResponse(response=response)

        if isinstance(response, dict):
            result = json.dumps(response, indent=2)
            return QueryResponse(response=result)
        else:
            return QueryResponse(response=str(response))
    except Exception as e:
        trace_exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/stream")
async def query_text_stream(request: QueryRequest):
    """
    This endpoint performs a retrieval-augmented generation (RAG) query and streams the response.

    Args:
        request (QueryRequest): The request object containing the query parameters.
        optional_api_key (Optional[str], optional): An optional API key for authentication. Defaults to None.

    Returns:
        StreamingResponse: A streaming response containing the RAG query results.
    """
    try:
        rag = await initialize_lightrag()
        param = request.to_query_params(True)
        response = await rag.aquery(request.query, param=param)

        from fastapi.responses import StreamingResponse

        async def stream_generator():
            if isinstance(response, str):
                # If it's a string, send it all at once
                yield f"{json.dumps({'response': response})}\n"
            elif response is None:
                # Handle None response (e.g., when only_need_context=True but no context found)
                yield f"{json.dumps({'response': 'No relevant context found for the query.'})}\n"
            else:
                # If it's an async generator, send chunks one by one
                try:
                    async for chunk in response:
                        if chunk:  # Only send non-empty content
                            yield f"{json.dumps({'response': chunk})}\n"
                except Exception as e:
                    logger.error(f"Streaming error: {str(e)}")
                    yield f"{json.dumps({'error': str(e)})}\n"

        return StreamingResponse(
            stream_generator(),
            media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "application/x-ndjson",
                # Ensure proper handling of streaming response when proxied by Nginx
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        trace_exception(e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query-simple")
async def query_text_simple(input_text: str):
    """
    This endpoint performs a simple query on the RAG.
    """
    try:
        rag = await initialize_lightrag()
        response = await rag.aquery(input_text, param=QueryParam(mode="hybrid"))
        return QueryResponse(response=response)
    except Exception as e:
        trace_exception(e)
        raise HTTPException(status_code=500, detail=str(e))
