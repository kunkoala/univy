from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, List, Dict, Any
from lightrag import LightRAG, QueryParam


class QueryRequest(BaseModel):
    query: str = Field(
        min_length=1,
        description="The query text",
    )

    mode: Literal["local", "global", "hybrid", "naive", "mix", "bypass"] = Field(
        default="hybrid",
        description="Query mode",
    )

    only_need_context: Optional[bool] = Field(
        default=None,
        description="If True, only returns the retrieved context without generating a response.",
    )

    only_need_prompt: Optional[bool] = Field(
        default=None,
        description="If True, only returns the generated prompt without producing a response.",
    )

    response_type: Optional[str] = Field(
        min_length=1,
        default=None,
        description="Defines the response format. Examples: 'Multiple Paragraphs', 'Single Paragraph', 'Bullet Points'.",
    )

    top_k: Optional[int] = Field(
        ge=1,
        default=None,
        description="Number of top items to retrieve. Represents entities in 'local' mode and relationships in 'global' mode.",
    )

    max_token_for_text_unit: Optional[int] = Field(
        gt=1,
        default=None,
        description="Maximum number of tokens allowed for each retrieved text chunk.",
    )

    max_token_for_global_context: Optional[int] = Field(
        gt=1,
        default=None,
        description="Maximum number of tokens allocated for relationship descriptions in global retrieval.",
    )

    max_token_for_local_context: Optional[int] = Field(
        gt=1,
        default=None,
        description="Maximum number of tokens allocated for entity descriptions in local retrieval.",
    )

    conversation_history: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Stores past conversation history to maintain context. Format: [{'role': 'user/assistant', 'content': 'message'}].",
    )

    history_turns: Optional[int] = Field(
        ge=0,
        default=None,
        description="Number of complete conversation turns (user-assistant pairs) to consider in the response context.",
    )

    ids: list[str] | None = Field(
        default=None, description="List of ids to filter the results."
    )

    user_prompt: Optional[str] = Field(
        default=None,
        description="User-provided prompt for the query. If provided, this will be used instead of the default value from prompt template.",
    )

    @field_validator("query", mode="after")
    @classmethod
    def query_strip_after(cls, query: str) -> str:
        return query.strip()

    @field_validator("conversation_history", mode="after")
    @classmethod
    def conversation_history_role_check(
        cls, conversation_history: List[Dict[str, Any]] | None
    ) -> List[Dict[str, Any]] | None:
        if conversation_history is None:
            return None
        for msg in conversation_history:
            if "role" not in msg or msg["role"] not in {"user", "assistant"}:
                raise ValueError(
                    "Each message must have a 'role' key with value 'user' or 'assistant'."
                )
        return conversation_history

    def to_query_params(self, is_stream: bool) -> "QueryParam":
        """Converts a QueryRequest instance into a QueryParam instance."""
        # Use Pydantic's `.model_dump(exclude_none=True)` to remove None values automatically
        request_data = self.model_dump(exclude_none=True, exclude={"query"})

        # Ensure `mode` and `stream` are set explicitly
        param = QueryParam(**request_data)
        param.stream = is_stream
        return param


class QueryResponse(BaseModel):
    response: str = Field(
        description="The generated response",
    )
