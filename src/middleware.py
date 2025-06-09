"""Middleware to communicate with PubSub Message Broker."""
from collections.abc import Callable
from enum import Enum
from queue import LifoQueue, Empty
from typing import Any, Tuple
import socket
from .protocol import CDProto, CDProtoBadFormat, Serializer


class MiddlewareType(Enum):
    """Middleware Type."""

    CONSUMER = 1
    PRODUCER = 2


class Queue:
    """Representation of Queue interface for both Consumers and Producers."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        """Create Queue."""

        # Código Tiago
        self.topic = topic
        self.type = _type
        self.callback = None

        # Criar a socket
        self.socket_middleware = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_middleware.connect(("localhost", 5000))
        self.socket_middleware.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


    def push(self, value):
        """Sends data to broker."""
        pass

    def pull(self) -> Tuple[str, Any]:
        """Receives (topic, data) from broker.

        Should BLOCK the consumer!"""
    
        result = CDProto.recv_msg(self.socket_middleware)
        if result is None:
            return None

        msg, _format = result

        # Se for para fazer a lista de tópicos, recorre-se ao callback
        while (msg.data["command"] == "listReply"):
            self.callback(msg.data["list"])

            msg, _format = CDProto.recv_msg(self.socket_middleware)

        return (msg.data["topic"], msg.data.get("message"))


    def list_topics(self, callback: Callable):
        """Lists all topics available in the broker."""
        pass

    def cancel(self):
        """Cancel subscription."""
        pass

class JSONQueue(Queue):
    """Queue implementation with JSON based serialization."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        super().__init__(topic, _type)

        if self.type == MiddlewareType.CONSUMER:
            msg = CDProto.subscribe(self.topic)
            CDProto.send_msg(self.socket_middleware, msg, Serializer.JSON)

    def push(self, value):
        msg = CDProto.publish(self.topic, value)
        CDProto.send_msg(self.socket_middleware, msg, Serializer.JSON)
        
    def list_topics(self, callback):
        msg = CDProto.requestTopics()
        CDProto.send_msg(self.socket_middleware, msg, Serializer.JSON)

        self.callback = callback

    def cancel(self):
        msg = CDProto.cancel(self.topic)
        CDProto.send_msg(self.socket_middleware, msg, Serializer.JSON)


class XMLQueue(Queue):
    """Queue implementation with XML based serialization."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        super().__init__(topic, _type)

        if self.type == MiddlewareType.CONSUMER:
            msg = CDProto.subscribe(self.topic)
            CDProto.send_msg(self.socket_middleware, msg, Serializer.XML)

    def push(self, value):
        msg = CDProto.publish(self.topic, value)
        CDProto.send_msg(self.socket_middleware, msg, Serializer.XML)
        
    def list_topics(self, callback):
        msg = CDProto.requestTopics()
        CDProto.send_msg(self.socket_middleware, msg, Serializer.XML)

        self.callback = callback

    def cancel(self):
        msg = CDProto.cancel(self.topic)
        CDProto.send_msg(self.socket_middleware, msg, Serializer.XML)



class PickleQueue(Queue):
    """Queue implementation with Pickle based serialization."""

    def __init__(self, topic, _type=MiddlewareType.CONSUMER):
        super().__init__(topic, _type)

        if self.type == MiddlewareType.CONSUMER:
            msg = CDProto.subscribe(self.topic)
            CDProto.send_msg(self.socket_middleware, msg, Serializer.PICKLE)

    def push(self, value):
        msg = CDProto.publish(self.topic, value)
        CDProto.send_msg(self.socket_middleware, msg, Serializer.PICKLE)
        
    def list_topics(self, callback):
        msg = CDProto.requestTopics()
        CDProto.send_msg(self.socket_middleware, msg, Serializer.PICKLE)

        self.callback = callback

    def cancel(self):
        msg = CDProto.cancel(self.topic)
        CDProto.send_msg(self.socket_middleware, msg, Serializer.PICKLE)

