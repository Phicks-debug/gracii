import tools, json
import xml.etree.ElementTree as ET

from termcolor import cprint, colored    # type: ignore
from typing import List, Optional, Any, Dict, Callable
from functools import wraps
from techxmodule import utils
from techxmodule.models.__core_skeleton__ import LLM
from techxmodule.messages import Image


class ChatLLM(LLM):
    """
    Parent clas for Chat Model
    """
    
    MEMORY_BUFFER = 4
    USER_ROLE = "user"
    ASSISTANT_ROLE = "assistant"
    TOOL_RESULT = "tool_result"

    
    def __init__(self, name: str, 
                 max_chat_memory: int, 
                 session: Any, 
                 region_name: str):
        """
        Initialize Chat model Instance
        
        :param name: Name of the LLM
        :param max_chat_memory: Maximum number of chats (plus buffer) the model can remember.
                                2 means 1 for user and 1 for assistant. Default is 0.
        :param session: Session object for API calls
        :param region_name: AWS region name
        """
        super().__init__(name, 
                         session, 
                         region_name, 
                         max_chat_memory+self.MEMORY_BUFFER)
    
    
    def manage_memory(func):
        """
        Decorator to manage memory by cleaning tag in questions and removing old messages.
        """
        
        def clean_tag_question(self):
            if len(self.memory.messages) > 2:
                try:
                    clean_text = utils.clean_tag(self.memory.messages[-3]["content"][0]["text"])
                    self.memory.messages[-3]["content"][0]["text"] = clean_text
                except (IndexError, KeyError) as e:
                    pass
    
        def removing_old_messages(self):
            while len(self.memory.messages) > self.memory.max_chat_message + 1:
                self.memory.messages.pop(0)
                if self.memory.messages and \
                    self.memory.messages[0]["role"] == self.USER_ROLE and \
                    self.memory.messages[0]["content"][0]["type"] != self.TOOL_RESULT:
                    break
        
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            clean_tag_question(self)
            func(self, *args, **kwargs)
            removing_old_messages(self)
        return wrapper
    
    
    @manage_memory
    def add_to_memory(self, role: str, 
                      text: str, 
                      images: Optional[List[Image]] = None) -> List[Dict]:
        """
        Add a new message to the memory.

        :param role: Role of the message sender ("user" or "assistant")
        :param text: Content of the message
        :param images: Optional list of associated images
        :return: Memory for the LLM
        """
        return self.memory.append_message(role, text, images)
            
    
    @manage_memory
    def add_tool_result_to_memory(self, results: List[Dict]) -> List[Dict]:
        """
        Add tool execution results to the memory.

        :param results: Results from tool execution
        :return: Memory for the LLM
        """
        return self.memory.append_tool_result(results)
            
    
    @manage_memory
    def add_tool_to_memory(self, tool_content: List[Dict]) -> List[Dict]:
        """
        Add tool-related content to the memory.

        :param tool_content: Content related to a tool
        :return: Memory for the LLM
        """
        return self.memory.append_tool(tool_content)
    

    def __assess_messages(self, messages: Optional[str] = None) -> List[str]:
    
        """
        Assess whether to use the provided messages or retrieve from internal memory.

        :param messages: string of user message, or None to use internal memory
        :return: user message formatted to payload
        """
        if not messages:
            if not self.memory.messages:
                raise AssertionError("Memory is empty. Please provide messages.")
            return self.memory.messages
        return [{"role": self.USER_ROLE, "content": messages}]
    

    def _invoke_chat_model(self, modelId: str, 
            build_payload_func, 
            payload_params: list, streaming: bool = False) -> Dict:
        """
        A wrapper to invoke the chat model, 
        allowing for custom payload construction with flexible arguments.

        @param modelId: The ID of the model to be invoked.
        @param build_payload_func: A function that builds the payload.
        @param payload_params: A list of parameters to be passed to the build_payload_func.
        @param streaming: Whether to stream the response (default is False).
        @return: JSON response from the model.
        """
        # Assess the messages in the payload (assuming the first item in payload_params is 'messages')
        payload_params[0] = self.__assess_messages(payload_params[0])

        # Call the build_payload_func with parameters unpacked from the list
        payload = build_payload_func(*payload_params)
        return self._invoke_with_payload(modelId, payload, streaming)


