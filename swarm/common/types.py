from typing import Any, Dict, List, Literal, Optional, TypeAlias, TypedDict, TypeVar, Generic
from pydantic import BaseModel

# Define generic type variables
TAgentInstructions = TypeVar('TAgentInstructions')
TAgentFunction = TypeVar('TAgentFunction')
TAgent = TypeVar('TAgent')

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

class MessageStreamingChunk(TypedDict):
    content: Any
    sender: str
    role: Literal["system", "user", "assistant", "tool"]
    tool_calls: List[dict[Literal["id", "function", "type"], Any]]
    function_call: None

class BaseAgent(BaseModel, Generic[TAgentInstructions, TAgentFunction]):
  name: str = "Agent"
  model: str = "gpt-4o"
  instructions: TAgentInstructions = "You are a helpful agent."  # type: ignore
  functions: List[TAgentFunction] = []
  tool_choice: Optional[str] = None
  parallel_tool_calls: bool = True

class BaseResponse(BaseModel, Generic[TAgent]):
    messages: List[Message] = []
    agent: Optional[TAgent] = None
    context_variables: dict = {}

class BaseResult(BaseModel, Generic[TAgent]):
    """
    Encapsulates the possible return values for an agent function.

    Attributes:
        value (str): The result value as a string.
        agent (Agent): The agent instance, if applicable.
        context_variables (dict): A dictionary of context variables.
    """

    value: str = ""
    agent: Optional[TAgent] = None
    context_variables: dict = {}
