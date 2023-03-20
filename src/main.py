from os import name
from kivy.app import App
from kivy.properties import ListProperty, StringProperty, BooleanProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Label
from kivy.metrics import dp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.core.window import Window

from kivymd.app import MDApp
from kivymd.uix.button import MDFlatButton
from kivymd.uix.card.card import MDBoxLayout
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.list import OneLineAvatarIconListItem


LANGUAGES = { "DE": "Deutsch", "EN": "English", "FR": "Francais" }

Window.size = (400, 800)

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
    add_dialog = None

    def on_bestaetigen(self, *args):
        if self.add_dialog is None:
            return
        
        text = self.add_dialog.content_cls.ids['shopping_entry_text'].text
        print(text)
        if not text or len(text) == 0:
            print("Kein Text") # TODO: Fehlermeldung anzeigen
            return

        self.add_shopping_entry(text)
        

    def open_add_popup(self):
        if self.add_dialog:
            return

        # SPRACHE
        buttons = [
            MDFlatButton(text='Abbrechen', on_release=self.close_add_popup),
            MDFlatButton(text='Bestätigen', on_release=lambda args: self.on_bestaetigen(args)),
        ]
        # SPRACHE
        self.add_dialog = MDDialog(
            title='Eintrag hinzufügen',
            type='custom',
            content_cls=AddDialog(),
            buttons=buttons,
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        menu_items = [
            {
                "viewclass": "OneLineListItem",
                "text": f"{LANGUAGES.get(language_key)}",
                "height": dp(56),
                "on_release": lambda x=f"{LANGUAGES.get(language_key)}": self.set_item(language_key),
            } for language_key in LANGUAGES.keys()
        ]

        self.menu = MDDropdownMenu(
            caller=self.ids.language_drop_down,
            items=menu_items,
            position="center",
            width_mult=4,
        )
        
        self.menu.bind()

    def navigate_to_shopping_list(self):
        self.manager.transition.direction = 'right'
        self.manager.current = 'shopping'

    def show_languages_menu(self):
        self.menu.open()

    def set_item(self, language_key):
        language = LANGUAGES.get(language_key)
        self.ids.language_drop_down.set_item(language)
        self.menu.dismiss()

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
