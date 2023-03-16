import random
from paho.mqtt import client as mqtt_client
import json


class MqttConnectionError(ConnectionError):
    def __init__(self, *args: object) -> None:
        super().__init__("Connection error with the MQTT broker", *args)


class MqttSendError(ConnectionError):
    def __init__(self, *args: object) -> None:
        super().__init__("Error sending message to MQTT broker", *args)


class MqttClient:
    def __init__(self, broker: str, topic: str, subscribe_callback, username: str | None = None, password: str | None = None, client_id: str | None = None) -> None:
        self._broker = broker
        self._port = 1883
        self._topic = "/gsog/shopping"  # TODO: settings
        self.__client_id = client_id
        if self.__client_id is None:
            self.__client_id = f'python-mqtt-{random.randint(0, 1000)}'
        self.__username = username
        self.__password = password
        self.__client: mqtt_client.Client | None = None
        self.__subscribe_callback = subscribe_callback

    @staticmethod
    def on_connect(client, userdata, flags, rc) -> None:
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code", rc)

    def publish(self, msg: str, topic: str | None = None) -> None:
        if self.__client is None:
            self.connect()
            if self.__client is None:
                raise MqttConnectionError()

        if topic is None:
            topic = self._topic

        result = self.__client.publish(topic, msg)
        status = result[0]
        if status != 0:
            raise MqttSendError()

    def subscribe(self) -> None:
        if self.__client is None:
            self.connect()
            if self.__client is None:
                raise MqttConnectionError()

        self.__client.subscribe(self._topic)
        self.__client.on_message = self.__subscribe_callback

    def connect(self) -> None:
        self.__client = mqtt_client.Client(self.__client_id)
        if self.__username:
            self.__client.username_pw_set(self.__username, self.__password)

        self.__client.on_connect = self.on_connect
        self.__client.connect(self._broker, self._port)
        self.__client.loop_start()

    def disconnect(self) -> None:
        if self.__client:
            print("Disconnecting from MQTT broker...")
            self.__client.loop_stop()
            self.__client.disconnect()

    def __del__(self) -> None:
        self.disconnect()


def sample2():

    broker = 'broker.hivemq.com'
    topic = "/gsog/shopping"
    username = None
    password = None

    def on_message(client, userdata, msg) -> None:
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
    client = MqttClient(broker, topic, on_message, username, password)
    client.connect()
    count = 0
    while True:
        text = input("Press enter to send a message... (q to quit)")
        if text == 'q':
            break

        count += 1
        msg_dict = {
            "dummy": "Hello there",
            "message": text,
            "counter": count,
        }
        msg = json.dumps(msg_dict, indent=4)
        client.publish(msg)

    print("Now subscribing...")
    client.subscribe()
    msg = input("enter message to send (& recieve?) (q to quit)\n")
    client.publish(msg)
    input("Press enter to quit...\n")


if __name__ == '__main__':
    sample2()
