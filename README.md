# qtPad
- Modern and highly customizable sticky note application
- Written in Python 3 and Qt 5

# Features
- Customizable actions of left and middle click on the tray icon
- Customizable default style for all new notes, style for specific notes and style presets
- Customizable hotkeys and context menus
- Auto detect image content or path from clipboard
- Auto save when loosing focus, and auto load when gaining focus
- Indication of unsaved changes by an asterisk* at the end of the note title 
- All notes are locally stored in plain text, identified by their name
- Many text actions boundable to hotkeys, such as indenting, sorting, case change, line shift... 
- Search and replace GUI

# Screenshots
Customizable style presets

![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/quickstyle.png)
![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/stylepreset.gif)

Preferences GUI

![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/preferences_general.png)
![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/preferences_hotkeys.png)
![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/preferences_menus.png)
![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/preferences_presets.png)

Profile GUI

![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/style.png)

# Command line interface
- All the actions listed in the preferences dialog can be called from command, by using flags -a or --action
    - ie. qtpad -a "new note"

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
