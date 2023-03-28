
import json
import os
from pathlib import Path
from typing import Dict

FILES_PATH = Path("files")

settings_filename = "settings.json"
entries_filename = "entries.json"

# region write

def write_json_to_files(dict_to_save, filename):
    """
    Hilfsmethode zum Schreiben einer JSON-Datei auf dem Geraet.

    :param dict_to_save: ``dict``, das als JSON-Datei gespeichert werden soll.
    :param filename: Name der Datei als ``str``.
    """
    if not FILES_PATH.is_dir():
        FILES_PATH.mkdir()

    path = Path(FILES_PATH, filename)

    if os.path.exists(path):
        access_mode = "w"
    else:
        access_mode = "x"

    with open(path, access_mode) as json_file:
        json.dump(dict_to_save, json_file, indent=4)


def write_settings_to_files(settings_dict):
    """
    Schreibt Einstellungen in JSON-Datei auf Geraet.

    :param settings_dict: ``dict`` mit entsprechenden Einstellungen.
    """
    write_json_to_files(settings_dict, settings_filename)

def write_entries_to_files(entries_dict):
    """
    Schreibt Eintraege der Einkaufsliste in JSON-Datei auf Geraet.

    :param entries_dict: ``dict`` mit entsprechenden Eintraegen.
    """

    write_json_to_files(entries_dict, entries_filename)

# endregion

# region read

def read_json_from_files(filename) -> dict:
    """
    Liest eine JSON-Datei als ``dict`` ein.

    :param filename: Name der auszulesenden Datei als ``str``.
    :return: Liefert ``dict`` der JSON-Datei zurueck.
    """
    path = Path(FILES_PATH, filename)

    if not os.path.exists(path):
        raise FileNotFoundError(f"File {path} not found")

    with open(path, "r") as json_file:
        return json.load(json_file)

def read_settings_from_files() -> dict:
    """
    Liest Einstellungen der lokalen JSON-Datei ein.

    :return: Liefert Einstellungen als ``dict`` zurueck.
    """
    return read_json_from_files(settings_filename)

def read_entries_from_files() -> Dict[str, list]:
    """
    Liest Eintraege der Einkaufsliste der lokalen JSON-Datei ein.

    :return: Liefert Eintraege als ``dict`` zurueck.
    """

    return read_json_from_files(entries_filename)

# endregion
