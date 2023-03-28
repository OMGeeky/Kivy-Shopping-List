import random
from typing import Callable, Optional
from kivymd.toast import toast
from paho.mqtt import client as mqtt_client
import json

def _get_broker_and_port(broker: str, port: int) -> tuple[str, int]:
    """
    Teilt die Broker-Adresse in Broker und Port auf.
    Wenn der Port in der Broker-Adresse angegeben ist, wird er aus der Broker-Adresse entfernt und
    der Port-Parameter ignoriert.

    :param broker: Der Hostname oder die IP-Adresse des Brokers (kann auch Port enthalten) als
    ``str``.
    :param port: Der Port als ``int`` der verwendet wird, wenn der Port nicht in der Broker-Adresse
    angegeben ist.
    :return: (broker, port) als Tuple.
    """
    print("getting broker and port", broker, port)

    if ":" in broker:
        broker, port = broker.split(":")  # type: ignore
        port = int(port)

    return broker, port


class MqttClient:
    """
    Klasse zum Verbinden mit einem MQTT-Broker.
    """
    def __init__(
        self,
        broker: str,
        port: int,
        topic: str,
        subscribe_callback: Callable[[dict, str], None],
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None,
    ) -> None:
        self.__connection_error = False
        self.set_target(broker, topic, port, username, password)
        if client_id is None:
            self.__client_id = f"python-mqtt-{random.randint(0, 1000)}"
        self.__client: Optional[mqtt_client.Client] = None
        self.__subscribe_callback = subscribe_callback

    def set_target(
        self,
        broker: str,
        topic: str,
        port: int,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Setzt die Verbindungsdaten für den MQTT-Broker.

        :param broker: Die Adresse des Brokers als ``str``.
        :param topic: Die Topic ``str``, die der Client standardmäßig verwendet.
        :param port: Port des Brokers als ``int``, kann auch durch : in der Broker-Adresse
        angegeben werden.
        :param username: Username als ``str`` zum Verbinden mit dem Broker.
        :param password: Passwort als ``str`` zum Verbinden mit dem Broker.
        """
        broker, port = _get_broker_and_port(broker, port)
        self.__broker = broker
        self.__port = port
        self.__topic = topic
        self.__username = username
        self.__password = password

    def parse_callback(self, msg, callback: Optional[Callable]):
        """
        Verarbeitet die empfangenen Nachrichten und ruft die angegebene Callback-Funktion auf.

        :param msg: Die Nachricht als ``str``, die empfangen wurde.
        :param callback: [optional] Die Callback-Funktion als ``Callable``, die aufgerufen werden
        soll (wenn nicht angegeben wird die Callback-Funktion der Klasse verwendet).
        """
        if callback is None:
            callback = self.__subscribe_callback
        x = json.loads(msg.payload.decode())
        callback(x, msg.topic)

    @staticmethod
    def on_connect(return_code: int) -> None:
        """
        Wird aufgerufen, wenn eine Verbindung zum MQTT-Broker hergestellt wurde.
        Gibt lediglich eine Meldung aus.

        :param return_code: Mitgabe als ``int``, wodurch entschieden wird, ob die Verbindung
        erfolgreich war.
        """
        if return_code == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code", return_code)

    def publish(
        self, msg: dict, topic: Optional[str] = None, retain: bool = True
    ) -> None:
        """
        Sendet eine Nachricht an den MQTT-Broker.

        :param msg: Die zu sendenden Daten als ``dict`` (wird automatisch in JSON umgewandelt).
        :param topic: [optional] Die Topic als ``str`` an welche die Nachricht gesendet werden soll
        (wenn nicht angegeben wird die topic der Klasse verwendet).
        :param retain: Ob bei der Nachricht die retain-Flag gesetzt werden soll, als ``bool``.
        """
        if self.__client is None:
            print("publish called but mqtt-client is None", self)
            return

        if topic is None:
            topic = self.__topic

        msg_str = json.dumps(msg)
        result = self.__client.publish(topic, msg_str, retain=retain)
        status = result[0]
        if status != 0:
            print("Failed to send message to MQTT broker", status, self)
            toast("Failed to send message to MQTT broker")

    def subscribe(self, callback=None) -> None:
        """
        Abonniert die Topic der Klasse und ruft die angegebene Callback-Funktion auf, wenn eine
        Nachricht empfangen wird.

        :param callback: Die Callback-Funktion als ``Callable``, die aufgerufen werden soll
        (wenn nicht angegeben, wird die Callback-Funktion der Klasse verwendet).
        """
        if self.__connection_error:
            return

        if self.__client is None:
            print("subscribe called but mqtt-client is None", self)
            return

        self.__client.subscribe(self.__topic)
        self.__client.on_message = lambda _client, _userdata, msg: self.parse_callback(
            msg, callback
        )

    def connect(self) -> None:
        """
        Verbindet mit dem MQTT-Broker
        """
        self.__client = mqtt_client.Client(self.__client_id)
        if self.__username:
            print("setting username and password")
            self.__client.username_pw_set(self.__username, self.__password)

        self.__client.on_connect = lambda _client, _userdata, _flags, return_code: MqttClient.on_connect(return_code)
        print("Connecting to MQTT broker...")
        print("broker:", self.__broker, "port:", self.__port)
        try:
            self.__client.connect(host=self.__broker, port=self.__port)
            self.__client.loop_start()
            self.__connection_error = False
        except Exception as e:
            self.__connection_error = True
            print("Failed to connect to MQTT broker", e)
            toast("Failed to connect to MQTT broker")

    def disconnect(self) -> None:
        """
        Trennt die Verbindung zum MQTT-Broker.
        Muss nicht explizit aufgerufen werden, da die Klasse sich selbst beim Loeschen automatisch
        trennt.
        """
        if self.__client and self.__connection_error is False:
            print("Disconnecting from MQTT broker...")
            self.__client.loop_stop()
            self.__client.disconnect()

    def __del__(self) -> None:
        self.disconnect()
