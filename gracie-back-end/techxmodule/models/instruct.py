import json

from termcolor import cprint, colored    # type: ignore
from typing import List, Optional, Any, Dict, Callable
from techxmodule.models.__core_skeleton__ import LLM


class InstructLLM(LLM):
    """
    Parent clas for Instruct Model
    """
    
    def __init__(self, name: str, 
                 max_chat_memory: int, 
                 session: Any, 
                 region_name: str):
        super().__init__(name, 
                         session, 
                         region_name, 
                         max_chat_memory)
        
    
    def _invoke_instruct_model(self, modelId: str,
                        build_payload_func, 
                        payload_params: list, 
                        streaming: bool = False) -> Dict:
        """A wrapper to invoke the instruct model, 
        allowing for custom payload construction with flexible arguments.
        
        Args:
            modelId (str): 
                The ID of the model to be invoked.
            build_payload_func (_type_): 
                A function that builds the payload.
            payload_params (list): 
                A list of parameters to be passed to the build_payload_func.
            streaming (bool, optional): 
                Whether to stream the response. Defaults to False.

        Returns:
            Dict: JSON response from the model.
        """
        
        payload = build_payload_func(*payload_params)
        return self._invoke_with_payload(modelId, payload, streaming)   
    
    
class LLama(InstructLLM):
    """
    LLama Meta model class that interacts with AWS Bedrock runtime service.
    """
    
    def __init__(self, model_name: str, 
                 session: Any, 
                 region_name: str, 
                 max_chat_memory: int = 0) -> None:
        """Initialize Llama model with specified version and session.

        Args:
            model_name (str): 
                Name of the LLama model to use. 
                Valid options are "3.2-1B", "3.2-3B", "3.2-11B", or "3.2-90B".
            session (Any): 
                An instance of the boto3 session object.
            region_name (str): 
                AWS region name where the service is run.
            max_chat_memory (int, optional): 
                Maximum number of chats the model can remember. Defaults to 0.
        """
        
        super().__init__("llama", max_chat_memory, session, region_name)
        self.modelId = self.__set_model_id(model_name)


    def invoke(self, messages: str, 
               max_token: int = 1024, 
               temperature: float = 0.15, 
               top_p: float = 0.8, 
               streaming: bool = False,
               verbose: bool = False) -> Dict:
        """Invoke the model

        Args:
            messages (str): 
                Prompt to ask the model.
            max_token (int, optional): 
                Max number of output token. Defaults to 1024.
            temperature (float, optional): 
                Defaults to 0.15.
            top_p (float, optional): 
                Defaults to 0.8.
            streaming (bool, optional): 
                Whether to stream the response. Defaults to False.
            verbose (bool, optional): 
                Show the metatdata, log. Defaults to False.

        Returns:
            Dict: the full response from the model.
        """
        invoke_result = self._invoke_instruct_model(
            self.modelId, 
            self.__build_llama_payload, 
            payload_params= [messages, max_token, temperature, top_p], 
            streaming=streaming)
        
        return self._parse_response(invoke_result, 
            [
                self.__process_streaming_llama_response, 
                self.__process_non_streaming_llama_response
            ], 
            debug=verbose)


    def __build_llama_payload(self, 
                              messages: str, 
                              max_token: int, 
                              temperature: float, 
                              top_p: float):
        """
        Build JSON payload for API request.
        """
        return {
            "prompt": messages,
            "max_gen_len": max_token,
            "temperature": temperature,
            "top_p": top_p,
        }
    

    def __process_streaming_llama_response(
            self, model_response: Any, debug: bool = False) -> Dict[str, Any]:
        """
        Stream and print model output in real-time.

        :param model_response: The HTTP response containing streamed JSON data
        :param debug: Flag to enable debugging information
        :return: Full stream response with text, tool data, and stop reason
        """
        full_response = ""
        
        for event in model_response["body"]:
            chunk = json.loads(event["chunk"]["bytes"])
            text = chunk["generation"]
            print(colored(text, "green"), end="", flush=True)
            full_response += text
        
        return full_response


    def __process_non_streaming_llama_response(
            self, model_response: Any, debug: bool = False) -> Dict[str, Any]:
        """
        Handle and process non-streaming model output.

        :param model_response: The response object from the model
        :param debug: Flag to enable debugging information
        :return: Processed response with tools and output
        """
        chunk = model_response["body"].read()
        text = chunk["generation"]
        print(colored(text, "green"), end="", flush=True)
        
        return text
        
    
    def __set_model_id(self, model_name: str) -> str:
        """
        Set model ID based on provided model name.

        @param model_name: Name of the Claude model to use.
        @return: Model ID corresponding to the chosen model.
        """
        model_map = {
            "3.2-1B": "us.meta.llama3-2-1b-instruct-v1:0",
            "3.2-3B": "us.meta.llama3-2-3b-instruct-v1:0",
            "3.2-11B": "us.meta.llama3-2-11b-instruct-v1:0",
            "3.2-90B": "us.meta.llama3-2-90b-instruct-v1:0"
        }
        if model_name not in model_map:
            raise ValueError(f"Invalid model name: {model_name}")
        return model_map[model_name]