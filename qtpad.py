#!/usr/bin/python3
import os
import sys
import time
import json
from PyQt5 import QtGui, QtWidgets, QtCore, uic
from PyQt5.QtCore import Qt, QThread, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QSystemTrayIcon

LOCAL = os.path.dirname(os.path.realpath(__file__)) + '/'
ICONS = LOCAL + '/icons/'
DB = LOCAL + "/db/"
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
                    'middle_click_action': 'new',
                    'startup_action': '',
                    'minimize': True,
                    'top_level': True,
                    'save_position': True,
                    'safe_delete': False,
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
        with open(PREFERENCES) as f:
            self.db = json.load(f)

        if value is None:
            self.db[name] = entry
        else:
            self.db[name][entry] = value

        with open(PREFERENCES, "w+") as f:
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
                'x': '', 'y': '',
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
            self.width = parent.profile.q["width"]
            self.height = parent.profile.q["height"]
            self.background = parent.profile.q["background"]
            self.fontcolor = parent.profile.q["font_color"]
            self.fontsize = parent.profile.q["font_size"]
            self.fontfamily = parent.profile.q["font_family"]
        else:
            self.setWindowTitle("Default style")
            self.width = preferences.q["width"]
            self.height = preferences.q["height"]
            self.background = preferences.q["background"]
            self.fontcolor = preferences.q["font_color"]
            self.fontsize = preferences.q["font_size"]
            self.fontfamily = preferences.q["font_family"]
            self.ui.defaultOpt.hide()

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

        self.style = self.exec()
        self.close()

    def closeEvent(self, event):
        if self.style:
            if self.type is mother or self.ui.defaultOpt.isChecked():
                preferences.save("style", "width", self.width)
                preferences.save("style", "height", self.height)
                preferences.save("style", "background", self.background)
                preferences.save("style", "font_color", self.fontcolor)
                preferences.save("style", "font_size", self.fontsize)
                preferences.save("style", "font_family", self.fontfamily)

            if self.type is child:
                self.parent.profile.save("width", self.width)
                self.parent.profile.save("height", self.height)
                self.parent.profile.save("background", self.background)
                self.parent.profile.save("font_color", self.fontcolor)
                self.parent.profile.save("font_size", self.fontsize)
                self.parent.profile.save("font_family", self.fontfamily)

        elif self.type is child:
            self.parent.ui.textEdit.viewport().update()
            self.parent.resize(self.parent.profile.q["width"], self.parent.profile.q["height"])

        if self.ui.allOpt.isChecked():
            if self.type is mother:
                children = self.parent.children
            elif self.type is child:
                children = self.parent.parent.children

            for f in list(children):
                children[f].profile.save("background", self.background)
                children[f].profile.save("width", self.width)
                children[f].profile.save("height", self.height)
                children[f].profile.save("background", self.background)
                children[f].profile.save("font_color", self.fontcolor)
                children[f].profile.save("font_size", self.fontsize)
                children[f].profile.save("font_family", self.fontfamily)
                children[f].loadStyle()
        event.accept()

    def pickBackgroundColor(self):
        cw = QtWidgets.QColorDialog(QtGui.QColor(self.background))
        cw.setWindowFlags(cw.windowFlags() | Qt.WindowStaysOnTopHint)
        cw.exec()
        color = cw.selectedColor()
        if color:
            self.background = color.name()
            self.ui.backgroundLabel.setText(color.name().upper())
            if self.type is child:
                palette = self.parent.ui.textEdit.viewport().palette()
                palette.setColor(QtGui.QPalette.Base, color)
                self.parent.ui.textEdit.viewport().setPalette(palette)

    def pickFontColor(self):
        cw = QtWidgets.QColorDialog(QtGui.QColor(self.fontcolor))
        cw.setWindowFlags(cw.windowFlags() | Qt.WindowStaysOnTopHint)
        cw.exec()
        color = cw.selectedColor()
        if color.isValid():
            self.fontcolor = color.name()
            self.ui.fontcolorLabel.setText(color.name().upper())
            if self.type is child:
                palette = self.parent.ui.textEdit.viewport().palette()
                palette.setColor(QtGui.QPalette.Text, color)
                self.parent.ui.textEdit.viewport().setPalette(palette)

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
        icons = ["tray", "quit", "file_active", "file_inactive", "enabled", "new", "hide", "show",
                    "reverse" ,"preferences", "image", "toggle", "reset", "file_pinned", "style"]
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
        self.trayIcon = QSystemTrayIcon()
        self.trayIcon.activated.connect(self.clickEvent)
        self.trayIcon.setIcon(self.icon["tray"])
        self.trayIcon.setContextMenu(self.menu)
        self.trayIcon.show()

        self.children = {}
        for f in os.listdir(DB):
            if f.endswith(".txt"):
                name = f.rsplit('.', 1)[0]
                if os.stat(DB + f).st_size > 0:
                    self.children[name] = child(self, DB + f)
                else:
                    os.remove(DB + f)
        self.cleanProfiles()

        if preferences.q["startup_action"]:
            self.action(preferences.q["startup_action"])

    #Actions
    def cleanProfiles(self):
        with open(PROFILES, "r+") as db:
            profiles = json.load(db)
            for entry in list(profiles):
                path = DB + entry + ".txt"
                if not os.path.isfile(path) or os.stat(path).st_size < 0:
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

    def refreshMenu(self):
        self.menu.clear()
        self.menu.addAction(self.icon["new"], 'New note', lambda: self.action("new"))
        self.menu.addAction(self.icon["toggle"], 'Toggle actives', lambda: self.action("toggle"))
        if not self.clipboardImg().isNull():
            self.menu.addAction(self.icon["image"], 'Paste image', lambda: self.action("image"))
        self.menu.addSeparator()
        self.menu.addAction(self.icon["hide"], 'Hide all', lambda: self.action("hide"))
        self.menu.addAction(self.icon["show"], 'Show all', lambda: self.action("show"))
        self.menu.addAction(self.icon["reverse"], 'Reverse all', lambda: self.action("reverse"))
        self.menu.addAction(self.icon["reset"], 'Reset', lambda: self.action("reset"))
        self.menu.addSeparator()

        for name in self.children:
            if self.children[name].profile.q["pin"]:
                self.menu.addAction(self.icon["file_pinned"], self.children[name].name, self.children[name].focus)
            elif name in preferences.q["actives"]:
                self.menu.addAction(self.icon["file_active"], self.children[name].name, self.children[name].focus)
            else:
                self.menu.addAction(self.icon["file_inactive"], self.children[name].name, self.children[name].focus)
        self.menu.addSeparator()

        self.menu.addMenu(self.submenu["preferences"])
        self.submenu["preferences"].clear()
        self.submenu["preferences"].addAction(self.icon["style"], "Default style", lambda: styleDialog(self))
        if preferences.q["top_level"]:
            self.submenu["preferences"].addAction(self.icon["enabled"], 'Always on top', lambda: self.action("top"))
        else:
            self.submenu["preferences"].addAction('Always on top', lambda: self.action("top"))
        if preferences.q["minimize"]:
            self.submenu["preferences"].addAction(self.icon["enabled"], "Minimize on startup", lambda: preferences.save("general", "minimize", False))
        else:
            self.submenu["preferences"].addAction("Minimize on startup", lambda: preferences.save("general", "minimize", True))
        if preferences.q["save_position"]:
            self.submenu["preferences"].addAction(self.icon["enabled"], "Save notes position", lambda: preferences.save("general", "save_position", False))
        else:
            self.submenu["preferences"].addAction("Save notes position", lambda: preferences.save("general", "save_position", True))
        if preferences.q["safe_delete"]:
            self.submenu["preferences"].addAction(self.icon["enabled"], "Safe delete", lambda: preferences.save("general", "safe_delete", False))
        else:
            self.submenu["preferences"].addAction("Safe delete", lambda: preferences.save("general", "safe_delete", True))

        menus = ["left_click_action", "middle_click_action", "startup_action"]
        for sm in menus:
            self.submenu["preferences"].addMenu(self.submenu[sm])
            self.submenu[sm].clear()
            self.submenu[sm].addAction(self.icon["toggle"], "Toggle actives", lambda sm=sm: preferences.save("general", sm, "toggle"))
            self.submenu[sm].addAction(self.icon["new"], "Create new note", lambda sm=sm: preferences.save("general", sm, "new"))
            self.submenu[sm].addAction(self.icon["show"], "Show all", lambda sm=sm: preferences.save("general", sm, "show"))
            self.submenu[sm].addAction(self.icon["hide"], "Hide all", lambda sm=sm: preferences.save("general", sm, "hide"))
            self.submenu[sm].addAction(self.icon["reverse"], "Reverse all", lambda sm=sm: preferences.save("general", sm, "reverse"))
            self.submenu[sm].addAction(self.icon["reset"], "Reset notes", lambda sm=sm: preferences.save("general", sm, "reset"))
            self.submenu[sm].addAction(self.icon["image"], "Paste image", lambda sm=sm: preferences.save("general", sm, "image"))
            self.submenu[sm].addAction("None", lambda sm=sm: preferences.save("general", sm, ""))
        self.menu.addAction(self.icon["quit"], 'Quit', app.exit)

    def new(self, isImage = False):
        name = "Untitled 1"
        n = 1
        while name in self.children:
            n += 1
            name = "Untitled " + str(n)
        self.children[name] = child(self, DB + name + ".txt", isImage)
        self.children[name].show()
        return name

    def action(self, action):
        if action == "new":
            self.new()

        elif action == "image":
            pixmap = self.clipboardImg()
            if not pixmap.isNull():
                name = self.children[self.new(isImage = True)]
                name.ui.textEdit.hide()
                name.ui.imageLabel.show()
                width, height = pixmap.width(), pixmap.height()
                widthMax = QtWidgets.QDesktopWidget().screenGeometry().width() * 0.8
                heightMax = QtWidgets.QDesktopWidget().screenGeometry().height() * 0.8
                if width > widthMax:
                    width = widthMax
                if height > heightMax:
                    height = heightMax
                name.resize(width, height)

                picture = name.ui.imageLabel
                picture.setScaledContents(True)
                picture.setContextMenuPolicy(Qt.CustomContextMenu)
                picture.customContextMenuRequested.connect(lambda: name.menu.popup(QtGui.QCursor.pos()))
                picture.setPixmap(pixmap)
                picture.show()

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

            #Remove notes without assigned file
            for f in list(self.children):
                if not os.path.isfile(self.children[f].path):
                    self.children[f].delete()

            #Remove unassigned profiles
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

        self.menu = QtWidgets.QMenu()
        icons = ["hide", "quit", "delete", "rename", "tray", "pin_menu", "pin_title", "toggle", "style"]
        self.icon = {}
        for icon in icons:
            self.icon[icon] = QtGui.QIcon(ICONS + icon + ".svg")
        self.menu.addAction(self.icon["hide"], '&Hide', self.hide)
        self.menu.addAction(self.icon["pin_menu"], '&Pin', self.pin)
        self.menu.addAction(self.icon["rename"], '&Rename', self.rename)
        if not isImage:
            self.menu.addAction(self.icon["style"], "Style", lambda: styleDialog(self))
        self.menu.addSeparator()
        self.menu.addAction(self.icon["quit"], 'Close', self.quit)
        self.menu.addAction(self.icon["delete"], '&Delete', self.delete)

        self.loadStyle()
        self.setWindowTitle(self.name)
        self.setAttribute(Qt.WA_X11NetWmWindowTypeToolBar)
        self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        self.ui.imageLabel.hide()
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

        self.ui.textEdit.focusOutEvent = self.focusOutEvent
        self.ui.textEdit.focusInEvent = self.focusInEvent
        self.ui.textEdit.dropEvent = self.dropEvent
        self.ui.textEdit.keyPressEvent = self.keyPressEvent
        self.ui.textEdit.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.textEdit.customContextMenuRequested.connect(lambda: self.menu.popup(QtGui.QCursor.pos()))
        self.ui.textEdit.setAttribute(Qt.WA_TranslucentBackground)

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
                self.ui.textEdit.setPlainText(f.read())

        if not preferences.q["minimize"]:
            self.show()

    #Action
    def focus(self):
        self.show()
        self.activateWindow()

    def quit(self):
        #if self.name in self.parent.children:
        del self.parent.children[self.name]
        self.name = ""
        self.close()

    def delete(self):
        self.profile.load()
        #if self.name in self.profile.db:
        del self.profile.db[self.name]
        with open(PROFILES, "w+") as f:
            f.write(json.dumps(self.profile.db, indent=2, sort_keys=False))

        #if self.name in self.parent.children:
        del self.parent.children[self.name]

        if os.path.isfile(self.path):
            if preferences.q["safe_delete"] and os.stat(self.path).st_size > 0:
                os.rename(self.path, self.path + ".old")
            else:
                os.remove(self.path)
        self.name = ""
        self.close()

    def loadStyle(self):
        self.profile.load()
        palette = self.ui.textEdit.viewport().palette()
        palette.setColor(QtGui.QPalette.Base, QtGui.QColor(self.profile.q["background"]))
        palette.setColor(QtGui.QPalette.Text, QtGui.QColor(self.profile.q["font_color"]))
        self.ui.textEdit.viewport().setPalette(palette)

        font = self.ui.textEdit.font()
        font.setFamily(self.profile.q["font_family"])
        font.setPointSize(self.profile.q["font_size"])
        self.ui.textEdit.setFont(font)

        self.ui.textEdit.viewport().update()

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
                entry = self.ui.renameText.text()
                entry = "".join(x for x in entry if x.isalnum() or x is " ") #Remove illegal characters

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

    def keyPressEvent(self, event):
        key = event.key()
        if int(event.modifiers()) == (Qt.ControlModifier + Qt.ShiftModifier):
            isCtrl = True
            isShift = True
        else:
            isCtrl = (event.modifiers() == Qt.ControlModifier)
            isShift = (event.modifiers() == Qt.ShiftModifier)
            isAlt = (event.modifiers() == Qt.AltModifier)
            isCaps = (key == Qt.Key_CapsLock)

        if key == Qt.Key_H and isCtrl:
            self.hide()
        elif key == Qt.Key_P and isCtrl:
            self.pin()
        elif key == Qt.Key_R and isCtrl:
            self.rename()
        elif key == Qt.Key_Q and isCtrl:
            self.quit()
        elif key == Qt.Key_Delete and isCtrl:
            self.delete()
        elif key == Qt.Key_V and isCtrl and isShift:
            txt = clipboard.text()
            txt = txt.replace("\n", " ").replace("\t", " ")
            self.ui.textEdit.insertPlainText(txt)

        elif key == Qt.Key_Up and isCtrl:
            width, height = self.width() + 20, self.height() + 20
            self.resize(width, height)
        elif key == Qt.Key_Down and isCtrl:
            width, height = self.width() - 20, self.height() - 20
            self.resize(width, height)

        elif key == Qt.Key_Equal and isCtrl and self.ui.textEdit.isVisible():
            font = self.ui.textEdit.font()
            size = font.pointSize() + 1
        elif key == Qt.Key_Minus and isCtrl and self.ui.textEdit.isVisible():
            font = self.ui.textEdit.font()
            size = font.pointSize() - 1

        else:
            QtWidgets.QPlainTextEdit.keyPressEvent(self.ui.textEdit, event)
            if not self.windowTitle()[-1] == "*" and self.ui.textEdit.isVisible():
                if (isCtrl and key == Qt.Key_V) or (not isCtrl and not isAlt and not isCaps):
                    self.setWindowTitle(self.windowTitle() + "*")

        if 'size' in locals():
            font.setPointSize(size)
            self.ui.textEdit.setFont(font)
            self.profile.save("font_size", size)

    def focusOutEvent(self, event):
        if self.name:
            QtWidgets.QPlainTextEdit.focusOutEvent(self.ui.textEdit, event)
            self.save()

    def focusInEvent(self, event):
        QtWidgets.QPlainTextEdit.focusInEvent(self.ui.textEdit, event)
        self.load(self.name)

if __name__== '__main__':
    preferences = preferences()
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    clipboard = app.clipboard()
    daemon = mother()
    sys.exit(app.exec())

