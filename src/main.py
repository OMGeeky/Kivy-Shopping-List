import json
import os
from typing import Any, Dict, List, Optional, Tuple, Union
from data import AppSettings
from data.files import read_entries_from_files, write_entries_to_files
from language import TranslationProvider, LANGUAGES
from pathlib import Path

import kivy.utils
from kivy.properties import StringProperty, ObjectProperty
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.window import Window

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

    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)

        self.text = text
        self.is_checked = False

    def delete(self, shopping_entry):
        self.parent.remove_widget(shopping_entry)

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

    def get_translated(self, key: str) -> str:
        settings = AppSettings.get_or_create()
        return TranslationProvider.get_translated(key, settings.language)

    # *args bzw. *_ ist noetig, da weitere Parameter mitgegeben werden, die aber nicht genutzt werden
    def close_edit_popup(self, *_):
        if not self.edit_dialog:
            return

        self.edit_dialog.dismiss()
        self.edit_dialog = None


class AddDialog(MDBoxLayout):
    text = StringProperty("")

    def __init__(self, text="", **kwargs):
        super().__init__(**kwargs)
        self.text = text

    def get_translated(self, key: str) -> str:
        settings = AppSettings.get_or_create()
        return TranslationProvider.get_translated(key, settings.language)


class ShoppingEntryScreen(Screen):
    settings: Optional[AppSettings] = None
    add_dialog = None

    def on_bestaetigen(self, *_):
        if self.add_dialog is None:
            return

        text = self.add_dialog.content_cls.ids["shopping_entry_text"].text
        if not text or len(text) == 0:
            toast(self.get_translated("empty_text_alert"))
            return

        self.add_shopping_entry(text)

    def open_add_popup(self):
        if self.add_dialog:
            return

        language = self.get_settings().language

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
        self.ids["shopping_list"].add_widget(ShoppingEntry(text=text))
        self.close_add_popup()

    def export_entries(self):
        entries = self.get_entires()
        entries_dict = {"entries": entries}
        try:
            write_entries_to_files(entries_dict)
        except OSError:
            return
    def get_entires(self):
        entries = []
        for entry in self.ids.shopping_list.children:
            entry_dict = {"is_checked": entry.is_checked, "text": entry.text}
            entries.append(entry_dict)
        
        entries.sort(key=lambda entry: (entry['is_checked'], entry['text']))
        return entries

    def navigate_to_settings(self):
        self.manager.transition.direction = "left"
        self.manager.current = "settings"
        self.settings = None  # reset settings to reload them after change

    def load_settings(self) -> None:
        if not self.settings:
            self.settings = AppSettings.get_or_create()

    def get_settings(self) -> AppSettings:
        self.load_settings()
        return self.settings  # type: ignore

    def get_translated(self, key) -> str:
        language = self.get_settings().language
        return TranslationProvider.get_translated(key, language)


class SettingsScreen(Screen):
    settings = ObjectProperty(AppSettings(), rebind=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.settings = AppSettings.get_or_create()

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

    def navigate_to_shopping_list(self):
        self.manager.transition.direction = "right"
        self.manager.current = "shopping"

    def show_languages_menu(self):
        self.menu.open()

    def set_item(self, language_key):
        language = LANGUAGES.get(language_key)
        self.ids.language_drop_down.set_item(language)
        self.menu.dismiss()

    def get_translated(self, key) -> str:
        if self.settings is None:
            self.settings = AppSettings.get_or_create()

        language = self.settings.language
        return TranslationProvider.get_translated(key, language)


class ShoppingListApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Gray"
        self.theme_cls.theme_style = "Light"
        # TODO @Tom Theme anpassen
        self.title = "Shopping List App"

        sm = ScreenManager()
        sm.add_widget(ShoppingEntryScreen(name="shopping"))
        sm.add_widget(SettingsScreen(name="settings"))

        return sm


if __name__ == "__main__":
    app = ShoppingListApp()
    app.run()
