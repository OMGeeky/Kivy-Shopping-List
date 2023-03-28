import json
from pathlib import Path
from typing import Dict, Optional


LANGUAGES = {"DE": "Deutsch", "EN": "English", "FR": "Francais"}
LANGUAGE_FOLDER = Path("res", "lang")


class TranslationProvider:
    """
    Dient als statische Hilfsklasse zum Uebersetzen von Texten innerhalb der App.
    """
    src_dir : Path 
    last_language_key: Optional[str] = None
    last_language_dict: Optional[Dict[str, str]] = None

    @classmethod
    def get_language_file(cls, language: str) -> Dict[str, str]:
        """
        Statische Methode zum Auslesen einer Sprach-JSON-Datei.
        Laedt die Uebersetzungen anhand der ausgewaehlten Sprache.

        :param language: Sprachschluessel der gewuenschten Sprache als ``str``.
        """
        if language not in list(LANGUAGES.keys()):
            raise ValueError('invalid language key: "{language}"')

        if cls.last_language_key == language and cls.last_language_dict is not None:
            return cls.last_language_dict

        path = Path(cls.src_dir, LANGUAGE_FOLDER, f"{language}.json")
        print(f"loading language file: {path}")
        print(f'src_dir: {cls.src_dir}')
        try:
            with open(path, "r", encoding="utf-8") as f:
                result = json.load(f)
                cls.last_language_key = language
                cls.last_language_dict = result
                return result

        except FileNotFoundError:
            print(f'Language not found: "{language}"')
            return {}

    @classmethod
    def get_translated(cls, key: str, language: str) -> str:
        """
        Diese statische Methide uebersetzt einen Text anhand des Text-Schluessels und der Sprache.

        :param key: Schluessel des zu uebersetzenden Texts als ``str``.
        :param language: Sprachschluessel der gewuenschten Sprache als ``str``.
        """
        lang_dict = cls.get_language_file(language)
        result = lang_dict.get(key, None)
        if result:
            return result

        print(f"unsuccessful try to get {key} in language {language}")
        return f'key not found for language: \nkey:"{key}"\nlanguage:"{language}"'
