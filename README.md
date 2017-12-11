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
- Many options available, which can all be set using the tray icon menu

# Screenshots (not up-to-date)
![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/child.png)

![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/quickstyle.png)

![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/mother.png)
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

# Installation
Require Python 3, Qt5 and Qt5-SVG module. Installation will vary according to your kernel:
- Arch: 'sudo pacman -Syu python-pyqt5 qt5-svg'
- Debian: 'sudo apt-get install python3-pyqt5 libqt5svg5'
- Windows: Open the command prompt with administrator privileges and type 'python -m pip install pyqt5'

# Compatibility
qtPad is developed on Openbox. Altough not tested as often, it will also work on other platforms:
- Linux: Openbox, MATE, Cinnamon, XFCE, Deepin, KDE Plasma 5 
- Microsoft: Windows 7

Known bugs:
- Current font family is not loaded in style dialog font combo box
 
 Please report all issues on Github :)
