from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanel

class MainGridLayout(GridLayout):
    pass

class EntryBoxLayout(BoxLayout):
    pass

class PageTabPanel(TabbedPanel):
    pass

class ShoppingListApp(App):
    def build(self):
        self.title = 'Shopping List App'
        return PageTabPanel()

if __name__ == "__main__":
    ShoppingListApp().run()
