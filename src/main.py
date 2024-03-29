import socket
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path

from data import AppSettings
from data.files import read_entries_from_files, write_entries_to_files
from language import TranslationProvider, LANGUAGES
from mqtt import MqttClient

import kivy.utils
from kivy.properties import (
    StringProperty,
    ObjectProperty,
    BooleanProperty,
    ListProperty,
)
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.window import Window
from kivy.clock import mainthread

from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.card.card import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import OneLineAvatarIconListItem
from kivymd.toast import toast


if kivy.utils.platform not in ["android", "ios"]:
    Window.size = (400, 800)


class ShoppingEntry(OneLineAvatarIconListItem):
    """
    Stellt einen Eintrag in der Einkaufsliste dar.
    """
    edit_dialog = None
    is_checked = BooleanProperty(False)

    def __init__(self, text, **kwargs):
        """
        Instatiiert ein Einkaufslistenobjekt.

        :param kwargs: Zusaetzliche Keyword-Parameter als ``dict``.
        """
        super().__init__(**kwargs)
        self.initialized = False
        self.text = text
        self.is_checked = False
        self.initialized = True

    # region events

    def on_is_checked(self, *_):
        """
        Das Event wird abgefeuert, wenn der Eintrag angehakt wurde.

        :param _: Zusaetzliche Parameter als ``list``.
        """
        if not self.initialized:
            return

        list = self.get_shopping_list()
        if list:
            list.save_entries()

    # endregion
    def get_shopping_list(self):
        """
        Gibt die aktuelle Einkaufsliste durch das Eltern-Element zurueck.

        :return: Einkaufliste als ``list``.
        """
        if not self.initialized:
            return None
        if self.parent:
            return self.parent.parent.parent.parent

        return None

    def delete(self, shopping_entry):
        """
        Loescht den Eintrag aus der Einkaufsliste des Eltern-Elements.

        :param shopping_entry: Loescht den angegebenen ``ShoppingEntry`` aus Einkaufsliste.
        """
        list = self.get_shopping_list()
        if list:
            list.delete_entry(shopping_entry)

    def open_edit_popup(self):
        """
        Oeffnet ein Popup zum Bearbeiten des Eintrag-Texts.
        """
        if self.edit_dialog:
            return

        buttons = [
            MDFlatButton(
                text=self.get_translated("cancel"),
                on_release=lambda _: self.edit_dialog.dismiss()  # type: ignore
            ),
            MDFlatButton(
                text=self.get_translated("confirm"),
                on_release=lambda _: self.save_changes(),
            ),
        ]

        self.edit_dialog = MDDialog(
            title=self.get_translated("edit_entry"),
            type="custom",
            content_cls=AddDialog(self.text),
            buttons=buttons,
        )

        self.edit_dialog.on_dismiss = lambda: self.close_edit_popup()
        self.edit_dialog.open()

    def save_changes(self):
        """
        Speichert alle Aenderungen am Eintrag lokal und per MQTT auf dem jeweiligen Server.
        """
        if self.edit_dialog is None:
            return

        changed_text = self.edit_dialog.content_cls.ids["shopping_entry_text"].text
        if not changed_text or len(changed_text) == 0:
            toast(self.get_translated("empty_text_alert"))
            return

        self.text = changed_text

        self.edit_dialog.dismiss()
        list = self.get_shopping_list()
        if list:
            list.save_entries()

    def get_translated(self, key: str) -> str:
        """    
        Liefert die Uebersetzung zu einem Text-Schluessel.

        :param key: Schluessel als ``str`` zu uebersetzendem Text
        :return: Uebersetzter Text als ``str``.
        """
        settings = AppSettings.get_or_create()
        return TranslationProvider.get_translated(key, settings.language)

    def close_edit_popup(self):
        """
        Schliesst das Aendern-Popup sauber.
        """
        if not self.edit_dialog:
            return

        self.edit_dialog = None

    def __str__(self) -> str:
        return super().__str__() + f"is_checked: {self.is_checked} text: {self.text}"

class AddDialog(MDBoxLayout):
    """
    Stellt den Dialog zum Hinzufuegen und Aendern eines Einkaufslisten-Eintrags dar.
    """
    text = StringProperty("")

    def __init__(self, text="", **kwargs):
        """
        Inistantiiert ein Popup-Objekt.

        :param text: Default ist leer, gibt den initialen Anzeigetext als ``str`` an.
        :param kwargs: Zusaetzliche Keyword-Parameter als ``dict``.
        """
        super().__init__(**kwargs)
        self.text = text

    def get_translated(self, key: str) -> str:
        """    
        Liefert die Uebersetzung zu einem Text-Schluessel.

        :param key: Schluessel als ``str`` zu uebersetzendem Text.
        :return: Uebersetzter Text als ``str``.
        """
        settings = AppSettings.get_or_create()
        return TranslationProvider.get_translated(key, settings.language)


