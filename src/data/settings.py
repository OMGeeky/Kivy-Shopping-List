from dataclasses import dataclass, asdict
import json

from data.files import read_settings_from_files, write_settings_to_files

@dataclass
class AppSettings:
    """
    Stellt Datenklasse zum Halten der aktuellen Einstellungen dar.
    """
    language: str = "DE"
    dark_theme: bool = False
    mqtt_server: str = "broker.hivemq.com"
    mqtt_topic: str = "gsog/shopping"
    mqtt_username: str = ""
    mqtt_password: str = ""

    def to_json_file(self):
        """
        Wandelt das Objekt in eine Einstellung-JSON-Datei um und speichert diese auf dem Geraet.
        """
        settings_dict = {"settings": asdict(self)}
        try:
            write_settings_to_files(settings_dict)
        except OSError as e:
            print(e)
            return

    @staticmethod
    def from_json_file():
        """
        Statische Methode zum Auslesen einer lokalen JSON-Datei und direkten Umwandlung in ein
        ``AppSettings``-Objekt.
        """
        settings_dict = None

        try:
            settings_dict = read_settings_from_files()
        except FileNotFoundError:
            print("Settings file not found")
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

        return new_settings

    @staticmethod
    def get_or_create():
        """
        Statische Methode, welche entweder initiale Einstellungen anlegt oder diese aus einer
        vorhandenen JSON-Datei liest.
        """
        settings = AppSettings.from_json_file()
        if settings is None:
            print("Creating new settings")
            settings = AppSettings()
            settings.to_json_file()
        
        return settings
