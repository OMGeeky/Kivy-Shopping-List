[app]

title = Shopping List App
package.name = shoppingapp
package.domain = gsog.shopping

icon.filename = res/Kivy_logo_green.png
    

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json

version = 0.1
requirements = python3,kivy=2.1.0, paho-mqtt=1.6.1, kivymd=1.0.2

orientation = portrait
fullscreen = 0
android.arch = arm64-v8a

# Android specific

# (list) Permissions
android.permissions = INTERNET

# iOS specific
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.7.0



[buildozer]
log_level = 2
