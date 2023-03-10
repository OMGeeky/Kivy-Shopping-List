import imp
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import Screen

from kivy.config import Config
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'height', '1000')
Config.set('graphics', 'width', '620')

class MainScreen(Screen):
    pass

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
