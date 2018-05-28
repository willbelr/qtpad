#!/usr/bin/python3
import json
import os
import sys
import time
from PyQt5 import QtGui, QtWidgets, QtCore, uic
from PyQt5.QtCore import Qt

try:
    import qtpad.gui_preferences
    from qtpad.common import *
except ImportError:
    from common import *

# Init common settings
LOCAL_DIR, ICONS_DIR, PREFERENCES_FILE, PROFILES_FILE = getStaticPaths()
logger = getLogger()

PREFERENCES_DEFAULT = \
{
    'general':
    {
        'notesDb': os.path.expanduser("~/.config/qtpad/notes/"),
        'nameText': 'Untitled',
        'nameImage': 'Image',
        'minimize': True,
        'autoIndent': True,
        'safeDelete': True,
        'hotkeys': True,
        'frameless': False,
        'deleteEmptyNotes': False,
        'fetchClear': True,
        'fetchUrl': False,
        'fetchFile': True,
        'fetchTxt': True,
        'fetchIcon': True,
    },
    'actions':
    {
        'leftAction': 'Toggle actives',
        'middleAction': 'Fetch clipboard or new note',
        'startupAction': 'None',
        'leftCmd': '',
        'middleCmd': '',
        'startupCmd': '',
    },
    'styleDefault':
    {
        'pin': False,
        'sizeGrip': False,
        'x': 0,
        'y': 0,
        'width': 300,
        'height': 220,
        'background': '#ffff7f',
        'foreground': '#000000',
        'fontSize': 9,
        'fontFamily': 'Sans Serif',
    },
    'stylePresets':
    {
        'Black on yellow': {'background': '#ffff7f', 'foreground': '#000000'},
        'Black on white': {'background': '#ffffff', 'foreground': '#000000'},
        'White on black': {'background': '#2a2a2a', 'foreground': '#ffffff'},
        'Low priority': {'background': '#c6efce', 'foreground': '#004000'},
        'Mid priority': {'background': '#ffeb9c', 'foreground': '#553400'},
        'High priority': {'background': '#ffc7ce', 'foreground': '#9c0006'},
    },
    'hotkeys':
    {
        'ctrl':
        {
            'D': 'duplicate line',
            'F': 'search',
            'P': 'pin',
            'R': 'rename',
            'Y': 'redo',
            'Wheel Up': 'zoom in',
            'Wheel Down': 'zoom out',
            "<": "Decrease indent",
        },
        'ctrlShift':
        {
            'L': 'selection to lowercase',
            'R': 'toggle sizegrip',
            'S': 'sort selection',
            'U': 'selection to uppercase',
            'V': 'special paste',
            'Up': 'shift line up',
            'Down': 'shift line down',
            '+': 'zoom in',
            '_': 'zoom out',
            ">": "Increase indent",
        },
        'shift':
        {
            'Backspace': 'delete line',
        }
    },
    'menus':
    {
        'mother': ['New note', 'Toggle actives', 'Fetch clipboard', 'Show all', 'Reset positions', '(Separator)', 'Folders list', 'Delete folders', '(Separator)', 'Notes list', '(Separator)', 'Preferences', 'Quit'],
        'child': ['New note', 'Rename', 'Style', 'Pin', 'Save as', 'Copy to clipboard', 'Move to folder', '(Separator)', 'Delete'],
    },
    'actives': [],
    'folders': {},
}

