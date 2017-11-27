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

# Screenshots
![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/child.png)

![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/mother.png)
![alt tag](https://raw.githubusercontent.com/willbelr/qtpad/master/screenshots/style.png)

# Hotkeys
- Ctrl+H: Hide
- Ctrl+P: Pin
- Ctrl+R: Rename
- Ctrl+S: Save
- Ctrl+Delete: Delete 
- Ctrl+Shift+V: Paste without newline nor tabs
- Ctrl+Shift+U: Set selection to uppercase
- Ctrl+Shift+L: Set selection to lowercase
- Ctrl+Shift+R: Toggle visibility of a resize corner
- Ctrl+Shift+D: Duplicate current line
- Ctrl+Shift+Up: Shift current line up
- Ctrl+Shift+Down: Shift current line down
- Ctrl+Shift+Plus: Increase font or image size
- Ctrl+Shift+Minus: Decrease font or image size

# Dependencies
- Require Python 3 with Qt5 packages, including qt5-svg and python-pyqt5 (python3-pyqt5 on debian) 
- Made on Linux, might work on other platforms
- Tested on Openbox and tint2, KDE 5. Please report any problem :)

# Known bug
- Odd handling of the tray icon context menu on KDE
