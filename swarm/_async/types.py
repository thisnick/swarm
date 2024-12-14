from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionChunk,
    ChatCompletion,
)
from openai import AsyncStream
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
from typing import (
    Any,
    AsyncGenerator,
    List,
    Callable,
    TypedDict,
    Union,
    Optional,
    TypeAlias,
    Literal,
    Coroutine
)

# Third-party imports
from pydantic import BaseModel

from swarm.common.types import (
    Message,
    RetryState,
    MessageStreamingChunk as AsyncMessageStreamingChunk,
    BaseAgent,
    BaseResponse,
    BaseResult
)

AsyncAgentFunction = Callable[..., Coroutine[Any, Any, Union[str, "AsyncAgent", dict, "AsyncResult"]]]

AsyncAgentInstructions: TypeAlias = Union[str, Callable[..., Coroutine[Any, Any, str]]]


class AsyncAgent(BaseAgent[AsyncAgentInstructions, AsyncAgentFunction]):
    pass

class AsyncResponse(BaseResponse[AsyncAgent]):
    pass

class AsyncResult(BaseResult[AsyncAgent]):
    pass


AsyncDelimStreamingChunk = dict[Literal["delim"], Literal["start", "end"]]
AsyncResponseStreamingChunk = dict[Literal["response"], AsyncResponse]

class DeltaAsyncResponseStreamingChunk(TypedDict):
    partial_response: AsyncResponse

AsyncStreamingResponse: TypeAlias = AsyncGenerator[
  Union[
    AsyncDelimStreamingChunk,
    AsyncMessageStreamingChunk,
    AsyncResponseStreamingChunk,
    DeltaAsyncResponseStreamingChunk,
  ],
  None
]
