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

# Arch install
- Download the PKGBUILD and place it inside a new directory
- Open a terminal and type 'makepkg', then 'sudo pacman -U qtpad*'

# Installation of dependancies:
Require Python 3, Qt5 and Qt5-SVG module. The installation method will vary according to your kernel.
- Debian: 'sudo apt-get install python3-pyqt5 libqt5svg5'
- Windows: Open the command prompt with administrator privileges and type 'python -m pip install pyqt5'

# Compatibility
qtPad is developed on Openbox. Altough not tested as often, it will also work on other platforms:
- Linux: Openbox, MATE, Cinnamon, XFCE, Deepin, KDE Plasma 5 
- Microsoft: Windows 7

Known bugs:
- Current font family is not loaded in style dialog font combo box
 
 Please report all issues on Github :)
 
 # Future improvements
 - Dark icon theme
 - Search and replace functionnality
