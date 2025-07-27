from enum import Enum


# Actions available after response generation
class Action(Enum):
    create_events = "create_events"
    delete_events = "delete_events"
    update_events = "update_events"
