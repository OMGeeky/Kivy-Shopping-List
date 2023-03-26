import random
from typing import Callable, Optional, Tuple
from paho.mqtt import client as mqtt_client
import json


class MqttConnectionError(ConnectionError):
    def __init__(self, *args: object) -> None:
        super().__init__("Connection error with the MQTT broker", *args)


class MqttSendError(ConnectionError):
    def __init__(self, *args: object) -> None:
        super().__init__("Error sending message to MQTT broker", *args)

def _get_broker_and_port(broker: str, port: int):
        print('getting broker and port', broker, port)
              
        if ':' in broker:
            broker, port = broker.split(':') # type: ignore
            port = int(port)

        return broker, port

class MqttClient:
    def __init__(
        self,
        broker: str,
        port: int,
        topic: str,
        subscribe_callback: Callable[[dict, str], None],
        username: Optional[str]  = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> None:
        self.set_target(broker, topic, port, username, password)
        if client_id is None:
            self.__client_id = f"python-mqtt-{random.randint(0, 1000)}"
        self.__client: Optional[mqtt_client.Client] = None
        self.__subscribe_callback = subscribe_callback

    def set_target(self, broker: str, topic:str, port: int, username: Optional[str] = None, password: Optional[str] = None):
        broker, port = _get_broker_and_port(broker, port)
        self.__broker = broker
        self.__port = port
        self.__topic = topic
        self.__username = username
        self.__password = password

    def parse_callback(self, msg, callback: Optional[Callable]):

        if callback is None:
            callback = self.__subscribe_callback
        x = json.loads(msg.payload.decode())
        callback(x, msg.topic)

    @staticmethod
    def on_connect(_client, _userdata, _flags, rc) -> None:
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code", rc)

    def publish(self, msg: dict, topic: Optional[str] = None, retain: bool = True) -> None:
        if self.__client is None:
            self.connect()
            if self.__client is None:
                raise MqttConnectionError()

        if topic is None:
            topic = self.__topic

        msg_str = json.dumps(msg)
        result = self.__client.publish(topic, msg_str, retain=retain)
        status = result[0]
        if status != 0:
            raise MqttSendError()

    def subscribe(self, callback=None) -> None:
        if self.__client is None:
            self.connect()
            if self.__client is None:
                raise MqttConnectionError()

        self.__client.subscribe(self.__topic)
        self.__client.on_message = lambda _client, _userdata, msg: self.parse_callback(msg, callback)

    def connect(self) -> None:
        self.__client = mqtt_client.Client(self.__client_id)
        if self.__username:
            self.__client.username_pw_set(self.__username, self.__password)

        self.__client.on_connect = self.on_connect
        print("Connecting to MQTT broker...")
        print(self.__broker, self.__port)
        self.__client.connect(self.__broker, self.__port)
        self.__client.loop_start()

    def disconnect(self) -> None:
        if self.__client:
            print("Disconnecting from MQTT broker...")
            self.__client.loop_stop()
            self.__client.disconnect()

    def __del__(self) -> None:
        self.disconnect()


def sample2():

    broker = "broker.hivemq.com"
    topic = "/gsog/shopping"
    username = None
    password = None

    def on_message(msg: dict, topic: str) -> None:
        print(f"Received `{msg}` from `{topic}` topic")

    client = MqttClient(broker=broker, port=1883,topic=topic,subscribe_callback= on_message,username= username,password= password)
    client.connect()
    count = 0
    while True:
        text = input("Press enter to send a message... (q to quit)")
        if text == "q":
            break

        count += 1
        msg_dict = {
            "dummy": "Hello there",
            "message": text,
            "counter": count,
        }
        # msg = json.dumps(msg_dict, indent=4)
        msg = msg_dict
        client.publish(msg)

    print("Now subscribing...")
    client.subscribe()
    
    input("Press enter to quit...\n")


if __name__ == "__main__":
    sample2()
