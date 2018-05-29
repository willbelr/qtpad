#!/usr/bin/python3
import json
import os
import sys
from PyQt5 import QtGui, QtWidgets, QtCore, uic
from PyQt5.QtCore import Qt

try:
    import qtpad.gui_child
    from qtpad.preferences import PreferencesDialog, Profile
    from qtpad.common import *
except ImportError:
    from preferences import PreferencesDialog, Profile
    from common import *

# Init common settings
LOCAL_DIR, ICONS_DIR, PREFERENCES_FILE, PROFILES_FILE = getStaticPaths()
logger = getLogger()


class Child(QtWidgets.QWidget):
    def __init__(self, parent, path, popup=False, image=None, text=None):
        super().__init__()

        # Load the ui file in case the gui modules are not loaded
        if "qtpad.gui_child" in sys.modules:
            self.ui = qtpad.gui_child.Ui_Form()
            self.ui.setupUi(self)
        else:
            self.ui = uic.loadUi(LOCAL_DIR + 'gui_child.ui', self)

        # Load common settings
        notesDir = parent.preferences.query("general", "notesDb")
        self.parent = parent
        self.path = path
        self.name = path[len(notesDir):].rsplit(".", 1)[0]
        self.isImage = bool(image)
        self.preferences = parent.preferences
        self.profile = Profile(self, index=len(parent.children))
        self.setWindowTitle(self.name)
        self.ui.titleLabel.setText(self.name)
        self.borderColor = QtGui.QColor("#444444")
        self.modifier = {"ctrl": False, "shift": False, "ctrlShift": False}
        folder = path[len(notesDir):]
        if folder.find("/") == -1:
            self.folder = ""
        else:
            self.folder = folder.rsplit("/", 1)[0]

        # Hide window from system taskbar
        if os.environ.get('DESKTOP_SESSION') == "openbox":
            self.setAttribute(Qt.WA_X11NetWmWindowTypeToolBar)
        else:
            self.setAttribute(Qt.WA_X11NetWmWindowTypeUtility)

        # Init frame events
        self.saveTimer = QtCore.QTimer(singleShot=True)  # Save widget size only once the resize event is done
        self.saveTimer.timeout.connect(self.saveGeometry)

        self.ui.titleLabel.mousePressEvent = self.titleLabelMousePressEvent
        self.ui.titleLabel.mouseMoveEvent = self.titleLabelMouseMoveEvent
        self.sizeGrip = QtWidgets.QSizeGrip(self)
        self.ui.bottomLayout.addWidget(self.sizeGrip)
        self.ui.bottomLayout.setAlignment(self.sizeGrip, Qt.AlignRight)

        # Init context menus
        icons = ["hide", "delete", "rename", "tray", "pin_menu", "pin_title", "toggle", "style", "image",
                "file_inactive", "preferences", "new", "folder_active", "folder_inactive", "copy", "lowercase",
                "paste", "redo", "save", "search", "sizegrip", "sort", "undo", "uppercase", "wordwrap"]
        self.icon = {}
        for icon in icons:
            self.icon[icon] = QtGui.QIcon(ICONS_DIR + icon + ".svg")
        self.menu = QtWidgets.QMenu()
        self.menu.aboutToShow.connect(self.menuRefresh)
        self.styleMenu = QtWidgets.QMenu("Style")
        self.styleMenu.setIcon(self.icon["style"])
        self.moveMenu = QtWidgets.QMenu("Move to folder...")
        self.moveMenu.setIcon(self.icon["folder_active"])

        # Apply settings and display children
        if image:
            self.initImage(image)
        else:
            self.initText(text)
        self.refreshWindowState(updateFrame=True)
        if popup or self.profile.query("pin") or not self.preferences.query("general", "minimize"):
            self.display(updateState=False)

    def initText(self, text):
        self.ui.imageLabel.hide()
        self.ui.textEdit.installEventFilter(self)
        self.ui.textEdit.dropEvent = self.dropEvent
        self.ui.textEdit.keyPressEvent = self.keyPressEvent
        self.ui.textEdit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.textEdit.customContextMenuRequested.connect(lambda: self.menu.popup(QtGui.QCursor.pos()))
        self.ui.textEdit.setAttribute(Qt.WA_TranslucentBackground)
        if text:
            self.ui.textEdit.setPlainText(text)
        elif os.path.isfile(self.path):
            with open(self.path) as f:
                self.ui.textEdit.setPlainText(f.read())
        else:
            with open(self.path, 'w') as f:
                f.write('')

    def initImage(self, image):
        self.ui.textEdit.hide()
        self.ui.imageLabel.installEventFilter(self)
        self.ui.imageLabel.setScaledContents(True)
        self.ui.imageLabel.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.imageLabel.customContextMenuRequested.connect(lambda: self.menu.popup(QtGui.QCursor.pos()))
        self.ui.imageLabel.setFocusPolicy(Qt.StrongFocus)
        if os.path.isfile(self.path):
            image = QtGui.QPixmap(self.path)
            width, height = image.width(), image.height()
        else:
            f = QtCore.QFile(self.preferences.query("general", "notesDb") + self.name + ".png")
            f.open(QtCore.QIODevice.WriteOnly)
            image.save(f, "PNG")
            width, height = image.width(), image.height()
            self.profile.load()
            self.profile.set("width", width)
            self.profile.set("height", height)
            self.profile.save()

        # Load the image file and set the widget size
        widthMax = round(QtWidgets.QDesktopWidget().screenGeometry().width() * 0.8)
        heightMax = round(QtWidgets.QDesktopWidget().screenGeometry().height() * 0.8)
        if width > widthMax or height > heightMax:
            width = widthMax
            height = heightMax
        self.ui.imageLabel.setPixmap(image.scaled(width, height, Qt.KeepAspectRatio))

    def eventFilter(self, object, event):
        eventType = event.type()
        if eventType == QtCore.QEvent.KeyPress or eventType == QtCore.QEvent.KeyRelease:
            self.modifier["ctrl"] = (event.modifiers() == Qt.ControlModifier)
            self.modifier["shift"] = (event.modifiers() == Qt.ShiftModifier)
            self.modifier["ctrlShift"] = int(event.modifiers()) == (Qt.ControlModifier + Qt.ShiftModifier)

        if eventType == QtCore.QEvent.KeyPress:
            self.hotkeyParse(event)
            self.autoIndent(event)

        elif eventType == QtCore.QEvent.Wheel:
            self.hotkeySpecial(event)

        elif eventType == QtCore.QEvent.FocusOut:
            if self.name:
                self.saveContent()

        elif eventType == QtCore.QEvent.Resize:
            self.saveTimer.start(400)  # Workaround to avoid saving after each pixel update

        if not self.isImage:
            if eventType == QtCore.QEvent.Show:
                self.parent.lastActive = self

            elif eventType == QtCore.QEvent.FocusIn:
                self.parent.lastActive = self
                self.load(self.name)

        return QtCore.QObject.event(object, event)

    def dropEvent(self, event):
        QtWidgets.QPlainTextEdit.dropEvent(self.ui.textEdit, event)
        self.saveContent()

    def autoIndent(self, event):
        if self.preferences.query("general", "autoIndent"):
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                cursor = self.ui.textEdit.textCursor()
                position = cursor.position()

                # Get indent of previous line
                cursor.movePosition(QtGui.QTextCursor.Up)
                cursor.movePosition(QtGui.QTextCursor.StartOfLine)
                cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
                line = cursor.selectedText()
                indent_tab = len(line) - len(line.lstrip("\t"))
                indent_space = (len(line) - len(line.lstrip("    "))) / 4
                indent = indent_tab + int(indent_space)

                # Insert indent before current line and restore position
                cursor.movePosition(QtGui.QTextCursor.Down)
                cursor.movePosition(QtGui.QTextCursor.StartOfLine)
                for tab in range(0, indent):
                    cursor.insertText("\t")
                cursor.setPosition(position)

    def hotkeySpecial(self, event):
        if self.preferences.query("general", "hotkeys"):
            hotkeys = self.preferences.db["hotkeys"]
            # if event.type() == QtCore.QEvent.Wheel:
            if int(event.angleDelta().y()) > 0:
                delta = "Wheel Up"
            else:
                delta = "Wheel Down"

            for modifier in hotkeys:
                if hotkeys[modifier].get(delta) and self.modifier[modifier]:
                    self.hotkeyAction(hotkeys[modifier][delta])

    def hotkeyParse(self, event):
        if self.preferences.query("general", "hotkeys"):
            hotkeys = self.preferences.db["hotkeys"]
            key = QtGui.QKeySequence(event.key()).toString()
            for modifier in hotkeys:
                if self.modifier.get(modifier):
                    for hotkey in hotkeys[modifier]:
                        if key == hotkey:
                            return self.hotkeyAction(hotkeys[modifier][hotkey])

        QtWidgets.QPlainTextEdit.keyPressEvent(self.ui.textEdit, event)
        self.handleAsterisk()

    def styleAddPreset(self):
        msg = QtWidgets.QInputDialog()
        msg.setInputMode(QtWidgets.QInputDialog.TextInput)
        msg.setWindowFlags(msg.windowFlags() | Qt.WindowStaysOnTopHint)
        msg.setWindowTitle("Add style preset")
        msg.setLabelText("Enter preset name:")
        msg.setFixedSize(250, 100)
        accept = msg.exec_()
        name = msg.textValue()
        name = self.sanitizeString(name, '\/:*?"<>|')
        if accept and name:
            if name in self.preferences.db["stylePresets"]:
                logger.info("Name '%s' already exist, name index has been appended" % name)
                name = getNameIndex(name, self.preferences.db["stylePresets"])
            self.preferences.db["stylePresets"][name] = {}
            self.preferences.db["stylePresets"][name]["foreground"] = self.profile.query("foreground")
            self.preferences.db["stylePresets"][name]["background"] = self.profile.query("background")
            self.preferences.save()

    def styleMenuRefresh(self):
        self.styleMenu.clear()
        self.styleMenu.addAction(self.icon["preferences"], "Customize", lambda: PreferencesDialog(self))
        self.styleMenu.addAction(self.icon["preferences"], "Save current style...", self.styleAddPreset)
        self.styleMenu.addSeparator()

        # Load style presets and replace transparency with background color, foreground with 'foreground'
        for entry in self.preferences.db["stylePresets"]:
            background = self.preferences.db["stylePresets"][entry]["background"]
            foreground = self.preferences.db["stylePresets"][entry]["foreground"]
            pixmap = QtGui.QPixmap(ICONS_DIR + "rename.svg")
            painter = QtGui.QPainter(pixmap)
            painter.setCompositionMode(painter.CompositionMode_Xor)
            painter.fillRect(pixmap.rect(), QtGui.QColor(background))
            painter.setCompositionMode(painter.CompositionMode_Overlay)
            painter.fillRect(pixmap.rect(), QtGui.QColor(foreground))
            painter.end()
            icon = QtGui.QIcon(pixmap)
            self.styleMenu.addAction(icon, entry, lambda background=background, foreground=foreground: self.setStyle(background, foreground, updateProfile=True))

    def menuAddOption(self, option):
        option = option.lower()
        if option == "(separator)":
            self.menu.addSeparator()

        elif option == "undo":
            self.menu.addAction(self.icon["undo"], 'Undo', self.ui.textEdit.undo)

        elif option == "redo":
            self.menu.addAction(self.icon["redo"], 'Redo', self.ui.textEdit.redo)

        elif option == "hide":
            self.menu.addAction(self.icon["hide"], 'Hide', self.hide)

        elif option == "pin":
            self.menu.addAction(self.icon["pin_menu"], 'Pin', self.pin)

        elif option == "rename":
            self.menu.addAction(self.icon["rename"], 'Rename', self.renamePrompt)

        elif option == "selection to lowercase":
            self.menu.addAction(self.icon["lowercase"], 'Selection to lowercase', lambda: self.hotkeyAction("selection to lowercase"))

        elif option == "selection to uppercase":
            self.menu.addAction(self.icon["uppercase"], 'Selection to uppercase', lambda: self.hotkeyAction("selection to uppercase"))

        elif option == "sort selection":
            self.menu.addAction(self.icon["sort"], 'Sort selection', lambda: self.textAction("sort selection"))

        elif option == "toggle wordwrap":
            self.menu.addAction(self.icon["wordwrap"], 'Toggle word wrap', self.toggleWordWrap)

        elif option == "special paste":
            self.menu.addAction(self.icon["paste"], 'Special paste', lambda: self.hotkeyAction("special paste"))

        elif option == "toggle sizegrip":
            self.menu.addAction(self.icon["sizegrip"], 'Toggle sizegrip', lambda: self.hotkeyAction("toggle sizegrip"))

        elif option == "new note":
            self.menu.addAction(self.icon["new"], 'New note', lambda: self.parent.action("New note"))

        elif option == "delete":
            self.menu.addAction(self.icon["delete"], 'Delete', self.delete)

        elif option == "save as":
            if self.isImage:
                self.menu.addAction(self.icon["save"], 'Save image as', self.saveImageToFile)
            else:
                self.menu.addAction(self.icon["save"], 'Save text as', self.saveTextToFile)

        elif option == "search":
            self.menu.addAction(self.icon["search"], 'Search', lambda: self.hotkeyAction("search"))

        elif option == "move to folder":
            self.moveMenu.clear()
            self.parent.loadFolders() # Make sure each folders have a key in preferences database
            for folder in self.parent.listFolders(self.preferences.query("general", "notesDb")):
                if not folder == self.folder:
                    self.moveMenu.addAction(self.parent.pollFolderIcon(folder), folder, lambda folder=folder: self.moveToFolder(folder))
            self.moveMenu.addSeparator()
            if self.folder:
                self.moveMenu.addAction(self.icon["hide"], "None", self.moveToFolder)
            self.moveMenu.addAction(self.icon["preferences"], "New folder", self.folderPrompt)
            self.menu.addMenu(self.moveMenu)

        elif option == "style":
            self.styleMenuRefresh()
            self.menu.addMenu(self.styleMenu)

        elif option == "copy to clipboard":
            if self.isImage:
                self.menu.addAction(self.icon["copy"], 'Copy to clipboard', self.saveImageToClipboard)
        else:
            logger.error("Invalid child menu option '%s'" % option)

    def menuRefresh(self):
        self.menu.clear()
        for option in self.preferences.query("menus", "child"):
            self.menuAddOption(option)

    def display(self, updateState=True, updatePosition=True):
        if updateState:
            self.refreshWindowState()
        if updatePosition:
            self.resize(self.profile.query("width"), self.profile.query("height"))
            self.move(self.profile.query("x"), self.profile.query("y"))
        self.show()
        self.loadStyle()
        self.activateWindow()
        logger.info("Displayed '" + self.name + "'")

    def load(self, name):
        if os.path.isfile(self.path):
            with open(self.path) as f:
                content = f.read()
            if not content == self.ui.textEdit.toPlainText():
                self.ui.textEdit.setPlainText(content)
                logger.info("Updated content of '" + self.name + "'")

    def saveContent(self):
        if not self.isImage:
            if self.windowTitle()[-1] == "*" or self.ui.titleLabel.text()[-1] == "*":
                self.setWindowTitle(self.windowTitle()[:-1])
                self.ui.titleLabel.setText(self.ui.titleLabel.text()[:-1])
            with open(self.path, 'w') as f:
                f.write(self.ui.textEdit.toPlainText())

    def saveGeometry(self):
        self.profile.load()
        self.profile.set("x", self.pos().x())
        self.profile.set("y", self.pos().y())
        if self.isImage:
            self.profile.set("width", self.ui.imageLabel.width())
            self.profile.set("height", self.ui.imageLabel.height())
        else:
            self.profile.set("width", self.width())
            self.profile.set("height", self.height())
        self.profile.save()

    def delete(self):
        if os.path.isfile(self.path):
            logger.warning("Removed '" + self.name + "' (user)")
            if self.preferences.query("general", "safeDelete") and os.stat(self.path).st_size > 0:
                msg = QtWidgets.QMessageBox()
                msg.setWindowFlags(msg.windowFlags() | Qt.WindowStaysOnTopHint)
                msg.setIcon(QtWidgets.QMessageBox.Warning)
                msg.setWindowTitle("Delete confirmation")
                msg.setText("Please confirm deletion of '" + self.name + "'")
                msg.setStandardButtons(QtWidgets.QMessageBox.Apply | QtWidgets.QMessageBox.Cancel)
                if msg.exec_() == QtWidgets.QMessageBox.Apply:
                    self.remove()
            else:
                self.remove()

    def remove(self):
        # Remove from profile list
        if self.name in self.profile.db:
            del self.profile.db[self.name]
            self.profile.save()

        # Remove from active list
        if self.name in self.preferences.db["actives"]:
            self.preferences.db["actives"].remove(self.name)
            self.preferences.set("actives", self.preferences.db["actives"])

        # Remove from loaded list
        if self.name in self.parent.children:
            del self.parent.children[self.name]

        # Remove from database
        if os.path.isfile(self.path):
            os.remove(self.path)

        # Close widget
        self.name = ""
        self.close()

    def pin(self):
        self.profile.save("pin", not self.profile.query("pin"))
        self.display(updatePosition=False)

    def moveToFolder(self, folder=""):
        # Make sure the destination folder exist
        if folder:
            notesDir = self.preferences.query("general", "notesDb")
            if not os.path.exists(notesDir + folder):
                os.makedirs(notesDir + folder)
            if folder not in self.preferences.db["folders"]:
                self.preferences.db["folders"][folder] = True
                self.preferences.save()

        # Erase previous folder from name (if any)
        if self.folder:
            newName = self.name[len(self.folder):].lstrip("/")
        else:
            newName = self.name

        # Append new folder to name (if any)
        if folder:
            newName = folder + "/" + newName

        # Handle name conflicts
        if newName in self.parent.children:
            newName = getNameIndex(newName, self.parent.children)

        # Apply new settings
        self.folder = folder
        self.rename(newName)

    def sanitizeString(self, string, unwanted):
        for c in unwanted:
            string = string.replace(c, '')
        return string

    def folderPrompt(self):
        msg = QtWidgets.QInputDialog()
        msg.setInputMode(QtWidgets.QInputDialog.TextInput)
        msg.setWindowFlags(msg.windowFlags() | Qt.WindowStaysOnTopHint)
        msg.setWindowTitle("Move '" + self.name + "'")
        msg.setLabelText("Enter the folder name:")
        msg.setFixedSize(250, 100)
        accept = msg.exec_()
        newName = msg.textValue()
        newName = self.sanitizeString(newName, '\/:*?"<>|')
        if accept and newName and not newName == self.folder:
            self.moveToFolder(newName)

    def renamePrompt(self):
        msg = QtWidgets.QInputDialog()
        msg.setInputMode(QtWidgets.QInputDialog.TextInput)
        msg.setWindowFlags(msg.windowFlags() | Qt.WindowStaysOnTopHint)
        msg.setWindowTitle("Rename '" + self.name + "'")
        msg.setLabelText("Enter the new name:")
        name = self.path.rsplit('/', 1)[-1].rsplit('.', 1)[0]
        msg.setTextValue(name)
        msg.setFixedSize(250, 100)
        accept = msg.exec_()
        newName = msg.textValue()
        newName = self.sanitizeString(newName, '\/:*?"<>|')
        if self.folder:
            newName = self.folder + "/" + newName
        if accept and newName:
            self.rename(newName)

    def rename(self, name):
        if name not in self.parent.children:
            notesDir = self.preferences.query("general", "notesDb")

            # Rename note file
            if os.path.isfile(self.path):
                try:
                    if self.isImage:
                        os.rename(self.path, notesDir + name + ".png")
                        self.path = notesDir + name + ".png"
                    else:
                        os.rename(self.path, notesDir + name + ".txt")
                        self.path = notesDir + name + ".txt"
                except OSError:
                    logger.error("Could not rename file (name too long?)")
                    name = self.name

            # Replace name in profiles database
            with open(PROFILES_FILE, "r+") as db:
                profiles = json.load(db)
                profiles[name] = profiles.pop(self.name)
                db.seek(0)
                db.truncate()
                db.write(json.dumps(profiles, indent=2, sort_keys=False))

            # Replace name in children list
            self.parent.children[name] = self.parent.children.pop(self.name)

            # Update child proprieties
            newName = self.path[len(notesDir):].rsplit(".", 1)[0]
            logger.info("Renamed '" + self.name + "' to '" + newName + "'")
            self.profile.path = self.path
            self.profile.name = newName
            self.setWindowTitle(newName)
            self.ui.titleLabel.setText(newName)

            # Change name in active list
            if self.name in self.preferences.db["actives"]:
                self.preferences.db["actives"].remove(self.name)
                self.preferences.db["actives"].append(newName)
                self.preferences.set("actives", self.preferences.db["actives"])

            # Update profile database
            self.name = newName
            self.profile.load()

    def setBackground(self, color):
        color = QtGui.QColor(color)
        palette = self.ui.textEdit.viewport().palette()
        palette.setColor(QtGui.QPalette.Base, color)  # textEdit
        palette.setColor(QtGui.QPalette.Background, self.borderColor)  # widget
        self.ui.textEdit.viewport().setPalette(palette)
        self.ui.textEdit.viewport().update()
        self.setPalette(palette)
        self.update()

    def setForeground(self, color):
        color = QtGui.QColor(color)
        palette = self.ui.textEdit.viewport().palette()
        palette.setColor(QtGui.QPalette.Text, color)  # textEdit
        palette.setColor(QtGui.QPalette.WindowText, color)  # label
        self.ui.textEdit.viewport().setPalette(palette)

    def setStyle(self, background, foreground, updateProfile):
        self.setBackground(background)
        self.setForeground(foreground)
        if updateProfile:
            self.profile.set("background", background)
            self.profile.set("foreground", foreground)
            self.profile.save()

    def loadStyle(self):
        font = self.ui.textEdit.font()
        font.setFamily(self.profile.query("fontFamily"))
        font.setPointSize(self.profile.query("fontSize"))
        self.ui.textEdit.setFont(font)
        self.setStyle(self.profile.query("background"), self.profile.query("foreground"), updateProfile=False)
        self.resize(self.profile.query("width"), self.profile.query("height"))
        logger.info("Loaded style for '" + self.name + "'")

    def refreshWindowState(self, updateFrame=False):
        # Handle window icon
        if self.profile.query("pin"):
            icon = self.icon["pin_title"]
        elif self.name in self.preferences.query("actives"):
            icon = self.icon["toggle"]
        else:
            icon = self.icon["tray"]
        self.ui.iconLabel.setPixmap(icon.pixmap(14, 14))
        self.setWindowIcon(icon)

        # Choose between native and custom frame
        if updateFrame:
            if self.preferences.query("general", "frameless"):
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
                self.setContentsMargins(1, 0, 1, 1)
                self.ui.closeButton.clicked.connect(self.close)
                with open(os.path.expanduser("~/.config/qtpad/frame.css")) as f:
                    stylesheet = f.read()
                    self.ui.iconLabel.setStyleSheet(stylesheet)
                    self.ui.titleLabel.setStyleSheet(stylesheet)
                    self.ui.closeButton.setStyleSheet(stylesheet)
                    border = stylesheet[stylesheet.find("QLabel#titleLabel"):]
                    start = border.find("background-color: ") + 18
                    self.borderColor = QtGui.QColor(border[start:start+7])
                self.ui.iconLabel.show()
                self.ui.titleLabel.show()
                self.ui.closeButton.show()
            else:
                self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
                self.setContentsMargins(0, 0, 0, 0)
                self.ui.iconLabel.hide()
                self.ui.titleLabel.hide()
                self.ui.closeButton.hide()

        # Handle resize corner
        if self.profile.query("sizeGrip") or self.preferences.query("general", "frameless"):
            self.sizeGrip.show()
        else:
            self.sizeGrip.hide()

        logger.info("Updated window state for '" + self.name + "'")

    def paintEvent(self, event):
        if self.preferences.query("general", "frameless"):
            # Draw a border for FramelessWindowHint
            painter = QtGui.QPainter(self)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QtGui.QBrush(self.borderColor))
            painter.drawRect(0, 0, self.width(), self.height())

    def closeEvent(self, event):
        if self.name:
            self.saveGeometry()
            self.hide()
            logger.info("Closed '" + self.name + "'")
            event.ignore()

            # Remove empty notes
            if not self.isImage:
                if self.preferences.query("general", "deleteEmptyNotes") and self.ui.textEdit.toPlainText() == "":
                    logger.warning("Removed '" + self.name + "' (empty)")
                    self.remove()

    def handleAsterisk(self):
        # Indicate unsaved changes with title*
        if self.ui.textEdit.isVisible():
            content = ""
            if os.path.isfile(self.path):
                with open(self.path) as f:
                    content = f.read()

            isSame = (content == self.ui.textEdit.toPlainText())
            asterisk = (self.windowTitle()[-1] == "*" or self.ui.titleLabel.text()[-1] == "*")
            if asterisk and isSame:
                self.setWindowTitle(self.windowTitle()[:-1])
                self.ui.titleLabel.setText(self.ui.titleLabel.text()[:-1])
            elif not asterisk and not isSame:
                self.setWindowTitle(self.windowTitle() + "*")
                self.ui.titleLabel.setText(self.ui.titleLabel.text() + "*")

    def saveTextToFile(self):
        saveWidget = QtWidgets.QFileDialog.getSaveFileName(self, "Save text as", self.name, ".txt")
        path = saveWidget[0]
        if path:
            path += ".txt"
            with open(path, 'w') as f:
                f.write(self.ui.textEdit.toPlainText())

    def saveImageToFile(self):
        saveWidget = QtWidgets.QFileDialog.getSaveFileName(self, "Save image as", self.name, ".png")
        path = saveWidget[0]
        if path:
            path += ".png"
            f = QtCore.QFile(path)
            f.open(QtCore.QIODevice.WriteOnly)
            self.ui.imageLabel.pixmap().save(f, "PNG")

    def saveImageToClipboard(self):
        self.parent.clipboard.setPixmap(self.ui.imageLabel.pixmap())

    def titleLabelMousePressEvent(self, event):
        # Mouse dragging for frameless windows
        if event.button() == QtCore.Qt.LeftButton:
            self.dragPosition = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def titleLabelMouseMoveEvent(self, event):
        # Mouse dragging for frameless windows
        if event.buttons() == QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.dragPosition)
            event.accept()

    def toggleWordWrap(self, state=None):
        if state is None:
            self.toggleWordWrap(not self.ui.textEdit.lineWrapMode())
        elif state is True:
            self.ui.textEdit.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
        elif state is False:
            self.ui.textEdit.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)

    def textAction(self, action):
        savedLineWrapMode = bool(self.ui.textEdit.lineWrapMode())
        self.toggleWordWrap(False)

        # Save initial selection
        cursor = self.ui.textEdit.textCursor()
        hasSelection = cursor.hasSelection()
        initialSelectedText = cursor.selectedText()
        initialSelectionStart = cursor.selectionStart()
        initialSelectionEnd = cursor.selectionEnd()

        # Extend selection, save content and selection borders
        linesCount = cursor.selectedText().count("\u2029") + 1  # \u2029 is unicode for \n
        if linesCount > 1:
            selectionEnd = cursor.selectionEnd()
            cursor.setPosition(cursor.selectionStart())
            cursor.movePosition(QtGui.QTextCursor.StartOfLine)
            selectionStart = cursor.position()
            cursor.setPosition(selectionEnd, QtGui.QTextCursor.KeepAnchor)
            cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
            selectionEnd = cursor.position()
            selectedText = cursor.selectedText()
        else:
            cursor.movePosition(QtGui.QTextCursor.StartOfLine)
            selectionStart = cursor.position()
            cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
            selectionEnd = cursor.position()
            selectedText = cursor.selectedText()

        if action == "delete":
            if cursor.atEnd():
                cursor.movePosition(QtGui.QTextCursor.EndOfLine)
                cursor.movePosition(QtGui.QTextCursor.StartOfLine, QtGui.QTextCursor.KeepAnchor)
                cursor.movePosition(QtGui.QTextCursor.Left, QtGui.QTextCursor.KeepAnchor)
            else:
                cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor)
            cursor.removeSelectedText()

        elif action == "duplicate":
            cursor.insertText(selectedText + "\n" + selectedText)
            cursor.setPosition(initialSelectionStart)

        elif action == "shift up":
            # Remove selected text
            cursor.removeSelectedText()
            cursor.movePosition(QtGui.QTextCursor.Left, QtGui.QTextCursor.KeepAnchor)

            # Save and remove newline character
            newline = cursor.selectedText()
            cursor.removeSelectedText()

            # Insert saved text
            cursor.movePosition(QtGui.QTextCursor.StartOfLine)
            cursor.insertText(selectedText + newline)

            # Select inserted text
            cursor.movePosition(QtGui.QTextCursor.Up, n=linesCount)
            cursor.movePosition(QtGui.QTextCursor.StartOfLine)
            cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor, n=len(selectedText))

        elif action == "shift down":
            # Remove selected text
            cursor.removeSelectedText()
            cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor)

            # Save and remove newline character
            newline = cursor.selectedText()
            cursor.removeSelectedText()

            # Insert saved text
            cursor.movePosition(QtGui.QTextCursor.EndOfLine)
            cursor.insertText(newline + selectedText)

            # Select inserted text
            cursor.movePosition(QtGui.QTextCursor.EndOfLine)
            cursor.movePosition(QtGui.QTextCursor.Left, QtGui.QTextCursor.KeepAnchor, n=len(selectedText))

        elif action == "increase indent":
            # Add one tab before every line
            newText = []
            for line in selectedText.splitlines(True):
                newText.append("\t" + line)
            newText = "".join(newText)
            cursor.insertText(newText)

            # Restore selection
            cursor.setPosition(selectionStart)
            cursor.setPosition(selectionEnd+linesCount, QtGui.QTextCursor.KeepAnchor)

        elif action == "decrease indent":
            # Remove one tab before every line (if any)
            newText = []
            tabsCount = 0
            for line in selectedText.splitlines(True):
                if line[:1] == "\t":
                    line = line[1:]
                    tabsCount += 1
                elif line[:4] == "    ":
                    line = line[4:]
                    tabsCount += 4
                newText.append(line)
            newText = "".join(newText)
            cursor.insertText(newText)

            # Restore selection
            cursor.setPosition(selectionStart)
            cursor.setPosition(selectionEnd-tabsCount, QtGui.QTextCursor.KeepAnchor)

        elif action == "sort selection":
            # Sort either the whole line or a partial selection
            if hasSelection:
                selectedText = initialSelectedText
                selectionStart = initialSelectionStart
                selectionEnd = initialSelectionEnd
                cursor.setPosition(selectionStart)
                cursor.setPosition(selectionEnd, QtGui.QTextCursor.KeepAnchor)

            # Determine how to split the text
            if linesCount > 1:
                separator = "\u2029"
            elif selectedText.count(" ") > 0:
                separator = " "
            else:
                separator = ""

            # Determine direction, split and sort
            newText = []
            if separator:
                sortedList = sorted(selectedText.split(separator))
                if sortedList == selectedText.split(separator):
                    sortedList = sorted(selectedText.split(separator), reverse=True)
                for item in sortedList:
                    newText.append(item + separator)
                newText = separator.join(sortedList)
            else:
                direction = (sorted(list(selectedText)) == list(selectedText))
                sortedList = sorted(list(selectedText), reverse=direction)
                newText = "".join(sortedList)

            # Insert the result and restore previous selection
            cursor.insertText(newText)
            cursor.setPosition(selectionStart)
            cursor.setPosition(selectionEnd, QtGui.QTextCursor.KeepAnchor)

        self.ui.textEdit.setTextCursor(cursor)
        self.toggleWordWrap(savedLineWrapMode)
        self.handleAsterisk()

    def resizeAction(self, sizeIncrement):
        if sizeIncrement > 0:
            fontIncrement = 1
        else:
            fontIncrement = -1

        if self.isImage:
            width, height = self.width() + sizeIncrement, self.height() + sizeIncrement
            if 'width' in locals() and width > 50:
                self.resize(width, self.height())
            if 'height' in locals() and height > 50:
                self.resize(self.width(), height)
        else:
            font = self.ui.textEdit.font()
            size = font.pointSize() + fontIncrement
            if size < 7:
                size = 7
            font.setPointSize(size)
            self.ui.textEdit.setFont(font)
            self.profile.save("fontSize", size)

    def hotkeyAction(self, action):
        action = action.lower()

        if action == "toggle sizegrip":
            if self.sizeGrip.isVisible():
                self.sizeGrip.hide()
                self.profile.save("sizeGrip", False)
            else:
                self.sizeGrip.show()
                self.profile.save("sizeGrip", True)

        elif action == "special paste":
            txt = self.parent.clipboard.text()
            txt = txt.replace("\n", " ")
            txt = txt.replace("\t", " ")
            self.ui.textEdit.insertPlainText(txt)

        elif action == "selection to uppercase":
            cursor = self.ui.textEdit.textCursor()
            cursor.insertText(cursor.selectedText().upper())

        elif action == "selection to lowercase":
            cursor = self.ui.textEdit.textCursor()
            cursor.insertText(cursor.selectedText().lower())

        elif action == "delete line":
            self.textAction("delete")

        elif action == "duplicate line":
            self.textAction("duplicate")

        elif action == "shift line up":
            self.textAction("shift up")

        elif action == "shift line down":
            self.textAction("shift down")

        elif action == "increase indent":
            self.textAction("increase indent")

        elif action == "decrease indent":
            self.textAction("decrease indent")

        elif action == "sort selection":
            self.textAction("sort selection")

        elif action == "toggle wordwrap":
            self.toggleWordWrap()

        elif action == "zoom in":
            self.resizeAction(20)

        elif action == "zoom out":
            self.resizeAction(-20)

        elif action == "rename":
            self.renamePrompt()

        elif action == "save":
            self.saveContent()

        elif action == "pin":
            self.pin()

        elif action == "hide":
            self.hide()

        elif action == "new note":
            self.parent.action("New note")

        elif action == "delete":
            self.delete()

        elif action == "undo":
            self.ui.textEdit.undo()

        elif action == "redo":
            self.ui.textEdit.redo()

        elif action == "save as":
            if self.isImage:
                self.saveImageToFile()
            else:
                self.saveTextToFile()

        elif action == "search":
            selection = self.ui.textEdit.textCursor().selectedText()
            self.parent.searchForm.ui.searchFindLine.setText(selection)
            self.parent.searchForm.show()
            self.parent.searchForm.activateWindow()
            self.parent.searchForm.ui.searchFindLine.setFocus()
            self.parent.searchForm.ui.searchFindLine.selectAll()

        else:
            logger.error("Invalid hotkey action '%s'" % action)
        return None
