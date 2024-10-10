import tkinter as tk
from tkinter import simpledialog, messagebox
import requests

# Function to send prompt to the LLM API
def send_prompt():
    prompt = input_box.get("1.0", "end-1c")
    if prompt:
        # Here, send API request to LLM (replace with your API details)
        response = send_llm_request(prompt)
        show_response(response)
    else:
        messagebox.showinfo("Empty Prompt", "Please enter a prompt.")

# Function to send API request to the LLM
def send_llm_request(prompt):
    # Example LLM API request to OpenAI (replace with actual endpoint and API key)
    api_url = "https://api.openai.com/v1/completions"
    headers = {
        "Authorization": "Bearer YOUR_API_KEY",
        "Content-Type": "application/json"
    }
    data = {
        "model": "text-davinci-003",  # You can change the model here
        "prompt": prompt,
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data)
        response_data = response.json()
        return response_data['choices'][0]['text']
    except Exception as e:
        return f"Error: {str(e)}"

# Function to display response in another popup window
def show_response(response):
    response_window = tk.Toplevel(root)
    response_window.geometry("400x200+500+300")  # Popup window at a specific location
    response_label = tk.Label(response_window, text="Model Response:", font=("Arial", 12))
    response_label.pack(pady=10)
    response_box = tk.Text(response_window, wrap='word', height=5)
    response_box.pack(expand=True, fill='both', padx=10, pady=10)
    response_box.insert(tk.END, response)

# Create the main application window
root = tk.Tk()
root.title("LLM Prompt App")
root.geometry("300x100+1000+800")  # Place the window in the corner

# Input box for user prompt
input_label = tk.Label(root, text="Enter your prompt:", font=("Arial", 10))
input_label.pack(pady=5)
input_box = tk.Text(root, height=2, wrap='word')
input_box.pack(expand=True, fill='both', padx=10, pady=5)

# Button to send the prompt
send_button = tk.Button(root, text="Send", command=send_prompt)
send_button.pack(pady=5)

root.mainloop()
