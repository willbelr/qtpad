#!/usr/bin/python3
import os
import sys
import time
import json
from PyQt5 import QtGui, QtWidgets, QtCore, uic
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal, pyqtSlot
LOCAL = os.path.dirname(os.path.realpath(__file__)) + '/'
ICONS = LOCAL + 'icons/'
DB = LOCAL + "db/"
PREFERENCES = DB + "preferences.json"
PROFILES = DB + "profiles.json"
if not os.path.exists(DB):
    os.makedirs(DB)

class preferences(object):
    def __init__(self):
        if os.path.isfile(PREFERENCES) and os.stat(PREFERENCES).st_size > 0:
            with open(PREFERENCES) as f:
                self.db = json.load(f)
        else:
            self.db = \
            {
                'general':
                {
                    'left_click_action': 'toggle',
                    'middle_click_action': 'image-new',
                    'startup_action': '',
                    'minimize': True,
                    'top_level': True,
                    'save_position': True,
                    'safe_delete': True,
                    'hotkeys': True,
                },
                'style':
                {
                    'width': 300,
                    'height': 220,
                    'background': '#ffff7f',
                    'font_color': '#000000',
                    'font_size': 9,
                    'font_family': 'Sans Serif',
                },
                'actives': '',
            }
            with open(PREFERENCES, "w+") as f:
                f.write(json.dumps(self.db, indent=2, sort_keys=False))
        self.load()

    def load(self):
        self.q = {}
        for entry in self.db["general"]:
            self.q[entry] = self.db["general"][entry]
        for entry in self.db["style"]:
            self.q[entry] = self.db["style"][entry]
        self.q["actives"] = self.db["actives"]

    def save(self, name, entry, value=None):
        with open(PREFERENCES, "r+") as f:
            self.db = json.load(f)
            if value is None:
                self.db[name] = entry
            else:
                self.db[name][entry] = value
            f.seek(0)
            f.truncate()
            f.write(json.dumps(self.db, indent=2, sort_keys=False))
        self.load()

    def toggle(self, name, entry):
        with open(PREFERENCES, "r+") as f:
            self.db = json.load(f)
            self.db[name][entry] = not self.db[name][entry]
            f.seek(0)
            f.truncate()
            f.write(json.dumps(self.db, indent=2, sort_keys=False))
        self.load()

class profile(object):
    def __init__(self, entry):
        self.path = entry
        self.name = entry.rsplit('/', 1)[-1].rsplit('.', 1)[0]

        if os.path.isfile(PROFILES) and os.stat(PROFILES).st_size > 0:
            with open(PROFILES) as f:
                self.db = json.load(f)
        else:
            self.db = {}

        if not self.name in self.db:
            self.db[self.name] = \
            {
                'pin': False,
                'x': 0, 'y': 0,
                'width': preferences.q["width"],
                'height': preferences.q["height"],
                'background': preferences.q["background"],
                'font_color': preferences.q["font_color"],
                'font_size': preferences.q["font_size"],
                'font_family': preferences.q["font_family"],
            }

            with open(PROFILES, 'w') as f:
                f.write(json.dumps(self.db, indent=2, sort_keys=False))
        self.load()

    def load(self):
        with open(PROFILES) as f:
            self.db = json.load(f)
        if self.name in self.db:
            self.q = {}
            for entry in self.db[self.name]:
                self.q[entry] = self.db[self.name][entry]

    def save(self, entry, value):
        with open(PROFILES, "r+") as f:
            profiles = json.load(f)
            if self.name in profiles:
                profiles[self.name][entry] = value
                f.seek(0)
                f.truncate()
                f.write(json.dumps(profiles, indent=2, sort_keys=False))
        self.load()

class styleDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__()
        self.ui = uic.loadUi(LOCAL + 'gui_style.ui', self)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.type = type(parent)
        self.parent = parent

        if self.type is child:
            self.setWindowTitle("Style for '" + self.parent.name + "'")
            fetch = parent.profile.q
        else:
            self.setWindowTitle("Default style")
            fetch = preferences.q
            self.ui.defaultOpt.hide()

        self.width = fetch["width"]
        self.height = fetch["height"]
        self.background = fetch["background"]
        self.fontcolor = fetch["font_color"]
        self.fontsize = fetch["font_size"]
        self.fontfamily = fetch["font_family"]

        font = QtGui.QFont()
        font.setFamily(self.fontfamily)
        self.ui.fontfamilyOpt.setCurrentFont(font)

        self.ui.backgroundLabel.setText(self.background.upper())
        self.ui.fontcolorLabel.setText(self.fontcolor.upper())
        self.ui.widthOpt.setValue(self.width)
        self.ui.heightOpt.setValue(self.height)
        self.ui.fontsizeOpt.setValue(self.fontsize)

        self.ui.fontfamilyOpt.currentFontChanged.connect(self.updateFontfamily)
        self.ui.backgroundOpt.clicked.connect(self.pickBackgroundColor)
        self.ui.fontcolorOpt.clicked.connect(self.pickFontColor)
        self.ui.widthOpt.valueChanged.connect(self.updateWidth)
        self.ui.heightOpt.valueChanged.connect(self.updateHeight)
        self.ui.fontsizeOpt.valueChanged.connect(self.updateFontsize)

        self.style = self.exec_()
        self.close()

    def save(self, profile):
        profile("width", self.width)
        profile("height", self.height)
        profile("background", self.background)
        profile("font_color", self.fontcolor)
        profile("font_size", self.fontsize)
        profile("font_family", self.fontfamily)

    def closeEvent(self, event):
        if self.style:
            if self.type is mother or self.ui.defaultOpt.isChecked():
                self.save(preferences.save)
                preferences.save("style", "width", self.width)
                preferences.save("style", "height", self.height)
                preferences.save("style", "background", self.background)
                preferences.save("style", "font_color", self.fontcolor)
                preferences.save("style", "font_size", self.fontsize)
                preferences.save("style", "font_family", self.fontfamily)

            if self.type is child:
                self.save(self.parent.profile.save)

        elif self.type is child:
            self.parent.ui.textEdit.viewport().update()
            self.parent.resize(self.parent.profile.q["width"], self.parent.profile.q["height"])

        if self.ui.allOpt.isChecked():
            if self.type is mother:
                children = self.parent.children
            elif self.type is child:
                children = self.parent.parent.children

            for f in list(children):
                self.save(children[f].profile.save)
                children[f].loadStyle()
        event.accept()

    def pickColor(self, target):
        self.target = target
        self.colorWidget = QtWidgets.QColorDialog(QtGui.QColor(self.background))
        self.colorWidget.setWindowFlags(self.colorWidget.windowFlags() | Qt.WindowStaysOnTopHint)
        self.colorWidget.currentColorChanged.connect(self.colorChanged)
        self.colorWidget.exec_()
        return self.colorWidget.selectedColor()

    def colorChanged(self):
        color = self.colorWidget.currentColor()
        if self.target == "background":
            self.setBackgroundColor(color)
        elif self.target == "font":
            self.setFontColor(color)

    def setBackgroundColor(self, color):
        if self.type is child:
            palette = self.parent.ui.textEdit.viewport().palette()
            palette.setColor(QtGui.QPalette.Base, color)
            self.parent.ui.textEdit.viewport().setPalette(palette)

    def pickBackgroundColor(self):
        color = self.pickColor("background")
        if color.isValid():
            self.background = color.name()
            self.ui.backgroundLabel.setText(color.name().upper())
            self.setBackgroundColor(color)
        else:
            color = QtGui.QColor(self.ui.backgroundLabel.text())
            self.setBackgroundColor(color)

    def setFontColor(self, color):
        if self.type is child:
            palette = self.parent.ui.textEdit.viewport().palette()
            palette.setColor(QtGui.QPalette.Text, color)
            self.parent.ui.textEdit.viewport().setPalette(palette)

    def pickFontColor(self):
        color = self.pickColor("font")
        if color.isValid():
            self.fontcolor = color.name()
            self.ui.fontcolorLabel.setText(color.name().upper())
            self.setFontColor(color)
        else:
            color = QtGui.QColor(self.ui.fontcolorLabel.text())
            self.setFontColor(color)

    def updateWidth(self):
        self.width = self.ui.widthOpt.value()
        if self.type is child:
            self.parent.resize(self.width, self.parent.height())

    def updateHeight(self):
        self.height = self.ui.heightOpt.value()
        if self.type is child:
            self.parent.resize(self.parent.width(), self.height)

    def updateFontsize(self):
        self.fontsize = self.ui.fontsizeOpt.value()
        if self.type is child:
            font = self.parent.ui.textEdit.font()
            font.setPointSize(self.fontsize)
            self.parent.ui.textEdit.setFont(font)

    def updateFontfamily(self):
        self.fontfamily = self.ui.fontfamilyOpt.currentText()
        if self.type is child:
            font = self.parent.ui.textEdit.font()
            font.setFamily(self.fontfamily)
            self.parent.ui.textEdit.setFont(font)

