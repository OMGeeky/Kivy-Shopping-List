from dataclasses import dataclass, asdict
import json

@dataclass
class AppSettings:
    language: str = "DE"
    dark_theme: bool = False
    mqtt_server: str = "broker.hivemq.com"
    mqtt_topic: str = "gsog/shopping"
    mqtt_username: str = ""
    mqtt_password: str = ""

    def to_json_file(self):
        settings_dict = {"settings": asdict(self)}
        try:
            with open("settings.json", "x") as json_file:
                json.dump(settings_dict, json_file, indent=4)
        except FileExistsError:
            return

    @staticmethod
    def from_json_file():
        settings_dict = None

        try:
            with open("settings.json", "r") as json_file:
                settings_dict = json.load(json_file)
        except FileNotFoundError:
            return None

        settings_values = settings_dict["settings"]

        new_settings = AppSettings(
            language=settings_values["language"],
            dark_theme=settings_values["dark_theme"],
            mqtt_server=settings_values["mqtt_server"],
            mqtt_topic=settings_values["mqtt_topic"],
            mqtt_username=settings_values["mqtt_username"],
            mqtt_password=settings_values["mqtt_password"],
        )

        print(new_settings)
        return new_settings
