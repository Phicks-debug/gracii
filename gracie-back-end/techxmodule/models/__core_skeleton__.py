import json

from typing import List, Any, Dict, Callable
from techxmodule.messages import ChatMessage
from termcolor import cprint    # type: ignore


class LLM():
    """
    Base class for Large Language Models (LLM) with memory management 
    and tool integration.
    """
    
    
    def __init__(self, name: str, 
                 session: Any, 
                 region_name: str,
                 max_chat_memory: int) -> None:
        self.name = name
        self.runtime = session.client("bedrock-runtime", 
                                      region_name=region_name)
        self.memory = ChatMessage(max_chat_message=max_chat_memory)
        self.tools: List[Any] = []
        self._is_streaming = False
    
    
    def tool_add(self, tool_list: list):
        """
        Add tool for the model to extend its capability
        
        :param tool_list: list of usable tools for the model
        """
        self.tools.extend(tool_list)
    
    
    def _invoke_with_payload(self, modelId: str, 
                              payload: Dict, 
                              streaming: bool) -> Dict:
        """
        Invoke the bedrock API to the model provided payload.
        """
        # Build the key words arguments
        invoke_kwargs = {
            "modelId": modelId,
            "accept": "application/json",
            "contentType": "application/json",
            "body": json.dumps(payload)
        }

        # Call the model based on streaming tag
        self._is_streaming = streaming
        if self._is_streaming:
            return self.runtime.invoke_model_with_response_stream(**invoke_kwargs)
        return self.runtime.invoke_model(**invoke_kwargs)

    
    def _parse_response(self, invoke_result: Any, 
                 process_response_func: List[Callable], 
                 debug: bool = False) -> Dict[str, Any]:
        
        """Process the model's response, 
            handling both streaming and non-streaming cases.
            
        Arg:
            invoke_result (Any): 
                Raw response from the model invocation.
            process_response_func (List[Callable]): 
                List of two functions, 
                one for streaming, 
                one for non-streaming
            debug (bool, optional): 
                Flag to enable debug mode.

        Raises:
            ValueError: 
                The list must contain exactly two functions.
            TypeError: 
                Both items in the list must be callable.

        Returns:
            Dict[str, Any]: Processed response
        """
        
        # Validation: Ensure only two functions with specific names
        if len(process_response_func) != 2:
            raise ValueError("The process_response_func list must contain exactly two functions.")
        
        # Check if the first function is named 'streaming' and second is 'non_streaming'
        streaming_func = process_response_func[0]
        non_streaming_func = process_response_func[1]
        
        if not callable(streaming_func) or not callable(non_streaming_func):
            raise TypeError("Both items in the process_response_func list must be callable.")
            
        try:
            if self._is_streaming:
                return streaming_func(invoke_result, debug)
            else:
                return non_streaming_func(invoke_result, debug)
        except Exception as e:
            cprint(f"Error processing response: {e}", "red")
            return None  