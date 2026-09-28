[app]
title = Trading App
package.name = tradingapp
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db
version = 0.1

requirements = python3,kivy,google-generativeai,urllib3,chardet,idna,requests,certifi

orientation = portrait
fullscreen = 0

android.permissions = INTERNET
android.accept_sdk_license = True
android.api = 33
android.minapi = 24

[buildozer]
log_level = 2
warn_on_root = 1
