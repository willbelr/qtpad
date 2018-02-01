# qtPad
- Modern and highly customizable sticky note application
- Written in Python 3 and Qt 5

# Features
- Customize actions of left and middle click on the tray icon
- Customize default style for all new notes
- Customize style for specific notes
- Auto detect image content or path from clipboard
- Auto save when loosing focus, and auto load when gaining focus
- Indication of unsaved changes by an asterisk* at the end of the note title 
- All notes are locally stored in plain text, identified by their name
- Many options available, which can all be set using the preferences gui

# Screenshots
Text and image notes context menus

![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/child.png)


Tray icon context menu

![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/context_menu.png)


Customizable style presets

![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/quickstyle.png)
![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/stylepreset.gif)

Preferences GUI

![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/preferences.png)


Profile GUI

![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/style.png)

# Hotkeys
- Ctrl+H: Hide
- Ctrl+P: Pin
- Ctrl+R: Rename
- Ctrl+S: Save
- Ctrl+Shift+V: Paste without newline nor tabs
- Ctrl+Shift+U: Set selection to uppercase
- Ctrl+Shift+L: Set selection to lowercase
- Ctrl+Shift+R: Toggle visibility of a resize corner
- Ctrl+Shift+D: Duplicate current line
- Ctrl+Shift+Up: Shift current line up
- Ctrl+Shift+Down: Shift current line down
- Ctrl+Shift+Plus: Increase font or image size
- Ctrl+Shift+Minus: Decrease font or image size

![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/hotkeys.gif)

# Command line interface
- All the actions listed in the preferences dialog can be called from command, by using flags -a or --action
    - ie. qtpad -a "New note"

# Installation
- Arch Linux: install 'qtpad-git' from the AUR
- Linux (non-Arch): sudo pip install qtpad
- Windows:
    - Install the lastest version of Python, along with the PyPi utility (pip)
    - Open the command prompt (cmd.exe) with administrator privileges
    - Type 'python -m pip install pyqt5 requests'
    - Clone the repository and extract the qtpad folder
    - Create a shortcut to run the script manually with 'python your_installation_path/qtpad/\_\_init\_\_.py'

# Compatibility
qtPad is developed on Openbox. Altough not tested as often, it should also work on other platforms:
- Linux: Openbox, MATE, Cinnamon, XFCE, Deepin, KDE Plasma 5 
- Microsoft: Windows 7

Known bugs:
- Current font family is not loaded in style dialog font combo box
- Wrong position of the tray icon context menu in KDE 
 
 Please report all issues on Github :)
 
 # Future improvements
 - Ignore case of command line interface
 - Better size handling for images
     - Respect small size when pasting
     - Reduce size when image is larger than screen
     - Restore size after sizegrip or rename
 - Dark icon theme
 - Search and replace functionnality