class mother(object):
    def __init__(self, parent=None):
        icons = ["tray", "quit", "file_active", "file_inactive", "enabled", "new", "hide", "show", "none",
                    "reverse" ,"preferences", "image", "toggle", "reset", "file_pinned", "style", "file_image"]
        self.icon = {}
        for icon in icons:
            self.icon[icon] = QtGui.QIcon(ICONS + icon + ".svg")

        self.menu = QtWidgets.QMenu()
        self.menu.aboutToShow.connect(self.refreshMenu)
        self.submenu = {}
        self.submenu["preferences"] = QtWidgets.QMenu("Preferences")
        self.submenu["preferences"].setIcon(self.icon["preferences"])
        self.submenu["left_click_action"] = QtWidgets.QMenu("Left click action")
        self.submenu["left_click_action"].setIcon(self.icon["preferences"])
        self.submenu["middle_click_action"] = QtWidgets.QMenu("Middle click action")
        self.submenu["middle_click_action"].setIcon(self.icon["preferences"])
        self.submenu["startup_action"] = QtWidgets.QMenu("Startup action")
        self.submenu["startup_action"].setIcon(self.icon["preferences"])
        self.submenu["style"] = QtWidgets.QMenu("Default style")
        self.trayIcon = QtWidgets.QSystemTrayIcon()
        self.trayIcon.activated.connect(self.clickEvent)
        self.trayIcon.setIcon(self.icon["tray"])
        self.trayIcon.setContextMenu(self.menu)
        self.trayIcon.show()

        self.children = {}
        self.load()
        if preferences.q["startup_action"]:
            self.action(preferences.q["startup_action"])

    def load(self):
        for f in os.listdir(DB):
            name = f.rsplit('.', 1)[0]
            if not name in self.children:
                if f.endswith(".txt"):
                    if os.stat(DB + f).st_size > 0:
                        self.children[name] = child(self, DB + f)
                    else:
                        os.remove(DB + f)
                elif f.endswith(".png"):
                    self.children[name] = child(self, DB + f, True)
        self.cleanProfiles()

    #Actions
    def cleanOrphans(self):
        for f in list(self.children):
            if not os.path.isfile(self.children[f].path):
                self.children[f].delete()

    def cleanProfiles(self):
        if os.path.isfile(PROFILES):
            with open(PROFILES, "r+") as db:
                profiles = json.load(db)
                for entry in list(profiles):
                    txtPath = DB + entry + ".txt"
                    pngPath = DB + entry + ".png"
                    if not os.path.isfile(pngPath) and (not os.path.isfile(txtPath) or os.stat(txtPath).st_size < 0):
                        del profiles[entry]
                db.seek(0)
                db.truncate()
                db.write(json.dumps(profiles, indent=2, sort_keys=False))

    def clipboardImg(self):
        pixmap = clipboard.pixmap()
        if pixmap.isNull() and clipboard.text():
            path = clipboard.text().rstrip()
            if os.path.isfile(path) and os.stat(path).st_size > 0:
                ext = path.lower().rsplit('.', 1)[-1]
                allowed = ["gif", "png", "bmp", "jpg", "jpeg"]
                if ext in allowed:
                    pixmap = QtGui.QPixmap(path)
        return pixmap

    def pollIcon(self, entry, action = None):
        if action == preferences.q[entry] or (action is None and preferences.q[entry]):
            icon = "enabled"
        else:
            icon = "none"
        return self.icon[icon]

    def refreshMenu(self):
        #Monitor changes in the database directory, clear old menu
        self.load()
        self.cleanOrphans()
        self.menu.clear()

        #Actions menu
        self.menu.addAction(self.icon["new"], 'New note', lambda: self.action("new"))
        self.menu.addAction(self.icon["toggle"], 'Toggle actives', lambda: self.action("toggle"))
        if not self.clipboardImg().isNull():
            self.menu.addAction(self.icon["image"], 'Paste image', lambda: self.action("image"))
        self.menu.addSeparator()
        self.menu.addAction(self.icon["hide"], 'Hide all', lambda: self.action("hide"))
        self.menu.addAction(self.icon["show"], 'Show all', lambda: self.action("show"))
        self.menu.addAction(self.icon["reverse"], 'Reverse all', lambda: self.action("reverse"))
        self.menu.addAction(self.icon["reset"], 'Reset positions', lambda: self.action("reset"))
        self.menu.addSeparator()

        #List of children windows
        for name in self.children:
            if self.children[name].profile.q["pin"]:
                icon = self.icon["file_pinned"]
            elif name in preferences.q["actives"]:
                icon = self.icon["file_active"]
            elif self.children[name].isImage:
                icon = self.icon["file_image"]
            else:
                icon = self.icon["file_inactive"]
            self.menu.addAction(icon, self.children[name].name, self.children[name].focus)
        self.menu.addSeparator()

        #Preferences menus
        self.menu.addMenu(self.submenu["preferences"])
        self.submenu["preferences"].clear()
        self.submenu["preferences"].addAction(self.icon["style"], "Default style", lambda: styleDialog(self))
        self.submenu["preferences"].addAction(self.pollIcon("top_level"), "Always on top", lambda: self.action("top"))
        self.submenu["preferences"].addAction(self.pollIcon("minimize"), "Minimize on startup", lambda: preferences.toggle("general", "minimize"))
        self.submenu["preferences"].addAction(self.pollIcon("save_position"), "Save notes position", lambda: preferences.toggle("general", "save_position"))
        self.submenu["preferences"].addAction(self.pollIcon("hotkeys"), "Hotkeys", lambda: preferences.toggle("general", "hotkeys"))
        self.submenu["preferences"].addAction(self.pollIcon("safe_delete"), "Safe delete", lambda: preferences.toggle("general", "safe_delete"))

        menus = ["left_click_action", "middle_click_action", "startup_action"]
        for sm in menus:
            self.submenu["preferences"].addMenu(self.submenu[sm])
            self.submenu[sm].clear()
            self.submenu[sm].addAction(self.pollIcon(sm, "toggle"), "Toggle actives", lambda sm=sm: preferences.save("general", sm, "toggle"))
            self.submenu[sm].addAction(self.pollIcon(sm, "new"), "Create new note", lambda sm=sm: preferences.save("general", sm, "new"))
            self.submenu[sm].addAction(self.pollIcon(sm, "show"), "Show all", lambda sm=sm: preferences.save("general", sm, "show"))
            self.submenu[sm].addAction(self.pollIcon(sm, "hide"), "Hide all", lambda sm=sm: preferences.save("general", sm, "hide"))
            self.submenu[sm].addAction(self.pollIcon(sm, "reverse"), "Reverse all", lambda sm=sm: preferences.save("general", sm, "reverse"))
            self.submenu[sm].addAction(self.pollIcon(sm, "reset"), "Reset notes", lambda sm=sm: preferences.save("general", sm, "reset"))
            self.submenu[sm].addAction(self.pollIcon(sm, "image"), "Paste image", lambda sm=sm: preferences.save("general", sm, "image"))
            self.submenu[sm].addAction(self.pollIcon(sm, "image-new"), "Paste image / Create new", lambda sm=sm: preferences.save("general", sm, "image-new"))
            self.submenu[sm].addAction(self.pollIcon(sm, ""), "None", lambda sm=sm: preferences.save("general", sm, ""))
        self.menu.addAction(self.icon["quit"], 'Quit', app.exit)

    def new(self, prefix, isImage = False):
        name = prefix + " 1"
        n = 1
        while name in self.children:
            n += 1
            name = prefix + " " + str(n)
        if isImage:
            self.children[name] = child(self, DB + name + ".png", isImage)
        else:
            self.children[name] = child(self, DB + name + ".txt", isImage)
        self.children[name].show()
        return name

    def action(self, action):
        if action == "new":
            self.new("Untitled")

        elif action == "image" or action == "image-new":
            pixmap = self.clipboardImg()
            if not pixmap.isNull():
                child = self.children[self.new("Image", isImage = True)]
                child.setupPixmap(pixmap)
                f = QtCore.QFile(DB + child.name + ".png")
                f.open(QtCore.QIODevice.WriteOnly)
                pixmap.save(f, "PNG")
                if action == "image-new":
                    clipboard.setText("")
            elif pixmap.isNull() and action == "image-new":
                self.new("Untitled")

        elif action == "toggle":
            actives = []
            for name in self.children:
                children = self.children[name]
                if children.profile.q["pin"]:
                    children.activateWindow()
                elif children.isVisible():
                    actives.append(children.name)
            if actives:
                preferences.save("actives", actives)
                self.action("hide")
            elif preferences.q["actives"]:
                for note in preferences.q["actives"]:
                    if note in self.children:
                        self.children[note].show()
                        self.children[note].activateWindow()

        elif action == "hide":
            for name in self.children:
                children = self.children[name]
                if not children.profile.q["pin"]:
                    children.hide()

        elif action == "show":
            for name in self.children:
                children = self.children[name]
                children.show()
                children.activateWindow()

        elif action == "reverse":
            for name in self.children:
                children = self.children[name]
                if children.isVisible():
                    if not children.profile.q["pin"]:
                        children.hide()
                else:
                    children.show()

        elif action == "reset":
            #Remove empty notes
            for f in os.listdir(DB):
                if f.endswith(".txt") and os.stat(DB + f).st_size == 0:
                    name = f.rsplit('.', 1)[0]
                    if name in self.children:
                        self.children[name].delete()

            #Remove orhans and unassigned profiles
            self.cleanOrphans()
            self.cleanProfiles()

            #Reset position
            n, _x = 0, QtWidgets.QDesktopWidget().screenGeometry().width() - 350
            for name in self.children:
                children = self.children[name]
                n += 30
                x = _x - n
                y = 80 + n
                children.show()
                children.move(x, y)
                children.activateWindow()
                children.profile.save("x", x)
                children.profile.save("y", y)

        elif action == "top":
            preferences.save("general", "top_level", not preferences.q["top_level"])
            for name in self.children:
                children = self.children[name]
                visible = children.isVisible()
                if preferences.q["top_level"]:
                    children.setWindowFlags(children.windowFlags() | Qt.WindowStaysOnTopHint)
                elif not children.profile.q["pin"]:
                    children.setWindowFlags(children.windowFlags() &~ Qt.WindowStaysOnTopHint)
                time.sleep(0.1)
                if visible:
                    children.show()

    #Events
    def clickEvent(self, event):
        if event == 3:
            self.action(preferences.q["left_click_action"])
        elif event == 4:
            self.action(preferences.q["middle_click_action"])