class Preferences(object):
    def __init__(self):
        if os.path.isfile(PREFERENCES_FILE) and os.stat(PREFERENCES_FILE).st_size > 0:
            self.load()
            # Look for missing keys
            if not set(PREFERENCES_DEFAULT) == set(self.db):
                self.db = copyDict(PREFERENCES_DEFAULT)
                self.save()
                logger.error("KeyError: Preference database has been reset to default (failsafe patch)")
        else:
            self.db = copyDict(PREFERENCES_DEFAULT)
            with open(PREFERENCES_FILE, "w") as f:
                f.write(json.dumps(self.db, indent=2, sort_keys=False))
            logger.info("Created preferences file")
        self.initStyleSheet()

    def load(self):
        with open(PREFERENCES_FILE, "r") as f:
            self.db = json.load(f)
        logger.info("Loaded preferences database")

    def set(self, name, entry, value=None):
        if value is None:
            self.db[name] = entry
            self.save()
        else:
            self.db[name][entry] = value

    def save(self):
        with open(PREFERENCES_FILE, "w") as f:
            f.write(json.dumps(self.db, indent=2, sort_keys=False))
        logger.info("Saved preferences database")

    def query(self, *keys, db=None, fallback=False):
        if not db : db = self.db
        for key in keys:
            try:
                db = db[key]
            except KeyError:
                if not fallback:
                    logger.error("KeyError (preferences): fetching default value for %s" % str(keys))
                    return self.query(*keys, db=PREFERENCES_DEFAULT, fallback=True)
                logger.critical("KeyError: could not fetch key from default database %s" % str(keys))
                return None
        return db

    def initStyleSheet(self):
        STYLESHEET_FILE = os.path.expanduser("~/.config/qtpad/frame.css")
        if not os.path.isfile(STYLESHEET_FILE) or os.stat(STYLESHEET_FILE).st_size == 0:
            # Format python dict to CSS syntax
            default = \
            {
                'QLabel#iconLabel':
                {
                    'background-color': '#444444',
                },
                'QLabel#titleLabel':
                {
                    'color': '#888888',
                    'background-color': '#444444',
                    'font-weight': 'bold',
                },
                'QLabel#titleLabel:active':
                {
                    'color': '#ffffff',
                },
                'QPushButton#closeButton':
                {
                    'color': '#888888',
                    'background-color': '#444444',
                    'font-weight': 'bold',
                    'border': 'none',
                    'padding': '5px',
                },
                'QPushButton#closeButton:active':
                {
                    'color': '#ffffff',
                },
                'QPushButton#closeButton:hover':
                {
                    'color': '#1d90cd',
                }
            }
            stylesheet = ""
            for item in default:
                stylesheet += item + "\n{\n"
                for attribute in default[item]:
                    stylesheet += "  " + attribute + ": " + default[item][attribute] + ";\n"
                stylesheet += "}\n"
            with open(STYLESHEET_FILE, 'w') as f:
                f.write(stylesheet)
            logger.warning("New stylesheet created from default values")


class Profile(object):
    def __init__(self, parent, index):
        self.name = parent.name
        self.preferences = parent.parent.preferences
        PROFILES_FILE = os.path.expanduser("~/.config/qtpad/profiles.json")

        if os.path.isfile(PROFILES_FILE) and os.stat(PROFILES_FILE).st_size > 0:
            self.load()
        else:
            self.db = {}

        if self.name not in self.db:
            # Create a new profile and position the widget
            self.db[self.name] = copyDict(self.preferences.db["styleDefault"])

            if parent.isImage:
                image = QtGui.QPixmap(parent.path)
                self.db[self.name]["width"] = image.width()
                self.db[self.name]["height"] = image.height()

            x = QtWidgets.QDesktopWidget().screenGeometry().width() - self.query("width")
            x = x - (index * 28)
            y = (self.query("height")/2) + (index * 28)
            self.db[self.name]["x"] = x
            self.db[self.name]["y"] = y

            with open(PROFILES_FILE, 'w') as f:
                f.write(json.dumps(self.db, indent=2, sort_keys=False))
            logger.info("Created profile for '" + self.name + "'")

    def load(self):
        with open(PROFILES_FILE) as f:
            self.db = json.load(f)
        logger.info("Loaded profiles database (" + self.name + ")")

    def set(self, entry, value):
        if self.name in self.db:
            self.db[self.name][entry] = value
        else:
            self.db[self.name] = {}

    def save(self, entry=None, value=None):
        if entry and value is not None:
            self.load()
            self.set(entry, value)

        with open(PROFILES_FILE, "w") as f:
            f.write(json.dumps(self.db, indent=2, sort_keys=False))
        logger.info("Saved profile database (" + self.name + ")")

    def query(self, *keys, db=None, fallback=False):
        if not db : db = self.db[self.name]
        for key in keys:
            try:
                db = db[key]
            except KeyError:
                if not fallback:
                    logger.error("KeyError (profile): fetching default value for %s" % str(keys))
                    return self.query(*keys, db=PREFERENCES_DEFAULT["styleDefault"], fallback=True)
                logger.critical("KeyError: could not fetch key from default database %s" % str(keys))
                return None
        return db


class centeredTableItem(QtWidgets.QTableWidgetItem):
    def __init__(self, name):
        super().__init__()
        self.setText(name)
        self.setTextAlignment(Qt.AlignCenter)


class PreferencesDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__()

        # Load the ui file in case the gui modules are not loaded
        if "qtpad.gui_preferences" in sys.modules:
            self.ui = qtpad.gui_preferences.Ui_Dialog()
            self.ui.setupUi(self)
        else:
            self.ui = uic.loadUi(LOCAL_DIR + 'gui_preferences.ui', self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        self.parent = parent
        self.genre = type(parent).__name__

        # Load preferences from Mother instance
        if self.genre == "Mother":
            self.preferences = parent.preferences
        elif self.genre == "Child":
            self.preferences = parent.parent.preferences
        self.preferences.load()
        self.db = copyDict(self.preferences.db)

        # Init preferences or style dialog
        if self.genre == "Mother":
            self.initMother()
        elif self.genre == "Child":
            self.initChild()

        # Hotkeys
        self.modifier = {"ctrl": False, "shift": False, "ctrlShift": False}

        # Style default
        self.ui.styleBackgroundButton.clicked.connect(lambda: self.stylePickLayerColor("background"))
        self.ui.styleForegroundButton.clicked.connect(lambda: self.stylePickLayerColor("foreground"))
        self.ui.styleFontFamilyCombo.currentFontChanged.connect(self.styleUpdateFontFamily)
        self.ui.styleFontSizeBox.valueChanged.connect(self.styleUpdateFontSize)
        self.ui.styleWidthBox.valueChanged.connect(self.styleUpdateWidth)
        self.ui.styleHeightBox.valueChanged.connect(self.styleUpdateHeight)

        # Init preferences dialog
        self.load()
        self.done = self.exec_()
        self.close()

    def initMother(self):
        # General settings
        self.styleDefault = copyDict(self.preferences.db["styleDefault"])
        self.setFixedSize(640, 400)
        self.ui.resetButton.clicked.connect(self.reset)
        self.ui.styleDefaultBox.hide()

        # Default actions
        actions = ['Toggle actives', 'New note', 'Fetch clipboard or new note', 'Show all', 'Hide all', 'Reverse all',
                        'Reset positions', 'Fetch clipboard', 'Exec', 'None']
        actions.sort()
        self.ui.leftClickCombo.addItems(actions)
        self.ui.middleClickCombo.addItems(actions)
        self.ui.startupCombo.addItems(actions)
        self.ui.leftClickCombo.currentTextChanged.connect(self.actionToggleExecWidgets)
        self.ui.middleClickCombo.currentTextChanged.connect(self.actionToggleExecWidgets)
        self.ui.startupCombo.currentTextChanged.connect(self.actionToggleExecWidgets)

        # Hotkeys
        hotkeyActions = ['', 'Delete line', 'Duplicate line', 'Hide', 'Pin', 'Rename', 'Save', 'Selection to lowercase',
                            'Selection to uppercase', 'Shift line down', 'Shift line up', 'Increase indent', 'Decrease indent',
                            'Sort selection', 'Toggle wordwrap', 'Special paste', 'Toggle sizegrip', 'Zoom in', 'Zoom out',
                            'New note', 'Delete',  'Save as', 'Search', 'Undo', 'Redo']
        hotkeyActions.sort()
        self.ui.hotkeyActionCombo.addItems(hotkeyActions)
        self.ui.hotkeyKeyLine.event = self.hotkeyEventFilter
        self.ui.hotkeyKeyLine.textEdited.connect(self.ui.hotkeyKeyLine.undo)
        self.ui.hotkeyDeleteButton.clicked.connect(self.hotkeyDelete)
        self.ui.hotkeyAddButton.clicked.connect(self.hotkeyAdd)

        # Style presets
        self.ui.presetTable.selectionModel().selectionChanged.connect(self.presetSelectEvent)
        self.ui.presetBackgroundButton.clicked.connect(self.presetPickBackgroundColor)
        self.ui.presetForegroundButton.clicked.connect(self.presetPickForegroundColor)
        self.ui.presetNewButton.clicked.connect(self.presetNewEvent)
        self.ui.presetDeleteButton.clicked.connect(self.presetDeleteEvent)
        self.ui.presetNameLine.textEdited.connect(self.presetRenameEvent)

        # Context menus
        self.ui.menuChildAddButton.clicked.connect(self.menuChildAddEvent)
        self.ui.menuMotherAddButton.clicked.connect(self.menuMotherAddEvent)
        self.ui.menuChildRemoveButton.clicked.connect(self.menuChildRemoveEvent)
        self.ui.menuMotherRemoveButton.clicked.connect(self.menuMotherRemoveEvent)

        # Setup side menu
        self.ui.stackedWidget.setCurrentIndex(self.parent.preferencesMenuIndex)
        self.ui.sideMenuList.item(self.parent.preferencesMenuIndex).setSelected(True)
        self.ui.sideMenuList.selectionModel().selectionChanged.connect(self.menuEvent)

    def initChild(self):
        self.styleDefault = copyDict(self.parent.profile.db[self.parent.name])
        self.setWindowTitle("Style for '" + self.parent.name + "'")
        self.setFixedSize(480, 200)
        self.ui.stackedWidget.setCurrentIndex(4)
        self.sideMenuList.hide()
        self.line.hide()
        self.label_4.hide()
        self.label_5.hide()
        self.nameTextLine.hide()
        self.nameImageLine.hide()
        self.framelessBox.hide()
        self.styleSizegripBox.hide()
        self.stylePinBox.hide()

    def load(self):
        # General settings
        self.ui.minimizeBox.setChecked(self.db["general"]["minimize"])
        self.ui.autoIndentBox.setChecked(self.db["general"]["autoIndent"])
        self.ui.deleteEmptyNotesBox.setChecked(self.db["general"]["deleteEmptyNotes"])
        self.ui.safeDeleteBox.setChecked(self.db["general"]["safeDelete"])
        self.ui.notesDbLine.setText(self.db["general"]["notesDb"])

        # Fetch clipboard
        self.ui.fetchClearBox.setChecked(self.db["general"]["fetchClear"])
        self.ui.fetchUrlBox.setChecked(self.db["general"]["fetchUrl"])
        self.ui.fetchFileBox.setChecked(self.db["general"]["fetchFile"])
        self.ui.fetchTxtBox.setChecked(self.db["general"]["fetchTxt"])
        self.ui.fetchIconBox.setChecked(self.db["general"]["fetchIcon"])

        # Hotkeys
        self.ui.hotkeyBox.setChecked(self.db["general"]["hotkeys"])
        self.hotkeyEnumerate()

        # Default actions
        self.ui.leftClickCombo.setCurrentText(self.db["actions"]["leftAction"])
        self.ui.middleClickCombo.setCurrentText(self.db["actions"]["middleAction"])
        self.ui.startupCombo.setCurrentText(self.db["actions"]["startupAction"])
        self.ui.cmdLeftLine.setText(self.db["actions"]["leftCmd"])
        self.ui.cmdMiddleLine.setText(self.db["actions"]["middleCmd"])
        self.ui.cmdStartupLine.setText(self.db["actions"]["startupCmd"])
        self.actionToggleExecWidgets()

        # Style presets
        self.presetEnumerate()

        # Style default
        font = QtGui.QFont()
        font.setFamily(self.styleDefault["fontFamily"])
        self.ui.styleFontFamilyCombo.setCurrentFont(font)
        self.ui.styleWidthBox.setValue(self.styleDefault["width"])
        self.ui.styleHeightBox.setValue(self.styleDefault["height"])
        self.ui.styleFontSizeBox.setValue(self.styleDefault["fontSize"])
        self.ui.stylePinBox.setChecked(self.db["styleDefault"]["pin"])
        self.ui.styleSizegripBox.setChecked(self.db["styleDefault"]["sizeGrip"])
        self.ui.nameTextLine.setText(self.db["general"]["nameText"])
        self.ui.nameImageLine.setText(self.db["general"]["nameImage"])
        self.ui.framelessBox.setChecked(self.db["general"]["frameless"])

        # Context menus
        self.ui.menuMotherAvailableList.clear()
        self.ui.menuMotherSelectedList.clear()
        self.ui.menuMotherSelectedList.addItems(self.db["menus"]["mother"])
        menuMotherActions = ['(Separator)', 'Toggle actives', 'New note', 'Fetch clipboard', 'Show all', 'Hide all', 'Reverse all', 'Reset positions', 'Folders list', 'Delete folders', 'Notes list', 'Preferences', 'Quit']
        menuMotherActions.sort()
        for item in menuMotherActions:
            if item not in self.db["menus"]["mother"] or item == "(Separator)":
                self.ui.menuMotherAvailableList.addItem(item)

        self.ui.menuChildAvailableList.clear()
        self.ui.menuChildSelectedList.clear()
        self.ui.menuChildSelectedList.addItems(self.db["menus"]["child"])
        menuChildActions = ['(Separator)', 'Undo', 'Redo', 'Hide', 'Pin', 'Rename', 'Selection to lowercase', 'Selection to uppercase', 'Sort selection', 'Toggle wordwrap', 'Special paste', 'Toggle sizegrip', 'New note', 'Delete',  'Save as', 'Search', 'Move to folder', 'Style', 'Copy to clipboard']
        menuChildActions.sort()
        for item in menuChildActions:
            if item not in self.db["menus"]["child"] or item == "(Separator)":
                self.ui.menuChildAvailableList.addItem(item)

    def reset(self):
        self.db["general"] = copyDict(PREFERENCES_DEFAULT["general"])
        self.db["actions"] = copyDict(PREFERENCES_DEFAULT["actions"])
        self.db["hotkeys"] = copyDict(PREFERENCES_DEFAULT["hotkeys"])
        self.db["menus"] = copyDict(PREFERENCES_DEFAULT["menus"])
        self.db["stylePresets"] = copyDict(PREFERENCES_DEFAULT["stylePresets"])
        self.db["styleDefault"] = copyDict(PREFERENCES_DEFAULT["styleDefault"])
        self.styleDefault = copyDict(PREFERENCES_DEFAULT["styleDefault"])
        self.load()

    def save(self, child=None):
        if child:
            child.load()
            child.set("width", self.styleDefault["width"])
            child.set("height", self.styleDefault["height"])
            child.set("background", self.styleDefault["background"])
            child.set("foreground", self.styleDefault["foreground"])
            child.set("fontSize", self.styleDefault["fontSize"])
            child.set("fontFamily", self.styleDefault["fontFamily"])
            child.save()
        else:
            # General settings
            self.db["general"]["nameText"] = self.ui.nameTextLine.text()
            self.db["general"]["nameImage"] = self.ui.nameImageLine.text()
            self.db["general"]["minimize"] = self.ui.minimizeBox.isChecked()
            self.db["general"]["autoIndent"] = self.ui.autoIndentBox.isChecked()
            self.db["general"]["safeDelete"] = self.ui.safeDeleteBox.isChecked()
            self.db["general"]["deleteEmptyNotes"] = self.ui.deleteEmptyNotesBox.isChecked()
            self.db["general"]["frameless"] = self.ui.framelessBox.isChecked()
            if not self.db["general"]["notesDb"] == self.ui.notesDbLine.text():
                self.changeNotesPath(self.ui.notesDbLine.text())

            # Fetch clipboard
            self.db["general"]["fetchClear"] = self.ui.fetchClearBox.isChecked()
            self.db["general"]["fetchUrl"] = self.ui.fetchUrlBox.isChecked()
            self.db["general"]["fetchFile"] = self.ui.fetchFileBox.isChecked()
            self.db["general"]["fetchTxt"] = self.ui.fetchTxtBox.isChecked()
            self.db["general"]["fetchIcon"] = self.ui.fetchIconBox.isChecked()

            # Default actions
            self.db["actions"]["leftAction"] = self.ui.leftClickCombo.currentText()
            self.db["actions"]["middleAction"] = self.ui.middleClickCombo.currentText()
            self.db["actions"]["startupAction"] = self.ui.startupCombo.currentText()
            self.db["actions"]["leftCmd"] = self.ui.cmdLeftLine.text()
            self.db["actions"]["middleCmd"] = self.ui.cmdMiddleLine.text()
            self.db["actions"]["startupCmd"] = self.ui.cmdStartupLine.text()

            # Style default
            self.db["styleDefault"]["pin"] = self.ui.stylePinBox.isChecked()
            self.db["styleDefault"]["sizeGrip"] = self.ui.styleSizegripBox.isChecked()

            # Hotkeys
            self.db["general"]["hotkeys"] = self.ui.hotkeyBox.isChecked()

            # Mother context menu
            menuMotherItems = []
            for item in range(self.ui.menuMotherSelectedList.count()):
                menuMotherItems.append(self.ui.menuMotherSelectedList.item(item).text())
            self.db["menus"]["mother"] = menuMotherItems

            # Child context menu
            menuChildItems = []
            for item in range(self.ui.menuChildSelectedList.count()):
                menuChildItems.append(self.ui.menuChildSelectedList.item(item).text())
            self.db["menus"]["child"] = menuChildItems

    def sanitizeString(self, string, unwanted):
        for c in unwanted:
            string = string.replace(c, '')
        return string

    def menuChildAddEvent(self):
        item = self.ui.menuChildAvailableList.currentItem()
        if item:
            if item.text() == "(Separator)":
                self.ui.menuChildSelectedList.addItem(item)
                self.ui.menuChildSelectedList.addItem(item.text())
            else:
                row = self.ui.menuChildAvailableList.currentRow()
                item = self.ui.menuChildAvailableList.takeItem(row)
                self.ui.menuChildSelectedList.addItem(item)

    def menuChildRemoveEvent(self):
        row = self.ui.menuChildSelectedList.currentRow()
        item = self.ui.menuChildSelectedList.takeItem(row)
        if item:
            if not item.text() == "(Separator)":
                self.ui.menuChildAvailableList.addItem(item)

    def menuMotherAddEvent(self):
        item = self.ui.menuMotherAvailableList.currentItem()
        if item:
            if item.text() == "(Separator)":
                self.ui.menuMotherSelectedList.addItem(item)
                self.ui.menuMotherSelectedList.addItem(item.text())
            else:
                row = self.ui.menuMotherAvailableList.currentRow()
                item = self.ui.menuMotherAvailableList.takeItem(row)
                self.ui.menuMotherSelectedList.addItem(item)

    def menuMotherRemoveEvent(self):
        row = self.ui.menuMotherSelectedList.currentRow()
        item = self.ui.menuMotherSelectedList.takeItem(row)
        if item:
            if not item.text() == "(Separator)":
                self.ui.menuMotherAvailableList.addItem(item)

    def changeNotesPath(self, path):
        # Validation of a new notes database path
        path = os.path.expanduser(path)
        path = self.sanitizeString(path, ':*?"<>|')
        if not path.endswith("/"):
            path += "/"
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except PermissionError:
                logger.critical("PermissionError: could not create directory '%s'" % path)
                return False
        self.db["general"]["notesDb"] = path
        self.preferences.set("general", "notesDb", path)

        # Close old notes and load content from new folder
        for child in self.parent.children:
            self.parent.children[child].name = ""
            self.parent.children[child].close()
        self.parent.children = {}
        self.parent.lastActive = ""
        self.parent.load(path)
        logger.info("Unloaded all notes")
        logger.info("Loading notes from folder '%s'" % path)

    def updateFrames(self):
        # Override of window manager frame
        for name in self.parent.children:
            isVisible = self.parent.children[name].isVisible()
            self.parent.children[name].refreshWindowState(updateFrame=True)
            time.sleep(0.1)
            if isVisible:
                self.parent.children[name].display()

    def closeEvent(self, event):
        if self.done:
            if self.genre == "Mother" or self.ui.styleDefaultBox.isChecked():
                self.db["styleDefault"] = self.styleDefault
                frameChanged = not self.ui.framelessBox.isChecked() == self.preferences.query("general", "frameless")

            # Set style of all children
            if self.ui.styleAllBox.isChecked():
                if self.genre == "Child":
                    children = self.parent.parent.children
                elif self.genre == "Mother":
                    children = self.parent.children

                for f in list(children):
                    self.save(children[f].profile)
                    children[f].loadStyle()

            # Update preferences database
            self.save()
            self.preferences.db = self.db
            self.preferences.save()

            # Update child attributes
            if self.genre == "Mother":
                if frameChanged:
                    self.updateFrames()

            elif self.genre == "Child":
                # Set style for current child
                self.save(self.parent.profile)
                self.parent.resize(self.parent.profile.query("width"), self.parent.profile.query("height"))

        elif self.genre == "Child":
            self.parent.loadStyle()
        event.accept()

    def menuEvent(self):
        index = self.ui.sideMenuList.currentRow()
        self.ui.stackedWidget.setCurrentIndex(index)
        self.parent.preferencesMenuIndex = index

    def actionToggleExecWidgets(self):
        if self.ui.leftClickCombo.currentText() == "Exec":
            self.ui.cmdLeftLabel.show()
            self.ui.cmdLeftLine.show()
            self.ui.cmdLeftLine.show()
        else:
            self.ui.cmdLeftLabel.hide()
            self.ui.cmdLeftLine.hide()
            self.ui.cmdLeftLine.hide()

        if self.ui.middleClickCombo.currentText() == "Exec":
            self.ui.cmdMiddleLabel.show()
            self.ui.cmdMiddleLine.show()
            self.ui.cmdMiddleLine.show()
        else:
            self.ui.cmdMiddleLabel.hide()
            self.ui.cmdMiddleLine.hide()
            self.ui.cmdMiddleLine.hide()

        if self.ui.startupCombo.currentText() == "Exec":
            self.ui.cmdStartupLabel.show()
            self.ui.cmdStartupLine.show()
        else:
            self.ui.cmdStartupLabel.hide()
            self.ui.cmdStartupLine.hide()

    def styleUpdateChild(self):
        if self.genre == "Child":
            font = self.parent.ui.textEdit.font()
            font.setPointSize(self.styleDefault["fontSize"])
            font.setFamily(self.styleDefault["fontFamily"])
            self.parent.ui.textEdit.setFont(font)
            self.parent.setBackground(self.styleDefault["background"])
            self.parent.setForeground(self.styleDefault["foreground"])
            self.parent.resize(self.styleDefault["width"], self.styleDefault["height"])

    def styleUpdateFontSize(self):
        self.styleDefault["fontSize"] = self.ui.styleFontSizeBox.value()
        self.styleUpdateChild()

    def styleUpdateFontFamily(self):
        self.styleDefault["fontFamily"] = self.ui.styleFontFamilyCombo.currentText()
        self.styleUpdateChild()

    def stylePickLayerColor(self, layer):
        currentColor = self.styleDefault[layer]
        color = self.stylePickColor(layer, currentColor)
        if not color.isValid():
            color = QtGui.QColor(currentColor)
        self.styleDefault[layer] = color.name()
        self.styleUpdateChild()

    def stylePickColor(self, layer, color):
        self.colorWidget = QtWidgets.QColorDialog(QtGui.QColor(color))
        self.colorWidget.setWindowFlags(self.colorWidget.windowFlags() | Qt.WindowStaysOnTopHint)
        self.colorWidget.currentColorChanged.connect(lambda: self.styleColorChanged(layer))
        self.colorWidget.exec_()
        return self.colorWidget.selectedColor()

    def styleColorChanged(self, layer):
        color = self.colorWidget.currentColor()
        self.styleDefault[layer] = color.name()
        self.styleUpdateChild()

    def styleUpdateWidth(self):
        self.styleDefault["width"] = self.ui.styleWidthBox.value()
        self.styleUpdateChild()

    def styleUpdateHeight(self):
        self.styleDefault["height"] = self.ui.styleHeightBox.value()
        self.styleUpdateChild()

    def presetPickColor(self, preview, color):
        self.colorWidget = QtWidgets.QColorDialog(QtGui.QColor(color))
        self.colorWidget.setWindowFlags(self.colorWidget.windowFlags() | Qt.WindowStaysOnTopHint)
        self.colorWidget.currentColorChanged.connect(lambda: self.presetColorChanged(preview))
        self.colorWidget.exec_()
        return self.colorWidget.selectedColor()

    def presetPickBackgroundColor(self, preview):
        row, name, foreground, background = self.presetGetSelection()
        color = self.presetPickColor("background", background)
        if color.isValid():
            item = centeredTableItem(color.name())
            self.db["stylePresets"][name]["background"] = color.name()
        else:
            item = centeredTableItem(background)
        self.ui.presetTable.setItem(row, 2, item)
        self.presetUpdatePreview(row)

    def presetPickForegroundColor(self, preview):
        row, name, foreground, background = self.presetGetSelection()
        color = self.presetPickColor("foreground", foreground)
        if color.isValid():
            item = centeredTableItem(color.name())
            self.db["stylePresets"][name]["foreground"] = color.name()
        else:
            item = centeredTableItem(foreground)
        self.ui.presetTable.setItem(row, 1, item)
        self.presetUpdatePreview(row)

    def presetColorChanged(self, preview):
        row = self.ui.presetTable.currentRow()
        color = self.colorWidget.currentColor()
        if preview == "background":
            item = centeredTableItem(color.name())
            self.ui.presetTable.setItem(row, 2, item)
        elif preview == "foreground":
            item = centeredTableItem(color.name())
            self.ui.presetTable.setItem(row, 1, item)
        self.presetUpdatePreview(row)

    def presetGetRow(self, row):
        name = self.ui.presetTable.item(row, 0).text()
        foreground = self.ui.presetTable.item(row, 1).text()
        background = self.ui.presetTable.item(row, 2).text()
        return(name, foreground, background)

    def presetGetSelection(self):
        if self.ui.presetTable.rowCount() == 0:
            self.presetNewEvent()
            self.ui.presetTable.setCurrentCell(0, 1)

        row = self.ui.presetTable.currentRow()
        if row < 0:
            row = 0
            self.ui.presetTable.setCurrentCell(0, 1)

        name = self.ui.presetTable.item(row, 0).text()
        foreground = self.ui.presetTable.item(row, 1).text()
        background = self.ui.presetTable.item(row, 2).text()
        return(row, name, foreground, background)

    def presetSelectEvent(self):
        row, name, foreground, background = self.presetGetSelection()
        self.ui.presetNameLine.setText(name)

    def presetUpdatePreview(self, row):
        name, foreground, background = self.presetGetRow(row)
        nameItem = QtWidgets.QTableWidgetItem(name)
        nameItem.setForeground(QtGui.QColor(foreground))
        nameItem.setBackground(QtGui.QColor(background))
        nameItem.setFlags(Qt.NoItemFlags)  # Disable selection for that column
        self.ui.presetTable.setItem(row, 0, QtWidgets.QTableWidgetItem(nameItem))

    def presetEnumerate(self):
        self.ui.presetTable.setRowCount(0)  # Clear all content
        row = 0
        for entry in self.db["stylePresets"]:
            background = self.db["stylePresets"][entry]["background"]
            foreground = self.db["stylePresets"][entry]["foreground"]
            foregroundItem = centeredTableItem(foreground)
            backgroundItem = centeredTableItem(background)
            self.ui.presetTable.insertRow(row)
            self.ui.presetTable.setItem(row, 0, QtWidgets.QTableWidgetItem(entry))
            self.ui.presetTable.setItem(row, 1, QtWidgets.QTableWidgetItem(foregroundItem))
            self.ui.presetTable.setItem(row, 2, QtWidgets.QTableWidgetItem(backgroundItem))
            self.presetUpdatePreview(row)
            row += 1

    def presetDeleteEvent(self):
        if self.ui.presetTable.currentRow() > -1:
            row, name, foreground, background = self.presetGetSelection()
            del self.db["stylePresets"][name]
            self.presetTable.removeRow(row)

    def presetRenameEvent(self):
        row, name, foreground, background = self.presetGetSelection()
        newName = self.ui.presetNameLine.text()
        self.db["stylePresets"][newName] = self.db["stylePresets"].pop(name)
        self.ui.presetTable.setItem(row, 0, QtWidgets.QTableWidgetItem(newName))
        self.presetUpdatePreview(row)

    def presetNewEvent(self):
        name = self.preferences.query("general", "nameText")
        name = getNameIndex(name, self.db["stylePresets"])
        foreground = self.preferences.query("styleDefault", "foreground")
        background = self.preferences.query("styleDefault", "background")
        self.db["stylePresets"][name] = {}
        self.db["stylePresets"][name]["foreground"] = foreground
        self.db["stylePresets"][name]["background"] = background
        self.presetTable.insertRow(0)
        nameItem = centeredTableItem(name)
        foregroundItem = centeredTableItem(foreground)
        backgroundItem = centeredTableItem(background)
        self.ui.presetTable.setItem(0, 0, QtWidgets.QTableWidgetItem(nameItem))
        self.ui.presetTable.setItem(0, 1, QtWidgets.QTableWidgetItem(foregroundItem))
        self.ui.presetTable.setItem(0, 2, QtWidgets.QTableWidgetItem(backgroundItem))
        self.presetUpdatePreview(0)

    def hotkeyEnumerate(self):
        self.ui.hotkeyTable.setRowCount(0)  # Clear all content
        row = 0
        for hotkey in sorted(self.db["hotkeys"]["ctrl"]):
            self.ui.hotkeyTable.insertRow(row)
            self.ui.hotkeyTable.setItem(row, 0, QtWidgets.QTableWidgetItem("Ctrl + " + hotkey))
            self.ui.hotkeyTable.setItem(row, 1, QtWidgets.QTableWidgetItem(self.db["hotkeys"]["ctrl"][hotkey].capitalize()))
            row += 1

        for hotkey in sorted(self.db["hotkeys"]["shift"]):
            self.ui.hotkeyTable.insertRow(row)
            self.ui.hotkeyTable.setItem(row, 0, QtWidgets.QTableWidgetItem("Shift + " + hotkey))
            self.ui.hotkeyTable.setItem(row, 1, QtWidgets.QTableWidgetItem(self.db["hotkeys"]["shift"][hotkey].capitalize()))
            row += 1

        for hotkey in sorted(self.db["hotkeys"]["ctrlShift"]):
            self.ui.hotkeyTable.insertRow(row)
            self.ui.hotkeyTable.setItem(row, 0, QtWidgets.QTableWidgetItem("Ctrl + Shift + " + hotkey))
            self.ui.hotkeyTable.setItem(row, 1, QtWidgets.QTableWidgetItem(self.db["hotkeys"]["ctrlShift"][hotkey].capitalize()))
            row += 1

    def hotkeyAdd(self):
        row = self.ui.hotkeyTable.currentRow()
        hotkey = self.ui.hotkeyKeyLine.text()
        action = self.ui.hotkeyActionCombo.currentText()
        if hotkey[:15] == "Ctrl + Shift + ":
            db = "ctrlShift"
            key = hotkey[15:]
        elif hotkey[:8] == "Shift + ":
            db = "shift"
            key = hotkey[8:]
        elif hotkey[:7] == "Ctrl + ":
            db = "ctrl"
            key = hotkey[7:]

        if hotkey and action:
            self.db["hotkeys"][db][key] = action
            self.hotkeyEnumerate()
            self.ui.hotkeyKeyLine.clear()
            self.ui.hotkeyActionCombo.setCurrentText('')

    def hotkeyDelete(self):
        row = self.ui.hotkeyTable.currentRow()
        selectedKey = self.ui.hotkeyTable.item(row, 0)
        if selectedKey:
            selectedKey = selectedKey.text()
            if selectedKey[:15] == "Ctrl + Shift + ":
                del self.db["hotkeys"]["ctrlShift"][selectedKey[15:]]
            elif selectedKey[:8] == "Shift + ":
                del self.db["hotkeys"]["shift"][selectedKey[8:]]
            elif selectedKey[:7] == "Ctrl + ":
                del self.db["hotkeys"]["ctrl"][selectedKey[7:]]
            self.ui.hotkeyTable.removeRow(row)

    def hotkeyEventFilter(self, event):
        eventType = event.type()
        if eventType == QtCore.QEvent.KeyPress or eventType == QtCore.QEvent.KeyRelease:
            self.modifier["ctrl"] = (event.modifiers() == Qt.ControlModifier)
            self.modifier["shift"] = (event.modifiers() == Qt.ShiftModifier)
            self.modifier["ctrlShift"] = int(event.modifiers()) == (Qt.ControlModifier + Qt.ShiftModifier)

        if eventType == QtCore.QEvent.KeyPress or eventType == QtCore.QEvent.Wheel:
            modifier = ""
            if self.modifier["ctrlShift"] or not self.modifier["shift"]:
                modifier = "Ctrl + " + modifier
            if self.modifier["shift"] or self.modifier["ctrlShift"]:
                modifier += "Shift + "

        if eventType == QtCore.QEvent.KeyPress:
            key = QtGui.QKeySequence(event.key()).toString()
            try:
                key.encode('utf-8')
                self.ui.hotkeyKeyLine.setText(modifier + key)
            except UnicodeEncodeError:
                pass  # Filter unwanted unicode characters from modifiers

        elif eventType == QtCore.QEvent.Wheel:
            if int(event.angleDelta().y()) > 0:
                self.ui.hotkeyKeyLine.setText(modifier + "Wheel Up")
            else:
                self.ui.hotkeyKeyLine.setText(modifier + "Wheel Down")

        return QtWidgets.QLineEdit.event(self.ui.hotkeyKeyLine, event)
