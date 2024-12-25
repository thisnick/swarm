# Code generated from codegen/templates/swarm/(sync)/types.py.jinja2. DO NOT EDIT MANUALLY!


from pydantic import BaseModel
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
from typing import (
    Any,
    Generator,
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

AgentFunction = Callable[..., Union[str, "Agent", dict, "Result"]]
AgentInstructions: TypeAlias = Union[str, Callable[..., str]]

class Agent(BaseModel):
    name: str = "Agent"
    model: str = "gpt-4o"
    instructions: AgentInstructions = "You are a helpful agent."  # type: ignore
    functions: List[AgentFunction] = []
    tool_choice: Optional[str] = None
    parallel_tool_calls: bool = True

class Response(BaseModel):
    messages: List[Message] = []
    agent: Optional[Agent] = None
    context_variables: dict = {}


class Result(BaseModel):
    """
    Encapsulates the possible return values for an agent function.

    Attributes:
        value (str): The result value as a string.
        agent (Agent): The agent instance, if applicable.
        context_variables (dict): A dictionary of context variables.
    """

    value: str = ""
    agent: Optional[Agent] = None
    context_variables: dict = {}


DelimStreamingChunk = dict[Literal["delim"], Literal["start", "end"]]
ResponseStreamingChunk = dict[Literal["response"], Response]

class DeltaResponseStreamingChunk(TypedDict):
    partial_response: Response

class MessageStreamingChunk(TypedDict):
    content: Any
    sender: str
    role: Literal["system", "user", "assistant", "tool"]
    tool_calls: List[dict[Literal["id", "function", "type"], Any]]
    function_call: None


StreamingResponse: TypeAlias = Generator[
    Union[
        DelimStreamingChunk,
        MessageStreamingChunk,
        ResponseStreamingChunk,
        DeltaResponseStreamingChunk,
    ],
    None,
    None,
]