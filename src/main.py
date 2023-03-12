from kivy.app import App
from kivy.properties import ListProperty, StringProperty, BooleanProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Label
from kivy.uix.screenmanager import Screen
from kivy.config import Config

Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'height', '1000')
Config.set('graphics', 'width', '620')

class ShoppingEntry(BoxLayout):
    text = StringProperty()
    is_checked = BooleanProperty()

    def __init__(self, **kwargs):
        super(ShoppingEntry, self).__init__(**kwargs)

class MainScreen(Screen):
    shoppingEntries = ListProperty([])
    shop = ObjectProperty(BoxLayout())

    def __init__(self, *args, **kwargs):
        super(MainScreen, self).__init__(*args, **kwargs)
        self.add_shopping_entry("Test", True)

    def add_shopping_entry(self, text: str, is_checked: bool):
        entry = ShoppingEntry()
        entry.text = text
        entry.is_checked = is_checked

        self.shop.add_widget(entry)
        self.shop.add_widget(Label(text="Hallo"))
        print("ADD_ENTRY")

        self.shoppingEntries.append(entry)

    # load existing shopping entries
    def on_enter(self):
        print("ENTER_MAIN_SCREEN")

        entry = ShoppingEntry()
        entry.text = "Test"
        entry.is_checked = True
        #self.ids["shop"].add_widget(entry)

class SettingsScreen(Screen):
    pass

class MainPage(BoxLayout):
    pass

class ShoppingListApp(App):
    def build(self):
        self.title = 'Shopping List App'
        return MainPage()
    
if __name__ == "__main__":
    app = ShoppingListApp()
    app.run()
