from dataclasses import dataclass, asdict
import json
from pathlib import Path

FILES_PATH = Path("files")
settings_file_path = Path(FILES_PATH,'settings.json')

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
            if not FILES_PATH.is_dir():
                FILES_PATH.mkdir()
            with open(settings_file_path, "x") as json_file:
                json.dump(settings_dict, json_file, indent=4)
        except FileExistsError:
            return

    @staticmethod
    def from_json_file():
        settings_dict = None

        try:
            with open(settings_file_path, "r") as json_file:
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

    @staticmethod
    def get_or_create():        
        settings = AppSettings.from_json_file()

        if settings is None:
            settings = AppSettings()
            settings.to_json_file()
        
        return settings