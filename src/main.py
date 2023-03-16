from os import name
from kivy.app import App
from kivy.properties import ListProperty, StringProperty, BooleanProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Label
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.config import Config

from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.card.card import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import OneLineAvatarIconListItem

Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'height', '1000')
Config.set('graphics', 'width', '620')

class ShoppingEntry(OneLineAvatarIconListItem):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)

        self.text = text
        self.is_checked = False

    def delete(self, shopping_entry):
        self.parent.remove_widget(shopping_entry)

class AddDialog(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class ShoppingEntryScreen(Screen):
    add_dialog: MDDialog | None = None

    def open_add_popup(self):
        if self.add_dialog:
            return

        # SPRACHE
        buttons = [
            MDFlatButton(text='Abbrechen', on_release=self.close_add_popup),
            MDFlatButton(text='Bestätigen', on_release=lambda args: self.add_shopping_entry("Text"))
        ]
        # SPRACHE
        self.add_dialog = MDDialog(
            title='Eintrag hinzufügen',
            type='custom',
            content_cls=AddDialog(),
            buttons=buttons
        )

        self.add_dialog.open()

    # *args ist noetig, da weitere Parameter mitgegeben werden, die aber nicht genutzt werden
    def close_add_popup(self, *args):
        if not self.add_dialog:
            return

        self.add_dialog.dismiss()
        self.add_dialog = None


    def add_shopping_entry(self, text):
        self.ids['shopping_list'].add_widget(ShoppingEntry(text=text))
        self.close_add_popup()

    def delete_entry(self):
        pass

    def navigate_to_settings(self):
        self.manager.transition.direction = 'left'
        self.manager.current = 'settings'    

class SettingsScreen(Screen):
    def navigate_to_shopping_list(self):
        self.manager.transition.direction = 'right'
        self.manager.current = 'shopping'

class ShoppingListApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.theme_style = "Light"
        self.title = 'Shopping List App'

        sm = ScreenManager()
        sm.add_widget(ShoppingEntryScreen(name='shopping'))
        sm.add_widget(SettingsScreen(name='settings'))

        return sm
                   
if __name__ == "__main__":
    app = ShoppingListApp()
    app.run()
