from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path

from data import AppSettings
from data.files import read_entries_from_files, write_entries_to_files
from language import TranslationProvider, LANGUAGES
from mqtt import MqttClient

import kivy.utils
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty, ListProperty
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
    edit_dialog = None
    is_checked = BooleanProperty(False)

    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.initialized = False
        self.text = text
        self.is_checked = False
        self.initialized = True

    # region events
    
    def on_is_checked(self, *_):
        if not self.initialized:
            return
        print('on_is_checked')
        list = self.get_shopping_list()
        if list:
            list.update_entry(self)

    # endregion
    def get_shopping_list(self):
        if not self.initialized:
            return None
        if self.parent:
            return self.parent.parent.parent.parent
        
        return None
    
    def delete(self, shopping_entry):
        list = self.get_shopping_list()
        if list:
            list.delete_entry(shopping_entry)

    def edit_popup(self):
        if self.edit_dialog:
            return

        # SPRACHE
        buttons = [
            MDFlatButton(
                text=self.get_translated("cancel"),
                on_release=self.close_edit_popup
            ),
            MDFlatButton(
                text=self.get_translated("confirm"),
                on_release=lambda args: self.save_changes(args)
            ),
        ]

        self.edit_dialog = MDDialog(
            title=self.get_translated("edit_entry"),
            type="custom",
            content_cls=AddDialog(self.text),
            buttons=buttons,
        )

        self.edit_dialog.open()

    def save_changes(self, *_):
        if self.edit_dialog is None:
            return

        changed_text = self.edit_dialog.content_cls.ids["shopping_entry_text"].text
        if not changed_text or len(changed_text) == 0:
            toast(self.get_translated("empty_text_alert"))
            return

        self.text = changed_text

        self.close_edit_popup()
        list = self.get_shopping_list()
        if list:
            list.update_entry(self)

    def get_translated(self, key: str) -> str:
        settings = AppSettings.get_or_create()
        return TranslationProvider.get_translated(key, settings.language)

    # *args bzw. *_ ist noetig, da weitere Parameter mitgegeben werden, die aber nicht genutzt werden
    def close_edit_popup(self, *_):
        if not self.edit_dialog:
            return

        self.edit_dialog.dismiss()
        self.edit_dialog = None

    def __str__(self) -> str:
        return super().__str__() + f'is_checked: {self.is_checked} text: {self.text}'


class AddDialog(MDBoxLayout):
    text = StringProperty("")

    def __init__(self, text="", **kwargs):
        super().__init__(**kwargs)
        self.text = text

    def get_translated(self, key: str) -> str:
        settings = AppSettings.get_or_create()
        return TranslationProvider.get_translated(key, settings.language)


