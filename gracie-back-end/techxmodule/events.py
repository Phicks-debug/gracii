from typing import Any


class Event:
    
    def __init__(self, event_id: str, data: Any) -> None:
        self.id = event_id
        self.data = Any


class EventBus:
    
    def __init__(self) -> None:
        self.subscribers = {}
        
    def subscribe(self, event_type: str, callback) -> None:
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)
    
    def publish(self, event_type: str, data: Any) -> None:
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                callback(data)