class ShoppingEntryScreen(Screen):
    """
    Screen zum Anzeigen und Bearbeiten der Einkaufsliste.
    """
    add_dialog = None
    entries = ListProperty([])
    sort_reverse = BooleanProperty(False)

    def __init__(self, **kwargs):
        """
        Instantiiert das Einkaufsliste-Screen-Objekt.

        :param kwargs: Zusaetzliche Keyword-Parameter als ``dict``.
        """
        super().__init__(**kwargs)
        self.initialized = False
        self.update_from_file()
        self.initialized = True

    # region events

    def on_bestaetigen(self, *_):
        """
        Event wird gefeuert, wenn das Popup bestaetigt wurde.

        :param _: Nur fuer Event-Uebergabe, nicht fuer unsere Logik relevant.
        """
        if self.add_dialog is None:
            return

        text = self.add_dialog.content_cls.ids["shopping_entry_text"].text
        if not text or len(text) == 0:
            toast(self.get_translated("empty_text_alert"))
            return

        self.add_shopping_entry(text)
        self.add_dialog.dismiss()

    def on_sort_reverse(self, *_):
        """
        Event wird gefeuert, wenn die Einkaufsliste neu sortiert werden soll.

        :param _: Nur fuer Event-Uebergabe, nicht fuer unsere Logik relevant.
        """
        print("on_sort_reverse", self.sort_reverse)
        entries = self.get_entries()
        self.entries = self.sort(entries, self.sort_reverse)
        self.set_entries_widgets()

    # endregion

    # region entries

    # region update entries

    def update_from_file(self):
        """
        Liest die Einkaufsliste aus der JSON-Datei.
        """
        try:
            entries = read_entries_from_files()
        except OSError:
            return

        self.set_entries(entries["entries"])

    def update_from_mqtt(self, msg_dict):
        """
        Wird durch MQTT-Subscribe aufgerufen, wenn sich die Liste aendert.
        Aktualisiert die Liste mit den neuen Eintraegen.

        :param msg_dict: Gesamte Einkaufsliste als ``dict``.
        """
        self.from_mqtt = True
        self.set_entries(msg_dict["entries"], from_mqtt=True)

    # endregion

    # region add entry

    def open_add_popup(self):
        """
        Oeffnet das Popup zum Hinzufuegen eines Eintrags.
        """
        if self.add_dialog:
            return

        language = app.settings.language

        buttons = [
            MDFlatButton(
                text=TranslationProvider.get_translated("cancel", language),
                on_release=lambda _: self.add_dialog.dismiss(),  # type: ignore
            ),
            MDFlatButton(
                text=TranslationProvider.get_translated("confirm", language),
                on_release=lambda args: self.on_bestaetigen(args),
            ),
        ]
        self.add_dialog = MDDialog(
            title=TranslationProvider.get_translated("add_entry", language),
            type="custom",
            content_cls=AddDialog(),
            buttons=buttons,
        )
        self.add_dialog.on_dismiss = lambda: self.close_add_popup()
        self.add_dialog.open()

    def close_add_popup(self):
        """
        Schliesst das Hinzufuegen-Popup.
        """
        if not self.add_dialog:
            return

        self.add_dialog = None

    def add_shopping_entry(self, text):
        """
        Fuegt der Einkaufsliste einen Eintrag hinzu.

        :param text: Eintrag-Text als ``str``.
        """
        entry = ShoppingEntry(text=text)
        self.ids["shopping_list"].add_widget(entry)
        self.save_entries()

    # endregion

    @mainthread
    def set_entries_widgets(self):
        """
        Setzt die einzelnen Widgets pro Einkauflisteneintrag auf der Oberflaeche.
        """
        print("set_entries_widgets", self)
        self.ids["shopping_list"].clear_widgets()
        for entry in self.entries:
            shopping_entry = ShoppingEntry(text=entry["text"])
            shopping_entry.is_checked = entry["is_checked"]  # type: ignore
            self.ids["shopping_list"].add_widget(shopping_entry)

    def delete_entry(self, entry: ShoppingEntry):
        """
        Loescht einen Eintrag aus der Einkaufsliste.

        :param entry: Ein Eintrag als ``ShoppingEntry``.
        """
        print("remove_entry called", entry)
        self.ids.shopping_list.remove_widget(entry)
        self.save_entries()

    def save_entries(self, entries: Optional[list] = None, from_mqtt=False):
        """
        Speichert die Eintraege in einer JSON datei und wenn ``"from_mqtt" == False`` ist,
        sendet es die Eintraege auch an MQTT zur Synchronisation.

        :param entries: Die Eintraege, die gespeichert werden sollen, wenn ``None`` werden die
        Eintraege von ``self.get_entries()`` genommen.

        :param from_mqtt: Ob der Aufruf von MQTT kommt und nicht auf MQTT zurueckgeschrieben
        werden soll.
        """
        if not self.initialized:
            return

        print(f"saving entries (from mqtt: {from_mqtt})", self, entries)
        if entries is None:
            entries = self.get_entries()

        self.entries = self.sort(entries, self.sort_reverse)
        self.set_entries_widgets()
        entries_dict = {"entries": self.sort(self.entries, False)}
        try:
            print("writing entries to file", self)
            write_entries_to_files(entries_dict)
        except OSError:
            return

        # dont push to mqtt if coming from mqtt
        if not from_mqtt:
            print('publishing entries to mqtt', self)
            app.mqtt.publish(entries_dict)

    def get_entries(self):
        """
        Gibt alle Eintraege der Einkaufliste zurueck.

        :return: Alle Eintraege der Einkaufliste als ``list``.
        """
        entries = []
        for entry in self.ids.shopping_list.children:
            entry_dict = {"is_checked": entry.is_checked, "text": entry.text}
            entries.append(entry_dict)

        return entries

    @staticmethod
    def sort(entries, reverse) -> list:
        """
        Sortiert die Einkaufliste andhand der Status und dem Text.

        :param entries: Die Einkauflisten-Eintraege als ``list``.
        :param reverse: Gibt als ``bool`` an, ob umgekehrt soriert werden soll.
        :return: Sortierte ``list`` der Eintraege.
        """
        return sorted(entries, key=lambda entry: (entry["is_checked"], entry["text"]), reverse=reverse)

    def set_entries(self, entries: List[Dict[str, Union[str, bool]]], from_mqtt=False):
        """
        Setzt die Werte der Liste auf die mitgegebenen Eintraege und speichert diese.

        :param entries: Die neuen Eintraege als ``list``.
        :param from_mqtt: Als ``bool``, ob der Aufruf von MQTT kommt und nicht auf MQTT
        zurueckgeschrieben werden soll.
        """
        print("set_entries called", entries, self)
        self.save_entries(entries, from_mqtt=from_mqtt)

    # endregion

    # region general

    def toggle_sort(self):
        """
        Setzt die umgekehrte Sortierung.
        """
        self.sort_reverse = not self.sort_reverse

    def navigate_to_settings(self):
        """
        Navigiert zur Einstellungs-Seite
        """
        self.save_entries()
        self.manager.transition.direction = "left"
        self.manager.current = "settings"

    def get_translated(self, key) -> str:
        """    
        Liefert die Uebersetzung zu einem Text-Schluessel.

        :param key: Schluessel als ``str`` zu uebersetzendem Text.
        :return: Uebersetzter Text als ``str``.
        """

        language = app.settings.language
        return TranslationProvider.get_translated(key, language)

    def __str__(self) -> str:
        return super().__str__() + f"count: {len(self.entries)}"

    # endregion

