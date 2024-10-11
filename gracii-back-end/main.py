import boto3.session
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import boto3
import json

from techxmodule.models.chat import Claude
from techxmodule.utils import real_time
from toolsdata import return_tool
from io import StringIO

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Replace with your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create the Claude LLM instance once, outside the request handler
llm = Claude("3.5-sonnet", boto3.Session(), "us-east-1", 10)
llm.tool_add(return_tool())
llm.memory.messages.clear()

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message", "")
    
    # System prompt or instructions to guide the LLM
    system_prompt = f"""
        You have access to the real time. You know what time it is right now.
        The current real time is: {real_time()}
        
        Your name is Gracii.
        DO NOT call yourself Claude or mention anything about Anthropic company.
        You are Gracii, you was created by Phicks, a genius AI engineering. Your nationality is French.
        You can speak well Vietnamese, English and French.
        Main language is English.
        You are very smart and decisive. You can do anything with high presision.
        Always double check your answer, and thinking throughly it.
        Remember that progress is made one step at a time. Stay determined and keep moving foward.
        """

    # Create a function that accumulates the response in a string
    def accumulate_response(user_message, system_prompt):
        full_response = StringIO()  # Using StringIO to accumulate the streamed output
        tool_input = StringIO()
        tools = []
        body = []
        
        # Add user message to memory
        llm.add_to_memory("user", user_message)
        
               # The main loop for generating the response
        while True:
            
            stop_reason = ""
            
            # Stream and yield chunks of the response
            result = llm.invoke(system_prompt=system_prompt, temperature=0.25, top_p=0.9, top_k=60, streaming=True)
            
            for event in result.get("body"):
                
                chunk = json.loads(event["chunk"]["bytes"])
                
                print(chunk)

                # Debugging info
                if chunk['type'] == 'message_delta':
                    stop_reason = chunk['delta'].get('stop_reason', '')
                    stop_sequence = chunk['delta'].get('stop_sequence', '')
                    output_token = chunk['usage']['output_tokens']

                # Processing streaming content
                if chunk['type'] == 'content_block_delta':
                    if chunk['delta']['type'] == 'text_delta':
                        text_chunk = chunk['delta']['text']
                        # print(colored(text_chunk, "green"), end="", flush=True)
                        yield text_chunk
                        full_response.write(text_chunk)
                    elif chunk['delta']['type'] == 'input_json_delta':
                        tool_input.write(chunk['delta']['partial_json'])
                
                # Record the tool need to use
                if chunk['type'] == 'content_block_start' and chunk['index'] != 0:
                    tool_index = chunk['index'] - 1
                    tool_id = chunk['content_block']['id']
                    tool_name = chunk['content_block']['name']
        
                # End of content block
                if chunk['type'] == 'content_block_stop':
                    if chunk['index'] == 0:
                        body.append({"type": "text", "text": full_response.getvalue()})
                    else:
                        try:
                            tool_input_json = json.loads(tool_input.getvalue())
                        except json.JSONDecodeError:
                            tool_input_json = {}

                        tools.append({
                            "type": "tool_use",
                            "id": tool_id,
                            "name": tool_name,
                            "input": tool_input_json
                        })
                        body.append(tools[-1])
                        tool_input = StringIO()
                
            # Check if the response requests a tool
            if stop_reason == "tool_use":
                
                # Add tool results to memory and continue generating responses
                llm.add_tool_to_memory(body)  # Add the tool request to memory
                tool_result = llm.tool_use(tools)
                llm.add_tool_result_to_memory(tool_result)  # Add tool result to memory
                
                # Re-invoke the LLM with the tool result added
                continue  # Go back to the LLM for further processing with the tool results
            
            # If the response is complete (end_turn), add to memory and break
            elif stop_reason == "end_turn":
                llm.add_to_memory("assistant", full_response.getvalue())
                break
                
            
    
    # Create and return a StreamingResponse using the generator
    return StreamingResponse(accumulate_response(user_message, system_prompt), media_type="text/markdown")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
