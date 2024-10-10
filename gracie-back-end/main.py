import boto3.session
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import boto3

from techxmodule.models.chat import Claude

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Replace with your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message", "")
    
    llm = Claude("3.5-sonnet", boto3.Session(), "us-east-1", 10)
    
    return StreamingResponse(llm.invoke(user_message, 
               "You are an expert code front end assistant, please thinking the question carefully before answer the question", 
               temperature=0.25, 
               top_p=0.9, 
               top_k=60, 
               streaming=True), media_type="markdown")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)