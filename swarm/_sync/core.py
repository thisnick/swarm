# Code generated from codegen/templates/swarm/(sync)/core.py.jinja2. DO NOT EDIT MANUALLY!

# Standard library imports
import copy
import json
from collections import defaultdict
import time
from typing import (
    Any,
    Callable,
    Generator,
    List,
    Optional,
    Union,
    cast,
)
import time

# Package/library imports
from openai import OpenAI


# Local imports
from swarm.util import function_to_json, debug_print, merge_chunk, json_to_function_args
from .types import (
    Agent,
    AgentFunction,
    ChatCompletionChunk,
    ChatCompletion,
    ChatCompletionMessageToolCall,
    Function,
    Response,
    Result,
    RetryState,
    Stream,
    StreamingResponse,
    MessageStreamingChunk,
    Message,
)

__CTX_VARS_NAME__ = "context_variables"
RETRY_TIMES = [0, 5, 10, 30, 60]

class Swarm:
    def __init__(
        self,
        client=None,
        exponential_backoff: bool = False,
        retry_callback: Optional[Callable[[RetryState], Any]] = None,
    ):
        if not client:
            client = OpenAI()
        self.client = client
        self.exponential_backoff = exponential_backoff
        self.retry_callback = retry_callback

    def get_chat_completion(
        self,
        agent: Agent,
        history: List,
        context_variables: dict,
        model_override: str | None,
        stream: bool,
        debug: bool,
    ) -> ChatCompletion | Stream[ChatCompletionChunk]:
        context_variables = defaultdict(str, context_variables)
        instructions = (
            agent.instructions(context_variables)
            if callable(agent.instructions)
            else agent.instructions
        )
        # history contains "sender", which is unsupported
        history = [
            {
                k: v for k, v in message.items()
                if k not in ["sender", "tool_name"]
            } for message in history
        ]
        messages = [{"role": "system", "content": instructions}] + history
        debug_print(debug, "Getting chat completion for...:", messages)

        tools = [function_to_json(f) for f in agent.functions]
        # hide context_variables from model
        for tool in tools:
            params = tool["function"]["parameters"]
            params["properties"].pop(__CTX_VARS_NAME__, None)
            if __CTX_VARS_NAME__ in params["required"]:
                params["required"].remove(__CTX_VARS_NAME__)

        create_params = {
            "model": model_override or agent.model,
            "messages": messages,
            "tools": tools or None,
            "tool_choice": agent.tool_choice,
            "stream": stream,
        }

        if tools:
            create_params["parallel_tool_calls"] = agent.parallel_tool_calls

        return self.client.chat.completions.create(**create_params)

    def handle_function_result(self, result: Union[str, Agent, dict, Result], debug: bool) -> Result:
        match result:
            case Result() as result:
                return result

            case Agent() as agent:
                return Result(
                    value=json.dumps({"assistant": agent.name}),
                    agent=agent,
                )
            case _:
                try:
                    return Result(value=str(result))
                except Exception as e:
                    error_message = f"Failed to cast response to string: {result}. Make sure agent functions return a string or Result object. Error: {str(e)}"
                    debug_print(debug, error_message)
                    raise TypeError(error_message)

    def handle_tool_calls(
        self,
        tool_calls: List[ChatCompletionMessageToolCall],
        functions: List[AgentFunction],
        context_variables: dict,
        debug: bool,
    ) -> Response:
        function_map = {f.__name__: f for f in functions}
        partial_response = Response(
            messages=[], agent=None, context_variables={})

        assert partial_response.messages is not None, "partial_response.messages is None"

        for tool_call in tool_calls:
            name = tool_call.function.name
            # handle missing tool case, skip to next tool
            if name not in function_map:
                debug_print(debug, f"Tool {name} not found in function map.")
                partial_response.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "tool_name": name,
                        "content": f"Error: Tool {name} not found.",
                    }
                )
                continue
            args = json_to_function_args(function_map[name], json.loads(tool_call.function.arguments))
            debug_print(
                debug, f"Processing tool call: {name} with arguments {args}")

            func = function_map[name]
            # pass context_variables to agent functions
            if __CTX_VARS_NAME__ in func.__code__.co_varnames:
                args[__CTX_VARS_NAME__] = context_variables
            raw_result = function_map[name](**args)

            result: Result = self.handle_function_result(raw_result, debug)
            partial_response.messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "tool_name": name,
                    "content": result.value,
                }
            )
            partial_response.context_variables.update(result.context_variables)
            if result.agent:
                partial_response.agent = result.agent

        return partial_response

    def _get_streaming_completion_with_retry(
        self,
        active_agent: Agent,
        history: List[Message],
        context_variables: dict,
        model_override: Optional[str],
        debug: bool,
        message: dict
    ) -> StreamingResponse:
        tries = 0
        while True:
            try:
                completion = self.get_chat_completion(
                    agent=active_agent,
                    history=history,
                    context_variables=context_variables,
                    model_override=model_override,
                    stream=True,
                    debug=debug,
                )
                assert hasattr(completion, '__iter__') and hasattr(completion, '__next__'), "Expected generator for streaming completion"
                completion = cast(Stream[ChatCompletionChunk], completion)
                yielded_start = False

                for chunk in completion:
                    if not yielded_start:
                        yield {"delim": "start"}
                        yielded_start = True

                    chunk = cast(ChatCompletionChunk, chunk)
                    delta = cast(MessageStreamingChunk, chunk.choices[0].delta.model_dump())
                    if delta["role"] == "assistant":
                        delta["sender"] = active_agent.name
                    yield delta
                    to_merge = cast(dict, delta.copy())
                    to_merge.pop("role", None)
                    to_merge.pop("sender", None)
                    merge_chunk(message, to_merge)

                yield {"delim": "end"}
                break
            except Exception as e:
                if self.retry_callback:
                    self.retry_callback(
                        RetryState(
                            error=str(e),
                            tries=tries,
                            sleep_time=RETRY_TIMES[tries] if self.exponential_backoff else 0,
                        )
                    )
                tries += 1
                if tries >= len(RETRY_TIMES) or not self.exponential_backoff:
                    raise e
                time.sleep(RETRY_TIMES[tries])

    def run_and_stream(
        self,
        agent: Agent,
        messages: List[Message],
        context_variables: dict = {},
        model_override: Optional[str] = None,
        debug: bool = False,
        max_turns: int | float = float("inf"),
        execute_tools: bool = True,
    ) -> StreamingResponse:
        active_agent = agent
        context_variables = copy.deepcopy(context_variables)
        history = copy.deepcopy(messages)
        init_len = len(messages)

        while len(history) - init_len < max_turns:

            message = {
                "content": "",
                "sender": agent.name,
                "role": "assistant",
                "function_call": None,
                "tool_calls": defaultdict(
                    lambda: {
                        "function": {"arguments": "", "name": ""},
                        "id": "",
                        "type": "",
                    }
                ),
            }

            for chunk in self._get_streaming_completion_with_retry(
                active_agent=active_agent,
                history=history,
                context_variables=context_variables,
                model_override=model_override,
                debug=debug,
                message=message
            ):
                yield chunk

            message["tool_calls"] = list(
                message.get("tool_calls", {}).values())
            if not message["tool_calls"]:
                message["tool_calls"] = None
            debug_print(debug, "Received completion:", message)
            message["sender"] = active_agent.name
            history.append(cast(Message, message))

            if not message["tool_calls"] or not execute_tools:
                debug_print(debug, "Ending turn.")
                break

            # convert tool_calls to objects
            tool_calls = []
            for tool_call in message["tool_calls"]:
                function = Function(
                    arguments=tool_call["function"]["arguments"],
                    name=tool_call["function"]["name"],
                )
                tool_call_object = ChatCompletionMessageToolCall(
                    id=tool_call["id"], function=function, type=tool_call["type"]
                )
                tool_calls.append(tool_call_object)

            # handle function calls, updating context_variables, and switching agents
            partial_response = self.handle_tool_calls(
                tool_calls, active_agent.functions, context_variables, debug
            )
            yield {"partial_response": partial_response}
            history.extend(partial_response.messages)
            context_variables.update(partial_response.context_variables)
            if partial_response.agent:
                active_agent = partial_response.agent

        yield {
            "response": Response(
                messages=history[init_len:],
                agent=active_agent,
                context_variables=context_variables,
            )
        }

    def run(
        self,
        agent: Agent,
        messages: List,
        context_variables: dict = {},
        model_override: Optional[str] = None,
        stream: bool = False,
        debug: bool = False,
        max_turns: int | float = float("inf"),
        execute_tools: bool = True,
    ) -> Response | StreamingResponse:
        if stream:
            return self.run_and_stream(
                agent=agent,
                messages=messages,
                context_variables=context_variables,
                model_override=model_override,
                debug=debug,
                max_turns=max_turns,
                execute_tools=execute_tools,
            )
        active_agent = agent
        context_variables = copy.deepcopy(context_variables)
        history = copy.deepcopy(messages)
        init_len = len(messages)

        while len(history) - init_len < max_turns and active_agent:

            # get completion with current history, agent
            completion = self.get_chat_completion(
                agent=active_agent,
                history=history,
                context_variables=context_variables,
                model_override=model_override,
                stream=stream,
                debug=debug,
            )
            completion = cast(ChatCompletion, completion)
            message = completion.choices[0].message
            debug_print(debug, "Received completion:", message)
            message_json = message.model_dump()
            message_json["sender"] = active_agent.name
            history.append(message_json)

            if not message.tool_calls or not execute_tools:
                debug_print(debug, "Ending turn.")
                break

            # handle function calls, updating context_variables, and switching agents
            partial_response = self.handle_tool_calls(
                message.tool_calls, active_agent.functions, context_variables, debug
            )
            history.extend(partial_response.messages)
            context_variables.update(partial_response.context_variables)
            if partial_response.agent:
                active_agent = partial_response.agent

        return Response(
            messages=history[init_len:],
            agent=active_agent,
            context_variables=context_variables,
        )
