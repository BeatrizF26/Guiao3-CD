"""Message Broker"""
import enum
import socket
from typing import List, Any, Tuple
import selectors
from .protocol import CDProto, Serializer

class Broker:
    """Implementation of a PubSub Message Broker."""

    def __init__(self):
        """Initialize broker."""
        self.canceled = False
        self._host = "localhost"
        self._port = 5000

        self.topics = dict()    # dataionary that stores the last sent message in a topic
        self.subscriptions = dict() # dataionary that contains sets of tuples indicating which addresses are subscribed to which topic and which format they understand
                                    # {"topic1" : {(addr1, format1), (addr2, format2), ..., (addrN, formatN)},
                                    #  "topic2" : ...,
                                    #        ...
                                    #  "topicN" : ...}

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Criação da socket principal
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self._host, self._port))
        self.sock.listen(100)
        self.sock.setblocking(False)
        
        self.sel = selectors.DefaultSelector()  # Criação do seletor
        self.sel.register(self.sock, selectors.EVENT_READ, self.accept)

    def accept(self, sock, mask):
        """Função para aceitar um novo cliente"""

        (conn, addr) = sock.accept()  # Should be ready
        conn.setblocking(False)
        self.sel.register(conn, mask, self.read)

    def read(self, conn, mask):
        """Função para ler uma nova mensagem enviada pelo cliente"""
        try:
            msg, _format  = CDProto.recv_msg(conn)
        except:
            msg = None      # Caso não se consiga receber a mensagem, assume-se que o cliente desconectou-se

        # Se a mensagem for None, é porque o cliente se desconectou,
        # Então é preciso remover todos os tópicos, o cliente do seletor e fechar a conexão
        if msg is None:
            for topic in list(self.subscriptions.keys()):
                self.unsubscribe(topic, conn)

            self.sel.unregister(conn)
            conn.close()

        elif msg.data["command"] == "subscribe":
            self.subscribe(msg.data["topic"], conn, _format)
        
        elif msg.data["command"] == "publish":
            topic = msg.data["topic"]
            self.topics[topic] = msg.data["message"]

            #Obtém todos os tópicos que devem sofrer alterações
            parents = self.getParent(topic)

            for subscribed, subscribers in self.subscriptions.items():
                if not subscribed.startswith("/"):
                    subscribed = "/" + subscribed

                if subscribed in parents:
                    for sub in subscribers:
                        CDProto.send_msg(sub[0], msg, sub[1])

        elif msg.data["command"] == "request":
            msg = CDProto.requestTopicsReply(self.list_topics())
            CDProto.send_msg(conn, msg, _format)

        elif msg.data["command"] == "cancel":
            self.unsubscribe(msg.data["topic"], conn)

        else:
            print("Unknown message!")
        
    def list_topics(self) -> List[str]:
        """Returns a list of strings containing all topics containing values."""
        list = []
        for key in self.topics.keys():
            if key is not None:
                list.append(key)

        return list

    def get_topic(self, topic):
        """Returns the currently stored value in topic."""
        try:
            return self.topics.get(topic)
        
        except KeyError():
            print("ERROR: Topic not found!")

    def put_topic(self, topic, value):
        """Store in topic the value."""
        self.topics[topic] = value

        # Só para criar uma lista vazia de clientes no caso de ser um novo tópico
        if self.subscriptions.get(topic) is None:
            self.subscriptions[topic] = []


    def list_subscriptions(self, topic: str) -> List[Tuple[socket.socket, Serializer]]:
        """Provide list of subscribers to a given topic."""
        return self.subscriptions.get(topic)


    def subscribe(self, topic: str, address: socket.socket, _format: Serializer = None):
        """Subscribe to topic by client in address."""

        if self.subscriptions.get(topic) is None:
            self.subscriptions[topic] = []

        for subscribed in self.subscriptions.keys():
            if subscribed.startswith(topic):
                self.subscriptions[topic].append((address, _format))

    def unsubscribe(self, topic, address):
        """Unsubscribe to topic by client in address."""

        remove = False

        if (self.subscriptions.get(topic) is None):
            return
        
        for subscribed in self.subscriptions.keys():
            if subscribed.startswith(topic):
                for data in self.subscriptions[subscribed]:
                    if data[0] == address:
                        client = data
                        remove = True
                        break

                if remove:
                    self.subscriptions[subscribed].remove(client)

    def run(self):
        """Run until canceled."""

        while not self.canceled:
            events = self.sel.select()
            for key, mask in events:    # key = sock, mask = EVENT
                callback = key.data
                callback(key.fileobj, mask)

    def getParent(self, topic: str) -> List[str]:
        """Função para verificar a hierarquia dos tópicos"""
        parents = []

        if not topic.startswith("/"):
            topic = "/" + topic

        all_topics = topic.split("/")
        del all_topics[0]               # Remove a string vazia antes da primeira "/"
        num_parents = len(all_topics)

        # Cria todos os caminhos
        for i in range(num_parents):
            parent_str = ""
            for j in range(num_parents - i):
                parent_str += "/" + all_topics[j]
            parents.append(parent_str)
        
        return parents