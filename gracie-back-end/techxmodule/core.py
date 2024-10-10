from techxmodule import utils
from typing import List, Dict


class Guardrail:
    
    def __init__(self, session) -> None:
        self.session = session
    
    def validate(self, user_input: str) -> bool:
        # Implement your input validation logic here
        # Return True if the input is valid, False otherwise
        return len(user_input.strip()) > 0


class Prompts:
    
    def __init__(self, model: any = None) -> None:
        """
        Initializes the Prompts class with an optional model.

        @param model: An optional model object. If provided, it should have a `name` attribute.
                      If no model is provided, `_prompt_type` is set to "None".

        @raises ValueError: If a model is provided but lacks a `name` attribute.
        """
        self.__model = model if model \
            and hasattr(model, "name") else None
        if not self.__model:
            self.__prompt_type = "None"
        else:
            self.__prompt_type = model.name


    def build(self, user: str, 
              context = "", 
              example= "",
              instruction: str = None) -> str:

        """Builds the final prompt 
        based on the specified model type.
        
        Args:
            user (str): 
                The main user input prompt.
            context (str):
                Context information. 
                Default is empty string.
            example (str):
                Example prompts for few-shot.
                Default is empty string.
            instruction (str):
                Chain of Thought prompt or instruction.
                Default is None.
        Returns:
            str: A combined prompt as a single string.
        """

        build_prompt_fn = {
            "claude": self.__build_claude_prompt,
            "llama": self.__build_llama_prompt,
        }.get(self.__prompt_type, 
              self.__build_default_prompt)

        return build_prompt_fn(
            user, 
            context, 
            example, 
            instruction)


    def __build_claude_prompt(self, 
                              user_prompt: str, 
                              context_prompt = "", 
                              example_prompt = "", 
                              instruction: str = None) -> str:
        """
        Builds a prompt specifically for the Claude model 
        using the utility functions from the model.
        """
        
        prompt = utils.combine_string([
            self.__model.build_context_prompt(context_prompt),
            self.__model.build_user_prompt(user_prompt),
            self.__model.build_cot_prompt(instruction),
            self.__model.build_example_prompt(example_prompt)
        ])
        
        return utils.sanitize_input(prompt)

    
    def __build_llama_prompt(self, 
                             user_prompt: str, 
                             context_prompt = "", 
                             example_prompt = "", 
                             instruction: str = None,
                             tools: List[Dict] = None) -> str:
        """
        Builds a prompt specifically for the Llama model 
        using the utility functions from the model.
        """
        
        def format(prompt, text, footer=""):
            if prompt:
                return utils.combine_string([
                text, f"{prompt}", footer
                ])
            else: return ""
            
        context = format(context_prompt,
                         """
                            Here is context:\n
                            --------------------\n
                         """, 
                         """
                            --------------------\n
                            End of the context.\n
                         """)
        example = format(example_prompt,
                         "Here is some examples:\n")
        tool_list = format(tools,
                      """
                        You are an expert in composing functions. You are given a set of possible functions.
                        Based on the question, you will need to make one or more function/tool calls to achieve the purpose.
                        If none of the function can be used, point it out. 
                        If the given question lacks the parameters required by the function, also point it out. 
                        You should only return the function call in tools call sections.

                        If you decide to invoke any of the function(s), you MUST put it in the format of [func_name1(params_name1=params_value1, params_name2=params_value2...), func_name2(params)]
                        You SHOULD NOT include any other text in the response.

                        Here is a list of functions in JSON format that you can invoke.
                      """)
        
        if self.__model.memory.max_chat_message > 0:
            history = """
            Here is the chat histories between human and assistant, inside <histories></histories> XML tags.
            
            <histories>
            {}
            </histories>
            """
        else: history = ""
        
        # Format prompt
        return f"""
            <|begin_of_text|><|start_header_id|>system<|end_header_id|>
            
            {instruction}
            {tool_list}
            {context}
            {example}
            {history}
            
            <|eot_id|><|start_header_id|>user<|end_header_id|>
            
            {user_prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>
        """
    

    def __build_default_prompt(self, 
                               user_prompt: str, 
                               context_prompt: str = "", 
                               example_prompt: str = "", 
                               instruction: str = None) -> str:
        """
        Builds a default prompt with no specific model optimizations.

        @return: Combined and sanitized default prompt.
        """
        prompt = utils.combine_string(
            [
                context_prompt, 
                user_prompt, 
                instruction, 
                example_prompt
            ])
        return utils.sanitize_input(prompt)


class Tools:
    """
    A utility class designed to manage and apply decorators to functions interacting with specific tools.

    This class provides a decorator generator to wrap functions with additional metadata 
    about the tool's action and data type.
    """

    def __init__(self) -> None:
        """
        Initializes the Tools class. Currently serves as a placeholder.
        """
        pass

    @staticmethod
    def tool(action: str, data_type: str):
        """
        Decorator generator that adds metadata to the result of the decorated function.

        @param action: The action the tool performs (e.g., "fetch_data").
        @param data_type: The type of data the tool returns (e.g., "text").

        @return: A decorator function that wraps the original function, adding metadata to its output.
        """
        def tool_decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    return {
                        "text": result,
                        "type": data_type,
                        "action": action
                    }
                except (TypeError, KeyError) as e:
                    return {
                        "error": f"Error using tool: {e}",
                        "type": "parameterError",
                        "action": action
                    }
            return wrapper
        return tool_decorator