class ShoppingEntryScreen(Screen):
    add_dialog = None
    entries = ListProperty([])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.initialized = False
        self.update_from_file()
        self.initialized = True

    # region events

    def on_bestaetigen(self, *_):
        if self.add_dialog is None:
            return

        text = self.add_dialog.content_cls.ids["shopping_entry_text"].text
        if not text or len(text) == 0:
            toast(self.get_translated("empty_text_alert"))
            return

        self.add_shopping_entry(text)

    @mainthread
    def on_entries(self, *_):
        print("on_entries called")
        self.ids["shopping_list"].clear_widgets()
        for entry in self.entries:
            shopping_entry = ShoppingEntry(text=entry['text'])
            shopping_entry.is_checked = entry['is_checked']  # type: ignore
            self.ids["shopping_list"].add_widget(shopping_entry)

    # endregion

    # region entries

    # region update entries
    
    def update_from_file(self):
        try:
            entries = read_entries_from_files()
        except OSError:
            return

        self.set_entries(entries['entries'])

    def update_from_mqtt(self, msg_dict):
        self.from_mqtt = True
        self.set_entries(msg_dict['entries'], from_mqtt=True)
    
    def update_entry(self, entry: ShoppingEntry):
        print('update entry called', entry)
        self.export_entries()

    # endregion
    
    # region add entry

    def open_add_popup(self):
        if self.add_dialog:
            return

        language = app.settings.language

        buttons = [
            MDFlatButton(
                text=TranslationProvider.get_translated("cancel", language),
                on_release=self.close_add_popup,
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

        self.add_dialog.open()

    def close_add_popup(self, *_):
        if not self.add_dialog:
            return

        self.add_dialog.dismiss()
        self.add_dialog = None

    def add_shopping_entry(self, text):
        entry = ShoppingEntry(text=text)
        self.ids["shopping_list"].add_widget(entry)
        self.update_entry(entry)
        self.close_add_popup()
    
    # endregion

    def delete_entry(self, entry: ShoppingEntry):
        print('remove_entry called', entry)
        self.ids.shopping_list.remove_widget(entry)

    def export_entries(self, from_mqtt=False):
        """
        Speichert die einträge in einer JSON datei und wenn 'from_mqtt' == False ist 
        sendet es die daten an MQTT zur synchronisation

        :param from_mqtt: ob der aufruf von MQTT kommt und nicht auf MQTT zurück geschrieben werden soll
        """
        if not self.initialized:
            return
        print('exporting entries', from_mqtt)
        entries = self.get_entires()
        entries_dict = {"entries": entries}
        try:
            write_entries_to_files(entries_dict)
        except OSError:
            return

        # dont push to mqtt if coming from mqtt
        if not from_mqtt:
            app.mqtt.publish(entries_dict)

    def get_entires(self):
        entries = []
        for entry in self.ids.shopping_list.children:
            entry_dict = {"is_checked": entry.is_checked, "text": entry.text}
            entries.append(entry_dict)

        entries.sort(key=lambda entry: (entry['is_checked'], entry['text']))
        return entries

    def set_entries(self, entries: List[Dict[str, Union[str, bool]]], from_mqtt=False):
        """
        Setzt die werte der liste auf die mitgegebenen einträge

        :param entries: die neuen einträge
        :param from_mqtt: ob der aufruf von MQTT kommt und nicht auf MQTT zurück geschrieben werden soll
        """
        self.entries = entries
        self.export_entries(from_mqtt=from_mqtt)

    # endregion

    # region general
    
    def navigate_to_settings(self):
        """Navigiert zur Einstellungs-Seite"""
        self.export_entries()
        self.manager.transition.direction = "left"
        self.manager.current = "settings"

    def get_translated(self, key) -> str:
        language = app.settings.language
        return TranslationProvider.get_translated(key, language)
    
    def __str__(self) -> str:
        return super().__str__() + f'count: {len(self.entries)}'

    # endregion

class SettingsScreen(Screen):
    def __init__(self, **kwargs):
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
        if self.previous_mqtt_server != app.settings.mqtt_server or \
           self.previous_mqtt_topic != app.settings.mqtt_topic or \
           self.previous_mqtt_password != app.settings.mqtt_password or \
           self.previous_mqtt_username != app.settings.mqtt_username:
            app.mqtt.disconnect()
            app.mqtt.set_target(app.settings.mqtt_server,
                                app.settings.mqtt_topic,
                                1883,
                                app.settings.mqtt_username,
                                app.settings.mqtt_password)
            app.mqtt.connect()

    def navigate_to_shopping_list(self):
        self.apply_mqtt_settings()
        self.manager.transition.direction = "right"
        self.manager.current = "shopping"

    def show_languages_menu(self):
        self.menu.open()

    def set_item(self, language_key):
        self.language_key = language_key
        language = LANGUAGES.get(language_key)
        self.ids.language_drop_down.set_item(language)
        self.menu.dismiss()

    def get_translated(self, key) -> str:
        language = app.settings.language
        return TranslationProvider.get_translated(key, language)

    def update_language(self):
        if not self.initialized:
            return
        print("update_language")
        self.update_settings()
        toast(self.get_translated("change_setting_restart_alert"))
        # TODO (1): eventuell ohne restart

    def switch_theme(self):
        if not self.initialized:
            return
        self.update_settings()
        toast(self.get_translated("change_setting_restart_alert"))
        # app.update_theme() # TODO (1): eventuell ohne restart

    def update_settings(self):
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
    settings = ObjectProperty(AppSettings(), rebind=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mqtt: MqttClient = None  # type: ignore

    def build(self):
        self.title = "Shopping List App"
        self.settings = AppSettings.get_or_create()
        print(self.settings)
        print(self.user_data_dir)
        print(self.directory)

        if kivy.utils.platform in ["android", "ios"]:
            print('android or ios')
            src_path = Path(self.user_data_dir, 'app')
        else:
            print('not android or ios')
            src_path = Path(self.directory)

        print(src_path)
        TranslationProvider.src_dir = src_path

        # TODO @Tom Theme anpassen
        self.theme_cls.primary_palette = "Gray"
        self.update_theme()

        sm = ScreenManager()
        shoppingEntryScreen = ShoppingEntryScreen(name="shopping")
        sm.add_widget(shoppingEntryScreen)
        sm.add_widget(SettingsScreen(name="settings"))

        self.mqtt = MqttClient(broker=self.settings.mqtt_server,
                               port=1883,
                               topic=self.settings.mqtt_topic,
                               client_id=None,
                               subscribe_callback=lambda msg_dict, _: shoppingEntryScreen.update_from_mqtt(
                                   msg_dict),
                               username=self.settings.mqtt_username,
                               password=self.settings.mqtt_password)
        try:
            # print('skipping mqtt connection')
            self.mqtt.connect()
            self.mqtt.subscribe()
        except Exception as e:
            print(e)
            toast("MQTT-Connection failed")
        return sm

    def update_theme(self):
        if self.settings.dark_theme:
            self.theme_cls.theme_style = "Dark"
        else:
            self.theme_cls.theme_style = "Light"


if __name__ == "__main__":
    app = ShoppingListApp()
    app.run()
