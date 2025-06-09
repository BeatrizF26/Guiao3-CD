"""Protocol for chat server - Computação Distribuida Assignment 3."""
import json
import xml.etree.ElementTree as ET
import pickle
from datetime import datetime
from socket import socket
import enum

class Serializer(enum.Enum):
    """Possible message serializers."""

    JSON = 0
    XML = 1
    PICKLE = 2

class Message:
    """Message Type."""
    def __init__(self, command: str):
        self.data = {"command" : command}

    
class SubscribeTopicMessage(Message):
    """Message to subscribe to a topic."""
    # Aqui ainda não é preciso ter em conta o formato que a mensagem tem, isso só interessa na send_msg e recv_msg
    def __init__(self, topic: str):
        super().__init__("subscribe")
        self.data["topic"] = topic

class PublishTopic(Message):
    """Message to publish a message in a topic."""
    # Mesma coisa de cima, ainda não interessa o formato da mensagem
    def __init__(self, topic: str, msg: str):
        super().__init__("publish")
        self.data["topic"] = topic
        self.data["message"] = msg


class RequestTopics(Message):
    """Message to request a list of all topics."""   
    # Também ainda não interessar o formato da mensagem
    def __init__(self):
        super().__init__("request")

class RequestTopicsReply(Message):
    """Message to list topics"""
    def __init__(self, topics: list):
        super().__init__("requestTopicsReply")
        self.data["list": topics]

class CancelTopicMessage(Message):
    """Message to cancel messages from a topic."""
    # Também ainda não vai interessar o formato da mensagem
    def __init__(self, topic: str):
        super().__init__("cancel")
        self.data["topic": topic]

class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def subscribe(cls, topic: str) -> SubscribeTopicMessage:
        """Creates a SubscribeTopicMessage object."""
        return SubscribeTopicMessage(topic)

    @classmethod
    def publish(cls, topic: str, message: str) -> PublishTopic:
        """Creates a PublishTopic object."""
        return PublishTopic(topic, message)

    @classmethod
    def requestTopics(cls) -> RequestTopics:
        """Creates a RequestTopics object."""
        return RequestTopics()

    @classmethod
    def cancel(cls, topic: str) -> CancelTopicMessage:
        """Creates a CancelTopicMessage object."""
        return CancelTopicMessage(topic)
    
    # É preciso uma nova mensagem para ter uma lista dos tópicos a responder
    @classmethod
    def requestTopicsReply(cls, topics: list) -> CancelTopicMessage:
        """Creates a CancelMessage object."""
        return RequestTopicsReply(topics)

    @classmethod
    def send_msg(cls, connection: socket, msg: Message, msg_format = Serializer):
        """Sends through a connection a Message object."""

        # Verifica o formato em que a mensagem foi passada
        if msg_format == Serializer.JSON:
            msg = json.dumps(msg.data)

        elif msg_format == Serializer.XML:
            root = ET.Element("Message")

            for key, value in msg.data.items():
                child = ET.SubElement(root, key)
                child.text = str(value)

            msg = ET.tostring(root, encoding='unicode')

        elif msg_format == Serializer.PICKLE:
            msg = pickle.dumps(msg.data)

        else:
            raise CDProtoBadFormat(msg)
        
        # Converte para bytes se ainda for string
        if not isinstance(msg, bytes):
            msg = msg.encode()

        msg_format_encoded = msg_format.value.to_bytes(1, byteorder='big')
        msg_size = len(msg).to_bytes(2, byteorder='big')
        
        connection.send(msg_size + msg_format_encoded + msg)

    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""

        # Recebe os outros 2 primeiros bytes com o tamanho que a mensagem tem
        header = connection.recv(2)
        if not header:
            return None  # Ligação fechada

        size = int.from_bytes(header, byteorder='big')

        if size == 0:
            return None

        header = connection.recv(1)
        if not header:
            return None

        msg_format = int.from_bytes(header, byteorder='big')

        msg = connection.recv(size)
        if not msg:
            return None

        if Serializer(msg_format) == Serializer.JSON:
            data = json.loads(msg.decode())
            _format = Serializer.JSON

        elif Serializer(msg_format) == Serializer.XML:
            root = ET.fromstring(msg)
            data = {child.tag: child.text for child in root}
            _format = Serializer.XML

        elif Serializer(msg_format) == Serializer.PICKLE:
            data = pickle.loads(msg)
            _format = Serializer.PICKLE

        else:
            raise CDProtoBadFormat(msg)

        command = data["command"]

        if command == "subscribe":
            return (SubscribeTopicMessage(data["topic"]), _format)
        elif command == "publish":
            return (PublishTopic(data["topic"], data["message"]), _format)
        elif command == "request":
            return (RequestTopics(), _format)
        elif command == "cancel":
            return (CancelTopicMessage(data["topic"]), _format)
        elif command == "requestTopicsReply":
            return (RequestTopicsReply(data["list"]), _format)
        else:
            raise CDProtoBadFormat(msg)

class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")