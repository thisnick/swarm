# Code generated from codegen/templates/swarm/(sync)/types.py.jinja2. DO NOT EDIT MANUALLY!


from pydantic import BaseModel
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
    Coroutine,
    Dict,
)

Message : TypeAlias = Dict[Literal[
    "content",
    "sender",
    "role",
    "function_call",
    "tool_calls",
    "tool_call_id",
    "tool_name",
    "audio",
    "refusal",
], Any]


class RetryState(BaseModel):
  tries: int = 0
  sleep_time: int = 0
  error: str = ""

AsyncAgentFunction = Callable[..., Coroutine[Any, Any, Union[str, "AsyncAgent", dict, "AsyncResult"]]]
AsyncAgentInstructions: TypeAlias = Union[str, Callable[..., Coroutine[Any, Any, str]]]

class AsyncAgent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o"
    instructions: AsyncAgentInstructions = "You are a helpful agent."  # type: ignore
    functions: List[AsyncAgentFunction] = []
    tool_choice: Optional[str] = None
    parallel_tool_calls: bool = True

class AsyncResponse(BaseModel):
    messages: List[Message] = []
    agent: Optional[AsyncAgent] = None
    context_variables: dict = {}


class AsyncResult(BaseModel):
    """
    Encapsulates the possible return values for an agent function.

    Attributes:
        value (str): The result value as a string.
        agent (AsyncAgent): The agent instance, if applicable.
        context_variables (dict): A dictionary of context variables.
    """

    value: str = ""
    agent: Optional[AsyncAgent] = None
    context_variables: dict = {}


AsyncDelimStreamingChunk = dict[Literal["delim"], Literal["start", "end"]]
AsyncResponseStreamingChunk = dict[Literal["response"], AsyncResponse]

class AsyncDeltaResponseStreamingChunk(TypedDict):
    partial_response: AsyncResponse

class AsyncMessageStreamingChunk(TypedDict):
    content: Any
    sender: str
    role: Literal["system", "user", "assistant", "tool"]
    tool_calls: List[dict[Literal["id", "function", "type"], Any]]
    function_call: None


AsyncStreamingResponse: TypeAlias = AsyncGenerator[
    Union[
        AsyncDelimStreamingChunk,
        AsyncMessageStreamingChunk,
        AsyncResponseStreamingChunk,
        AsyncDeltaResponseStreamingChunk,
    ],
    None,
    
]