class child(QtWidgets.QWidget):
    def __init__(self, parent, path, isImage = False):
        super().__init__()
        self.ui = uic.loadUi(LOCAL + 'gui_child.ui', self)
        self.profile = profile(path)
        self.parent = parent
        self.path = path
        self.name = path.rsplit('/', 1)[-1].rsplit('.', 1)[0]

        self.sizeGrip = QtWidgets.QSizeGrip(self.ui.textEdit)
        self.gridLayout.addWidget(self.sizeGrip)
        self.gridLayout.setAlignment(self.sizeGrip, Qt.AlignRight)
        self.sizeGrip.hide()

        self.menu = QtWidgets.QMenu()
        icons = ["hide", "delete", "rename", "tray", "pin_menu", "pin_title", "toggle", "style", "image", "file_inactive"]
        self.icon = {}
        for icon in icons:
            self.icon[icon] = QtGui.QIcon(ICONS + icon + ".svg")
        self.menu.addAction(self.icon["hide"], '&Hide', self.hide)
        self.menu.addAction(self.icon["pin_menu"], '&Pin', self.pin)
        self.menu.addAction(self.icon["rename"], '&Rename', self.rename)

        if isImage:
            self.isImage = True
            self.menu.addAction(self.icon["image"], 'Save image as', self.imageToFile)
            self.menu.addAction(self.icon["image"], 'Copy to clipboard', self.imageToClipboard)
            self.ui.imageLabel.setScaledContents(True)
            self.ui.imageLabel.setContextMenuPolicy(Qt.CustomContextMenu)
            self.ui.imageLabel.customContextMenuRequested.connect(lambda: self.menu.popup(QtGui.QCursor.pos()))
            self.ui.imageLabel.setFocusPolicy(Qt.StrongFocus)
            self.ui.imageLabel.focusOutEvent = self.focusOutEvent
        else:
            self.isImage = False
            self.ui.imageLabel.hide()
            self.menu.addAction(self.icon["style"], "Style", lambda: styleDialog(self))
            self.menu.addAction(self.icon["file_inactive"], 'Save text as', self.textToFile)
            self.ui.textEdit.focusOutEvent = self.focusOutEvent
            self.ui.textEdit.focusInEvent = self.focusInEvent
            self.ui.textEdit.dropEvent = self.dropEvent
            self.ui.textEdit.keyPressEvent = self.keyPressEvent
            self.ui.textEdit.setContextMenuPolicy(Qt.CustomContextMenu)
            self.ui.textEdit.customContextMenuRequested.connect(lambda: self.menu.popup(QtGui.QCursor.pos()))
            self.ui.textEdit.setAttribute(Qt.WA_TranslucentBackground)

        self.menu.addSeparator()
        self.menu.addAction(self.icon["delete"], '&Delete', self.delete)

        self.loadStyle()
        self.setWindowTitle(self.name)
        self.setAttribute(Qt.WA_X11NetWmWindowTypeToolBar)
        self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        self.ui.renameText.hide()
        self.ui.renameLabel.hide()
        self.ui.renameText.keyPressEvent = self.renameAccept
        self.ui.renameText.focusOutEvent = self.renameReject

        if self.profile.q["pin"]:
            self.setWindowIcon(self.icon["pin_title"])
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.show()
        elif preferences.q["top_level"]:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        elif not preferences.q["top_level"]:
            self.setWindowFlags(self.windowFlags() &~ Qt.WindowStaysOnTopHint)
            self.show()

        if not preferences.q["save_position"] or not self.profile.q["x"] or not self.profile.q["width"]:
            x = QtWidgets.QDesktopWidget().screenGeometry().width() - 350
            x = x - (len(self.parent.children) * 30)
            y = 80 + (len(self.parent.children) * 30)
            self.setGeometry(x, y, preferences.q["width"], preferences.q["height"])
        elif preferences.q["save_position"]:
            self.resize(self.profile.q["width"], self.profile.q["height"])
            self.move(self.profile.q["x"], self.profile.q["y"])

        if os.path.isfile(path):
            with open(path) as f:
                if path.endswith(".txt"):
                    self.ui.textEdit.setPlainText(f.read())
                elif path.endswith(".png"):
                    pixmap = QtGui.QPixmap(path)
                    self.setupPixmap(pixmap)

        if not preferences.q["minimize"]:
            self.show()

    def setupPixmap(self, pixmap):
        self.ui.textEdit.hide()
        if not self.profile.q["width"] == preferences.q["width"]:
            width, height = self.profile.q["width"], self.profile.q["height"]
        else:
            width, height = pixmap.width(), pixmap.height()
        widthMax = QtWidgets.QDesktopWidget().screenGeometry().width() * 0.8
        heightMax = QtWidgets.QDesktopWidget().screenGeometry().height() * 0.8
        if width > widthMax:
            width = widthMax
        if height > heightMax:
            height = heightMax
        self.resize(width, height)
        self.ui.imageLabel.setPixmap(pixmap)

    #Action
    def focus(self):
        self.show()
        self.activateWindow()

    def delete(self):
        if os.path.isfile(self.path):
            if preferences.q["safe_delete"] and os.stat(self.path).st_size > 0:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Warning)
                msg.setWindowTitle("Delete confirmation")
                msg.setText("Please confirm deletion of '" + self.name + "'")
                msg.setStandardButtons(QtWidgets.QMessageBox.Apply | QtWidgets.QMessageBox.Cancel)
                if msg.exec_() == QtWidgets.QMessageBox.Apply:
                    self.remove()
            else:
                self.remove()

    def remove(self):
        self.profile.load()
        if self.name in self.profile.db:
            del self.profile.db[self.name]
            with open(PROFILES, "w+") as f:
                f.write(json.dumps(self.profile.db, indent=2, sort_keys=False))

        #if self.name in self.parent.children:
        del self.parent.children[self.name]
        os.remove(self.path)
        self.name = ""
        self.close()

    def loadStyle(self):
        self.profile.load()
        palette = self.ui.textEdit.viewport().palette()
        palette.setColor(QtGui.QPalette.Background, QtGui.QColor(self.profile.q["background"]))
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(self.profile.q["background"]))
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor(self.profile.q["font_color"]))
        self.ui.textEdit.viewport().setPalette(palette)

        font = self.ui.textEdit.font()
        font.setFamily(self.profile.q["font_family"])
        font.setPointSize(self.profile.q["font_size"])
        self.ui.textEdit.setFont(font)

        self.ui.textEdit.viewport().update()
        if not self.isImage:
            self.ui.setPalette(palette)
            self.ui.update()

    def pin(self):
        if self.profile.q["pin"]:
            self.setWindowIcon(self.icon["tray"])
            if not preferences.q["top_level"]:
                self.setWindowFlags(self.windowFlags() &~ Qt.WindowStaysOnTopHint)
                self.show()
        else:
            self.setWindowIcon(self.icon["pin_title"])
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.show()
        self.profile.save("pin", not self.profile.q["pin"])

    def promptAccept(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.prompt.accept()
            self.prompt.confirm = True

    def rename(self):
        self.ui.renameLabel.show()
        self.ui.renameText.setText(self.name)
        self.ui.renameText.show()
        self.ui.renameText.setFocus()
        self.ui.renameText.selectAll()

    def renameAccept(self, event):
        if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            name = self.ui.renameText.text()
            if name and not name == self.name and not name in self.parent.children:
                #Remove illegal characters
                entry = self.ui.renameText.text()
                entry = "".join(x for x in entry if x.isalnum() or x is " ")

                with open(PROFILES, "r+") as db:
                    profiles = json.load(db)
                    profiles[entry] = {}
                    profiles[entry] = profiles[self.name]
                    del profiles[self.name]
                    db.seek(0)
                    db.truncate()
                    db.write(json.dumps(profiles, indent=2, sort_keys=False))

                self.parent.children[entry] = {}
                self.parent.children[entry] = self.parent.children[self.name]
                del self.parent.children[self.name]

                if os.path.isfile(self.path):
                    if self.isImage:
                        os.rename(self.path, DB + entry + ".png")
                        self.path = DB + entry + ".png"
                    else:
                        os.rename(self.path, DB + entry + ".txt")
                        self.path = DB + entry + ".txt"
                self.name = self.path.rsplit('/', 1)[-1].rsplit('.', 1)[0]
                self.profile.path = self.path
                self.profile.name = self.name
                self.profile.load()
                self.setWindowTitle(entry)
                self.ui.renameText.hide()
                self.ui.renameLabel.hide()
            else:
                self.renameReject()
        else:
            QtWidgets.QLineEdit.keyPressEvent(self.ui.renameText, event)

    def renameReject(self, event=None):
        self.ui.renameText.hide()
        self.ui.renameLabel.hide()

    def textToFile(self):
        saveWidget = QtWidgets.QFileDialog.getSaveFileName(self, "Save text as", self.name, ".txt")
        path = saveWidget[0]
        if path:
            path += ".txt"
            with open(path, 'w') as f:
                f.write(self.ui.textEdit.toPlainText())

    def imageToFile(self):
        saveWidget = QtWidgets.QFileDialog.getSaveFileName(self, "Save image as", self.name, ".png")
        path = saveWidget[0]
        if path:
            path += ".png"
            f = QtCore.QFile(path)
            f.open(QtCore.QIODevice.WriteOnly)
            self.ui.imageLabel.pixmap().save(f, "PNG")

    def imageToClipboard(self):
        clipboard.setPixmap(self.ui.imageLabel.pixmap())

    def load(self, name):
        self.loadStyle()
        if os.path.isfile(self.path):
            with open(self.path) as f:
                content = f.read()
                if not content == self.ui.textEdit.toPlainText():
                    self.ui.textEdit.setPlainText(content)

    def save(self):
        if self.windowTitle()[-1] == "*":
            self.setWindowTitle(self.windowTitle()[:-1])
        if not self.isImage:
            with open(self.path, 'w') as f:
                f.write(self.ui.textEdit.toPlainText())
        if preferences.q["save_position"]:
            self.profile.save("x", self.pos().x())
            self.profile.save("y", self.pos().y())
            self.profile.save("width", self.width())
            self.profile.save("height", self.height())

    #Events
    def showEvent(self, event):
        if preferences.q["save_position"] and self.profile.q["x"] and self.profile.q["width"]:
            self.resize(self.profile.q["width"], self.profile.q["height"])
            self.move(self.profile.q["x"], self.profile.q["y"])

        if self.profile.q["pin"]:
            self.setWindowIcon(self.icon["pin_title"])
        elif self.name in preferences.q["actives"]:
            self.setWindowIcon(self.icon["toggle"])
        else:
            self.setWindowIcon(self.icon["tray"])

    def closeEvent(self, event):
        if self.name:
            self.save()
            self.hide()
            event.ignore()

    def dropEvent(self, event):
        QtWidgets.QPlainTextEdit.dropEvent(self.ui.textEdit, event)
        self.save()

    def focusInEvent(self, event):
        QtWidgets.QPlainTextEdit.focusInEvent(self.ui.textEdit, event)
        self.load(self.name)

    def focusOutEvent(self, event):
        if self.name:
            if not self.isImage:
                QtWidgets.QPlainTextEdit.focusOutEvent(self.ui.textEdit, event)
            self.save()

    def handleAsterisk(self):
        if self.ui.textEdit.isVisible():
            content = ""
            if os.path.isfile(self.path):
                with open(self.path) as f:
                    content = f.read()

            isSame = (content == self.ui.textEdit.toPlainText())
            if self.windowTitle()[-1] == "*" and isSame:
                self.setWindowTitle(self.windowTitle()[:-1])
            elif not self.windowTitle()[-1] == "*" and not isSame:
                self.setWindowTitle(self.windowTitle() + "*")

    def keyPressEvent(self, event):
        if preferences.q["hotkeys"]:
            isCtrlShift = int(event.modifiers()) == (Qt.ControlModifier + Qt.ShiftModifier)
            isCtrl = (event.modifiers() == Qt.ControlModifier)
            key = event.key()

            #Actions hotkeys
            if key == Qt.Key_H and isCtrl:
                self.hide()
            elif key == Qt.Key_P and isCtrl:
                self.pin()
            elif key == Qt.Key_R and isCtrl:
                self.rename()
            elif key == Qt.Key_S and isCtrl:
                self.save()
            elif key == Qt.Key_Delete and isCtrl:
                self.delete()

            #Special actions hotkeys
            elif key == Qt.Key_R and isCtrlShift:
                if self.sizeGrip.isVisible():
                    self.sizeGrip.hide()
                else:
                    self.sizeGrip.show()

            elif key == Qt.Key_V and isCtrlShift:
                txt = clipboard.text()
                txt = txt.replace("\n", " ").replace("\t", " ")
                self.ui.textEdit.insertPlainText(txt)

            elif key == Qt.Key_U and isCtrlShift:
                cursor = self.ui.textEdit.textCursor()
                cursor.insertText(cursor.selectedText().upper())

            elif key == Qt.Key_L and isCtrlShift:
                cursor = self.ui.textEdit.textCursor()
                cursor.insertText(cursor.selectedText().lower())

            elif (key == Qt.Key_Up or key == Qt.Key_Down or key == Qt.Key_D) and isCtrlShift:
                self.ui.textEdit.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
                cursor = self.ui.textEdit.textCursor()
                cursor.movePosition(QtGui.QTextCursor.StartOfLine);
                cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor);
                line = cursor.selectedText()

                #Duplicate line
                if key == Qt.Key_D:
                    cursor.insertText(line + "\n" + line)

                #Shift line up
                elif key == Qt.Key_Up:
                    cursor.removeSelectedText()
                    cursor.movePosition(QtGui.QTextCursor.Left, QtGui.QTextCursor.KeepAnchor);
                    newline = cursor.selectedText()
                    cursor.removeSelectedText()
                    cursor.movePosition(QtGui.QTextCursor.StartOfLine);
                    cursor.insertText(line + newline)
                    cursor.movePosition(QtGui.QTextCursor.Up);
                    cursor.movePosition(QtGui.QTextCursor.StartOfLine);

                #Shift line down
                elif key == Qt.Key_Down:
                    cursor.removeSelectedText()
                    cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor);
                    newline = cursor.selectedText()
                    cursor.removeSelectedText()
                    cursor.movePosition(QtGui.QTextCursor.EndOfLine);
                    cursor.insertText(newline + line)

                self.ui.textEdit.setTextCursor(cursor)
                self.ui.textEdit.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
                self.handleAsterisk()

            #Resize hotkeys
            elif key == Qt.Key_Plus and isCtrlShift:
                if self.isImage:
                    width, height = self.width() + 20, self.height() + 20
                else:
                    font = self.ui.textEdit.font()
                    size = font.pointSize() + 1
            elif key == Qt.Key_Underscore and isCtrlShift:
                if self.isImage:
                    width, height = self.width() - 20, self.height() - 20
                else:
                    font = self.ui.textEdit.font()
                    size = font.pointSize() - 1

            #No valid hotkeys
            else:
                QtWidgets.QPlainTextEdit.keyPressEvent(self.ui.textEdit, event)
                self.handleAsterisk()

            #Apply settings, if any
            if 'size' in locals() and size > 0:
                font.setPointSize(size)
                self.ui.textEdit.setFont(font)
                self.profile.save("font_size", size)
            if 'width' in locals() and width > 50:
                self.resize(width, self.height())
            if 'height' in locals() and height > 50:
                self.resize(self.width(), height)

        #No hotkeys
        else:
            QtWidgets.QPlainTextEdit.keyPressEvent(self.ui.textEdit, event)
            self.handleAsterisk()

if __name__== '__main__':
    preferences = preferences()
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    clipboard = app.clipboard()
    daemon = mother()
    sys.exit(app.exec_())
