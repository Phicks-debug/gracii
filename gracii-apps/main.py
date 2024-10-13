import threading
import queue
import time

# Payload class to encapsulate data
class Payload:
    def __init__(self, data, sender=None, receiver=None):
        self.data = data
        self.sender = sender  # The Agent sending the message
        self.receiver = receiver  # The Agent receiving the message

    def __str__(self):
        return f"Payload from {self.sender} to {self.receiver}: {self.data}"

# Agent (Acts as an Event broker and processor)
class Agent(threading.Thread):
    def __init__(self, name, event_system):
        threading.Thread.__init__(self)
        self.name = name
        self.event_system = event_system
        self.message_queue = queue.Queue()
        self.subscribed_events = []

    def subscribe(self, event_name):
        self.subscribed_events.append(event_name)
        self.event_system.subscribe(event_name, self)

    def send_event(self, event_name, payload):
        print(f"{self.name} sending event '{event_name}' with payload: {payload}")
        self.event_system.publish(event_name, payload)

    def receive_event(self, event_name, payload):
        # Put incoming payload into the message queue for processing
        self.message_queue.put((event_name, payload))

    def run(self):
        while True:
            if not self.message_queue.empty():
                event_name, payload = self.message_queue.get()
                print(f"{self.name} received event '{event_name}' with payload: {payload}")
                self.process_payload(event_name, payload)
            time.sleep(1)

    def process_payload(self, event_name, payload):
        # Each agent can implement custom behavior when processing payloads
        print(f"{self.name} processing payload for event '{event_name}': {payload}")
        # Example of dynamic message forwarding to another agent
        if event_name == "event1":
            # Modify the payload and send it to another agent
            new_payload = Payload(data=f"Processed {payload.data}", sender=self.name, receiver="Agent2")
            self.send_event("event2", new_payload)

# Event-driven system that routes events between agents
class EventSystem:
    def __init__(self):
        self.subscribers = {}

    def subscribe(self, event_name, agent):
        if event_name not in self.subscribers:
            self.subscribers[event_name] = []
        self.subscribers[event_name].append(agent)

    def publish(self, event_name, payload):
        if event_name in self.subscribers:
            for agent in self.subscribers[event_name]:
                agent.receive_event(event_name, payload)

# Example usage of the system
if __name__ == "__main__":
    event_system = EventSystem()

    # Create Agents
    agent1 = Agent(name="Agent1", event_system=event_system)
    agent2 = Agent(name="Agent2", event_system=event_system)

    # Subscribe agents to events
    agent1.subscribe("event1")
    agent2.subscribe("event2")

    # Start agent threads
    agent1.start()
    agent2.start()

    # Agent1 sends an initial event
    initial_payload = Payload(data="Initial Message", sender="Agent1", receiver="Agent1")
    agent1.send_event("event1", initial_payload)

    # Let threads run for a while to process events
    time.sleep(2)

    # Join threads before exiting (for clean shutdown in this example)
    agent1.join(timeout=1)
    agent2.join(timeout=1)
    
    
