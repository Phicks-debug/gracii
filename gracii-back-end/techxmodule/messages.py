class Image:
    """
    An Image object class to represent an image with type, media type, and data.
    """
    def __init__(self, type: str, media_type: str, data: str) -> None:
        self.type = type
        self.media_type = media_type
        self.data = data


class ChatMessage: 
    """
    A class that can store and handle images and text messages
    
    @param max_chat_message: maximum number of internal chat message (affect the model recall memory)
    """
    
    def __init__(self, max_chat_message: int=10) -> None:
        self.messages = []
        self.max_chat_message = max_chat_message
    

    def append_message(self, role :str, text: str, images: list[Image]|None=None) -> list:
        """
        Adds a message to the chat, including optional text and images.
        
        This method constructs a message dictionary that includes a role, text content, and optional images.
        The message is then appended to the `messages` list.
        
        @param role: A string indicating the role of the sender (e.g., 'user', 'system', 'assistant').
        @param text: A string containing the text of the message to be added.
        @param images: An optional list of Image objects to be included with the message. If provided,
                    each image should be accompanied by a descriptive text label, such as "Image 1:", 
                    "Image 2:", etc. If no images are provided, the message will contain only text.
        
        @return: A list of messages with the newly added message included.
        """
        content = []

        content = self._add_image(content, images)
        content = self._add_text(content, text)

        # Append the constructed message to the messages list
        self.messages.append({
            "role": role,
            "content": content
        })
        
        return self.messages
    
    
    def append_tool(self, tool_content) -> list:
        
        self.messages.append({
            "role": "assistant",
            "content": tool_content
        })
        
        return self.messages
    
    
    def append_tool_result(self, result_list: list) -> list:
        
        container_list = []
        
        for result in result_list:

            content = []

            content = self._add_text(content, result["content"])
            
            container_list.append({
                "type": "tool_result",
                "tool_use_id": result["tool_id"],
                "content": content
            })
        
        # Append the constructed message to the messages list
        self.messages.append({
            "role": "user",
            "content": container_list
        })
        
        return self.messages
    
    
    def _purify_recent_question(self) -> None:
        """
        Extracts the most recent chat message from the 'user' role and clears every other tag 
        except the <request> tag.
        This modifies the message content in place.
        """
        
        # Iterate through the messages in reverse to find the most recent 'user' message
        for message in reversed(self.messages):
            
            if message['role'] == 'user':
                
                purified_text = self._retain_request_tag(message['content'])
                
                # Update the content with the purified text
                
                message['content'] = [{
                    "type": "text",
                    "text": purified_text
                }]
                break


    def _retain_request_tag(self, content: list) -> str:
        """
        Retains only the <request> tag in the content, removing all other tags.
        
        @param content: A list of dictionaries representing the content of a message.
        @return: A string with only the <request> tag retained.
        """
        purified_text = ""
        
        for item in content:
            
            if item['type'] == 'text':
                text = item['text']
                
                # Retain only <request> tags and remove everything else
                start_tag = "<request>"
                end_tag = "</request>"
                
                start_idx = text.find(start_tag)
                end_idx = text.find(end_tag, start_idx)
                
                if start_idx != -1 and end_idx != -1:
                    purified_text += text[start_idx:end_idx + len(end_tag)]
        
        return purified_text
        
    
    def _add_image(self, content: list, images: list[Image]|None) -> list:
        """
        Add images to content with appropriate labels
        """
        
        if images:
            for index, image in enumerate(images, start=1):
                content.append({
                    "type": "text",
                    "text": f"Image {index}:"
                })
                content.append({
                    "type": "image",
                    "source": {
                        "type": image.type,
                        "media_type": image.media_type,
                        "data": image.data,
                    },
                })
        
        return content
    
    
    def _add_text(self, content: list, text: str) -> list:
        """
        Add text message to content
        """
        
        content.append({
            "type": "text",
            "text": text
        })
        
        return content