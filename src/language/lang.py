import json
from pathlib import Path
from typing import Dict, Optional


LANGUAGES = {"DE": "Deutsch", "EN": "English", "FR": "Francais"}
LANGUAGE_FOLDER = Path("src","res", "lang")


class TranslationProvider:
    last_language_key: Optional[str] = None
    last_language_dict: Optional[Dict[str, str]] = None

    @classmethod
    def get_language_file(cls, language: str) -> Dict[str, str]:
        if language not in list(LANGUAGES.keys()):
            raise ValueError('invalid language key: "{language}"')

        if cls.last_language_key == language and cls.last_language_dict is not None:
            return cls.last_language_dict

        path = Path(LANGUAGE_FOLDER, f"{language}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                result = json.load(f)
                cls.last_language_key = language
                cls.last_language_dict = result
                return result

        except FileNotFoundError:
            print(f'Language not found: "{language}"')
            raise

    @classmethod
    def get_translated(cls, key: str, language: str) -> str:
        lang_dict = cls.get_language_file(language)
        result = lang_dict.get(key, None)
        if result:
            return result

        print(f"unsuccesful try to get {key} in language {language}")
        return f'key not found for language: \nkey:"{key}"\nlanguage:"{language}"'