class SettingsScreen(Screen):
    """
    Screen zum Anzeigen und Bearbeiten der Einstellungen.
    """
    def __init__(self, **kwargs):
        """
        Instatiiert einen Einstellung-Screen.

        :param kwargs: Zusaetzliche Keyword-Parameter als ``dict``.
        """
        super().__init__(**kwargs)
        self.initialized = False

        # remember previous mqtt-settings to check if they changed
        self.previous_mqtt_server = app.settings.mqtt_server
        self.previous_mqtt_topic = app.settings.mqtt_topic
        self.previous_mqtt_password = app.settings.mqtt_password
        self.previous_mqtt_username = app.settings.mqtt_username

        menu_items = [
            {
                "viewclass": "OneLineListItem",
                "text": f"{LANGUAGES.get(language_key)}",
                "height": dp(56),
                "on_release": lambda x=language_key: self.set_item(x),
            }
            for language_key in LANGUAGES.keys()
        ]

        self.menu = MDDropdownMenu(
            caller=self.ids.language_drop_down,
            items=menu_items,
            position="center",
            width_mult=4,
        )

        self.menu.bind()
        # update the current selected from settings
        self.set_item(app.settings.language)

        self.initialized = True

    def apply_mqtt_settings(self):
        """
        Speichert neue MQTT-Einstellungen, sofern noetig.
        """
        if (
            self.previous_mqtt_server != app.settings.mqtt_server
            or self.previous_mqtt_topic != app.settings.mqtt_topic
            or self.previous_mqtt_password != app.settings.mqtt_password
            or self.previous_mqtt_username != app.settings.mqtt_username
        ):
            app.mqtt.disconnect()
            app.mqtt.set_target(
                app.settings.mqtt_server,
                app.settings.mqtt_topic,
                1883,
                app.settings.mqtt_username,
                app.settings.mqtt_password,
            )
            app.mqtt.connect()

    def navigate_to_shopping_list(self):
        """
        Navigiert zur Einkaufliste-Seite.
        """
        self.apply_mqtt_settings()
        self.manager.transition.direction = "right"
        self.manager.current = "shopping"

    def show_languages_menu(self):
        """
        Oeffnet das Dropdown-Menu der Sprachauswahl.
        """
        self.menu.open()

    def set_item(self, language_key):
        """
        Setze die neue Sprache bei Auswahl eines Items aus dem Dropdown-Menu.

        :param language_key: Schluessel zur Sprache als ``str``.
        """
        self.language_key = language_key
        language = LANGUAGES.get(language_key)
        self.ids.language_drop_down.set_item(language)
        self.menu.dismiss()

    def get_translated(self, key) -> str:
        """    
        Liefert die Uebersetzung zu einem Text-Schluessel.

        :param key: Schluessel als ``str`` zu uebersetzendem Text.
        :return: Uebersetzter Text als ``str``.
        """

        language = app.settings.language
        return TranslationProvider.get_translated(key, language)

    def update_language(self):
        """
        Aktualisiert auf die ausgewaehlte Sprache.
        """
        if not self.initialized:
            return
        print("update_language")
        self.update_settings()
        toast(self.get_translated("change_setting_restart_alert"))

    def switch_theme(self):
        """
        Wechselt zwischen einem Light- und einem Dark-Theme.
        """
        if not self.initialized:
            return
        self.update_settings()
        app.update_theme()

    def update_settings(self):
        """
        Speichert die Einstellungen der App neu.
        """
        if not self.initialized:
            return
        print("update_settings")
        app.settings.language = self.language_key
        app.settings.dark_theme = self.ids.theme_switch.active
        app.settings.mqtt_server = self.ids.mqtt_server_text_field.text
        app.settings.mqtt_topic = self.ids.mqtt_topic_text_field.text
        app.settings.mqtt_username = self.ids.mqtt_username_text_field.text
        app.settings.mqtt_password = self.ids.mqtt_password_text_field.text
        app.settings.to_json_file()