class Claude(ChatLLM):
    """
    Anthropic Claude model class that interacts with AWS Bedrock runtime service.
    """

    def __init__(self, model_name: str, 
                 session: Any, 
                 region: str, 
                 max_chat_memory = 0) -> None:
        """Initialize Claude model with specified version and session.

        Args:
            model_name (str): 
                Name of the Claude model to use.
                Valid options are "3-haiku", "3-sonnet", "3-opus", or "3.5-sonnet".
            session (Any): 
                An instance of the boto3 session object for creating a Bedrock client.
            region (str): 
                AWS region name where the service is run.
            max_chat_memory (int, optional): 
                Maximum number of chats (plus buffer) the model can remember. 
                Defaults to 0.
        """

        super().__init__("claude", 
                         max_chat_memory, 
                         session, 
                         region)
        self.modelId = self.__set_model_id(model_name)


    def invoke(self, messages: str = None, 
               system_prompt = "", 
               max_token = 4096,
               temperature = 0.15, 
               top_p = 0.8, 
               top_k = 50, 
               streaming = False,
               verbose = False) -> Dict[str, Any]:
        """Invoke the model

        Args:
            messages (str, optional): 
                Message prompt to the model
                (leave 'None' if use chat history).
                Defaults to None.
            system_prompt (str, optional): 
                Claude's role or personality prompt, system prompt.
                Defaults to "".
            max_token (int, optional): 
                Maximum number of output generate token.
                Defaults to 4096.
            temperature (float, optional):
                Sampling temperature for output variability.
                Defaults to 0.15.
            top_p (float, optional): 
                Nucleus sampling parameter for output diversity.
                Defaults to 0.8.
            top_k (int, optional): 
                Number of top tokens to consider for sampling.
                Defaults to 50.
            streaming (bool, optional): 
                Whether to stream the response.
                Defaults to False.
            verbose (bool, optional): 
                Whether to show log, tracking.
                Defaults to False.

        Returns:
            Dict: Json that contain full response output.
        """

        # Invoke model through bedrock runtime service
        invoke_result = self._invoke_chat_model(self.modelId, 
            self.__build_claude_payload, 
            payload_params=[messages, 
                            system_prompt, 
                            max_token, 
                            temperature, 
                            top_p, 
                            top_k], 
            streaming=streaming)
        
        # Return the parse response from the invoke result
        return self._parse_response(
            invoke_result, 
            [
                self.__process_streaming_claude_response, 
                self.__process_non_streaming_claude_response
            ], 
            debug=verbose)
    

    def tool_use(self, tools_list: list) -> list:
        """
        Invoke tools based on the provided list and process the results.

        @param tools_list: List of tools with 'name' and 'input' keys for invocation.
        @return: List of tool results containing tool_id and content.
        """
        results = []
        for tool in tools_list:
            cprint("Analyzing...", "cyan", attrs=["blink"])
            tool_function = getattr(tools, tool["name"])
            result = tool_function(**tool["input"])
            results.append({
                "tool_id": tool['id'],
                "content": self.__process_tool_result(result)
            })
        return results


    def __process_tool_result(self, result: dict) -> str:
        """
        Process tool result based on its type.

        @param result: Result returned from the tool.
        @return: Processed result string.
        """
        if result["type"] == "documents":
            cprint("Analyzing data from knowledge base...", "cyan")
            return self.__build_context_kb_prompt(result["text"])
        elif result["type"] == "data":
            cprint("Retrieving data from sources...", "cyan")
            return result["text"]
        elif result["type"] == "image":
            print("Image processing not yet implemented.")
            return ""
        elif result["type"] == "parameterError":
            cprint("Error using tool, retrying with different tools...", "red")
            return result["error"]
        return ""


    def __build_context_kb_prompt(self, retrieved_data: dict, 
                                  min_relevance: float = 0.5, 
                                  debug: bool = False) -> str:
        """
        Build XML context prompt from retrieved knowledge base data.

        @param retrieved_data: JSON object with retrieval results and metadata.
        @param min_relevance: Minimum relevance score for including context.
        @param debug: Flag to enable XML structure debugging.
        @return: XML string representing the context.
        """
        if not retrieved_data:
            return ""
        documents = ET.Element("documents")
        if retrieved_data["ResponseMetadata"]["HTTPStatusCode"] != 200:
            documents.text = "Error retrieving data. No context provided."
        else:
            for i, context in enumerate(retrieved_data["retrievalResults"]):
                if context["score"] < min_relevance:
                    break
                document = ET.SubElement(documents, "document", {"index": str(i + 1)})
                ET.SubElement(document, "source").text = utils.iterate_through_location(context["location"])
                ET.SubElement(document, "document_content").text = context["content"]["text"]
        if debug:
            ET.dump(documents)
        return ET.tostring(documents, encoding="unicode", method="xml")


    def __build_claude_payload(self, messages: list, 
                               system_prompt: str, 
                               max_token: float, 
                               temperature: float, 
                               top_p: float, 
                               top_k: int) -> str:
        """
        Build JSON payload for API request.

        @param messages: Messages to be sent to the model.
        @param system_prompt: System-level prompt for Claude.
        @param temperature: Sampling temperature for output.
        @param top_p: Nucleus sampling parameter.
        @param top_k: Number of top tokens for sampling.
        @return: JSON-encoded payload.
        """
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_token,
            "system": system_prompt,
            "messages": messages,
            "tools": self.tools,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "stop_sequences": []
        }


    def __process_streaming_claude_response(
            self, model_response: Any, 
            debug: bool = False) -> Dict[str, Any]:
        """
        Stream and print model output in real-time.

        :param model_response: The HTTP response containing streamed JSON data
        :param debug: Flag to enable debugging information
        :return: Full stream response with text, tool data, and stop reason
        """
        full_response = ""
        tool_input = ""
        tools_used = []
        body = []
        stop_reason = ""

        for event in model_response.get("body"):
            chunk = json.loads(event["chunk"]["bytes"])

            # Debugging info
            if chunk['type'] == 'message_delta':
                stop_reason = chunk['delta'].get('stop_reason', '')
                stop_sequence = chunk['delta'].get('stop_sequence', '')
                output_token = chunk['usage']['output_tokens']
                if debug:
                    print(f"\nStop reason: {stop_reason}")
                    print(f"Stop sequence: {stop_sequence}")
                    print(f"Output tokens: {output_token}\n")

            # Processing streaming content
            if chunk['type'] == 'content_block_delta':
                if chunk['delta']['type'] == 'text_delta':
                    text_chunk = chunk['delta']['text']
                    # print(colored(text_chunk, "green"), end="", flush=True)
                    yield text_chunk
                    full_response += text_chunk
                elif chunk['delta']['type'] == 'input_json_delta':
                    tool_input += chunk['delta']['partial_json']
            
            # Record the tool need to use
            if chunk['type'] == 'content_block_start' and chunk['index'] != 0:
                tool_index = chunk['index'] - 1
                tool_id = chunk['content_block']['id']
                tool_name = chunk['content_block']['name']
    
            # End of content block
            if chunk['type'] == 'content_block_stop':
                if chunk['index'] == 0:
                    body.append({"type": "text", "text": full_response})
                else:
                    try:
                        tool_input_json = json.loads(tool_input)
                    except json.JSONDecodeError:
                        tool_input_json = {}

                    tools_used.append({
                        "type": "tool_use",
                        "id": tool_id,
                        "name": tool_name,
                        "input": tool_input_json
                    })
                    body.append(tools_used[-1])
                    tool_input = ""

        return {
            "response": full_response,
            "tool": tools_used,
            "stop_reason": stop_reason,
            "body": body
        }


    def __process_non_streaming_claude_response(
            self, model_response: Any, 
            debug: bool = False) -> Dict[str, Any]:
        """
        Handle and process non-streaming model output.

        :param model_response: The response object from the model
        :param debug: Flag to enable debugging information
        :return: Processed response with tools and output
        """
        full_response = ""
        tools_used = []
        body = json.loads(model_response.get("body").read())

        for content_block in body["content"]:
            if content_block["type"] == "text":
                cprint(content_block["text"], "green")
                full_response += content_block["text"]
            elif content_block["type"] == "tool_use":
                tools_used.append({
                    "id": content_block["id"],
                    "name": content_block["name"],
                    "input": content_block["input"]
                })

        if debug:
            print(f"\nStop reason: {body['stop_reason']}")
            print(f"Stop sequence: {body['stop_sequence']}")
            print(f"Output tokens: {body['usage']['output_tokens']}")

        return {
            "response": full_response,
            "tool": tools_used,
            "stop_reason": body['stop_reason'],
            "body": body['content']
        }


    def __set_model_id(self, model_name: str) -> str:
        """
        Set model ID based on provided model name.

        @param model_name: Name of the Claude model to use.
        @return: Model ID corresponding to the chosen model.
        """
        model_map = {
            "3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
            "3-sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
            "3-opus": "us.anthropic.claude-3-opus-20240229-v1:0",
            "3.5-sonnet": "anthropic.claude-3-5-sonnet-20240620-v1:0"
        }
        if model_name not in model_map:
            raise ValueError(f"Invalid model name: {model_name}")
        return model_map[model_name]

    
    def build_context_prompt(self, prompt: str) -> str:
        """
        Constructs an XML representation of a context prompt.

        @param prompt: The context string to be included in the XML structure.
                       If empty, returns an empty string.

        @return: A string containing the XML representation of the context prompt.
        """
        if not prompt:
            return ""

        context_element = ET.Element("context")
        context_element.text = prompt
        return ET.tostring(context_element, encoding="unicode", method="xml")


    def build_cot_prompt(self, prompt: str = None) -> str:
        """
        Constructs an XML representation of a Chain of Thought (CoT) prompt.

        @param prompt: An optional string for the prompt. If not provided, a default template is used.

        @return: A string containing the XML representation of the CoT prompt.
        """
        default_prompt = (
            "Start the process by analyzing which actions need to do first "
            "from the <request> tag. Think what to do in <thinking> tag. "
            "If tools are required, list them with their parameters. "
            "After receiving tool results, continue analysis in the <middle_thinking> tag. "
            "Loop until the task is complete, and provide the final answer in the <answer> tag."
        )

        cot_content = prompt or default_prompt

        instructions_element = ET.Element("instructions")
        instructions_element.text = cot_content
        return ET.tostring(instructions_element, encoding="unicode", method="xml")


    def build_example_prompt(self, prompt: str) -> str:
        """
        Constructs an XML representation of an example prompt.

        @param prompt: The example prompt text. If empty, returns an empty string.

        @return: A string containing the XML representation of the example prompt.
        """
        if not prompt:
            return ""

        example_element = ET.Element("examples")
        example_element.text = prompt
        return ET.tostring(example_element, encoding="unicode", method="xml")


    def build_user_prompt(self, prompt: str) -> str:
        """
        Constructs an XML representation of a user prompt.

        @param prompt: The user prompt text.

        @return: A string containing the XML representation of the user prompt.
        """
        request_element = ET.Element("request")
        request_element.text = prompt
        return ET.tostring(request_element, encoding="unicode", method="xml")
    
