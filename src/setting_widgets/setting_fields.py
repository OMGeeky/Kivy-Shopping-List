from kivymd.uix.dropdownitem import MDDropDownItem
from kivymd.uix.list import BaseListItem, OneLineRightIconListItem, IRightBodyTouch
from kivymd.uix.selectioncontrol.selectioncontrol import MDSwitch
from kivymd.uix.textfield import MDTextField
from kivy.lang import Builder

Builder.load_file("setting_widgets\setting_fields.kv")

# ===== TextField =====

class SettingTextField(OneLineRightIconListItem):
    """DOCS"""

class RightTextField(IRightBodyTouch, MDTextField):
    """DOCS"""

# ===== ToggleField =====

class SettingToggleField(OneLineRightIconListItem):
    """DOCS"""
    
class RightToggleField(IRightBodyTouch, MDSwitch):
    """DOCS"""

# ===== DropDownField =====

class SettingDropDownField(OneLineRightIconListItem):
    """DOCS"""
    
class RightDropDownField(IRightBodyTouch, MDDropDownItem):
    """DOCS"""