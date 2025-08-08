from enum import Enum


class ChatInterface(Enum):
    # whatsapp = "whatsapp"  # Official WhatsApp Cloud API
    api = "api"  # Just send the response back.
    websocket = "websocket"  # Stream deltas via WebSocket
