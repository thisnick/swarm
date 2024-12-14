from openai.types.chat import (
    ChatCompletionMessage,
    ChatCompletionChunk,
    ChatCompletion,
)
from openai import Stream
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
from typing import Any, Generator, List, Callable, TypedDict, Union, Optional, TypeAlias, Literal

# Third-party imports
from pydantic import BaseModel

from swarm.common.types import (
    Message,
    RetryState,
    MessageStreamingChunk,
    BaseAgent,
    BaseResponse,
    BaseResult
)

AgentFunction = Callable[..., Union[str, "Agent", dict, "Result"]]

AgentInstructions: TypeAlias = Union[str, Callable[..., str]]


class Agent(BaseAgent[AgentInstructions, AgentFunction]):
    pass

class Response(BaseResponse[Agent]):
    pass

class Result(BaseResult[Agent]):
    pass


DelimStreamingChunk = dict[Literal["delim"], Literal["start", "end"]]
ResponseStreamingChunk = dict[Literal["response"], Response]

class DeltaResponseStreamingChunk(TypedDict):
    partial_response: Response

StreamingResponse: TypeAlias = Generator[
  Union[
    DelimStreamingChunk,
    MessageStreamingChunk,
    ResponseStreamingChunk,
    DeltaResponseStreamingChunk,
  ],
  None,
  None
]
