[app]

title = birabiro

package.name = birabiro


package.domain = beki.et

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas
#source.exclude_dirs = bin, venv, .git
#source.exclude_exts = pyc,log,tmp

# (str) Application versioning (method 1)
version = 0.1

# (str) Application versioning (method 2)
# version.regex = __version__ = ['"](.*)['"]
# version.filename = %(source.dir)s/main.py

requirements = python3,kivy==2.3.1,kivymd==1.2.0,Pillow,sqlite3,filetype,androidstorage4kivy


# (str) Presplash of the application
presplash.filename = %(source.dir)s/assets/splash.png

# (str) Icon of the application
icon.filename = %(source.dir)s/assets/icon.png

# Valid options are: landscape, portrait, portrait-reverse or landscape-reverse
orientation = portrait

#
#
# author = © Copyright Info

# change the major version of python used by the app
osx.python_version = 3

# Kivy version to use
osx.kivy_version = 2.3.1



# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE



#
# (int) Target Android API, should be as high as possible.
android.api = 34

# (int) Minimum API your APK / AAB will support.
android.minapi = 21


android.archs = arm64-v8a

# android.release_artifact = aab

android.release_artifact = apk


# (str) Path to a custom kivy-ios folder
#ios.kivy_ios_dir = ../kivy-ios
# Alternately, specify the URL and branch of a git checkout:
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master

# Another platform dependency: ios-deploy
# Uncomment to use a custom checkout
#ios.ios_deploy_dir = ../ios_deploy
# Or specify URL and branch
ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.10.0

# (bool) Whether or not to sign the code
ios.codesign.allowed = false



[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