class ShoppingListApp(MDApp):
    """
    Geruest der gesamten App.
    """
    settings = ObjectProperty(AppSettings(), rebind=True)

    def __init__(self, **kwargs):
        """
        Instantiiert ein Objekt der App.

        :param kwargs: Zusaetzliche Keyword-Parameter als ``dict``.
        """
        super().__init__(**kwargs)
        self.mqtt: MqttClient = None  # type: ignore

    def build(self):
        """
        Startet die App und baut dabei die einzelnen Screens und den MQTT-Client auf

        :return: Einen ``ScreenManger`` zur Navigation.
        """
        self.title = "Shopping List App"
        self.settings = AppSettings.get_or_create()
        print(self.settings)
        print(self.user_data_dir)
        print(self.directory)

        if kivy.utils.platform in ["android", "ios"]:
            print("android or ios")
            src_path = Path(self.user_data_dir, "app")
        else:
            print("not android or ios")
            src_path = Path(self.directory)

        print(src_path)
        TranslationProvider.src_dir = src_path

        self.update_theme()

        sm = ScreenManager()
        shoppingEntryScreen = ShoppingEntryScreen(name="shopping")
        sm.add_widget(shoppingEntryScreen)
        sm.add_widget(SettingsScreen(name="settings"))

        self.mqtt = MqttClient(
            broker=self.settings.mqtt_server,
            port=1883,
            topic=self.settings.mqtt_topic,
            client_id=None,
            subscribe_callback=lambda msg_dict, _: shoppingEntryScreen.update_from_mqtt(
                msg_dict
            ),
            username=self.settings.mqtt_username,
            password=self.settings.mqtt_password,
        )

        try:
            print("getaddrinfo google.com")
            print(socket.getaddrinfo("google.com", 80))
        except Exception as e:
            print(e)
        try:
            print(f"getaddrinfo {self.settings.mqtt_server}")
            print(socket.getaddrinfo(self.settings.mqtt_server, 1883))
        except Exception as e:
            print(e)

        self.mqtt.connect()
        self.mqtt.subscribe()
        return sm

    def update_theme(self):
        """
        Setze das jeweils gegenteilige Theme.
        """
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.accent_palette = "BlueGray"

        if self.settings.dark_theme:
            self.theme_cls.theme_style = "Dark"
        else:
            self.theme_cls.theme_style = "Light"


if __name__ == "__main__":
    app = ShoppingListApp()
    app.run()
