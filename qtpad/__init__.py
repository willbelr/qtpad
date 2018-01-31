#!/usr/bin/python3
import json
import logging
import os
import requests
import sys
import time
from PyQt5 import QtGui, QtWidgets, QtCore, QtDBus, uic
from PyQt5.QtCore import Qt, QThread, QObject, QProcess, pyqtSignal, pyqtSlot
try:
    # Load pre-compiled Ui files if available
    import qtpad.gui_child
    import qtpad.gui_preferences
    import qtpad.gui_profile
except ImportError:
    pass

class QDBusServer(QObject):
    def __init__(self):
        QObject.__init__(self)
        self.__dbusAdaptor = QDBusServerAdapter(self)


class QDBusServerAdapter(QtDBus.QDBusAbstractAdaptor):
    QtCore.Q_CLASSINFO("D-Bus Interface", "org.qtpad.session")
    QtCore.Q_CLASSINFO("D-Bus Introspection",
    '  <interface name="org.qtpad.session">\n'
    '    <method name="parse">\n'
    '      <arg direction="in" type="s" name="cmd"/>\n'
    '    </method>\n'
    '  </interface>\n')

    def __init__(self, parent):
        super().__init__(parent)

    @pyqtSlot(str, str, result=str)
    def parse(self, cmd, arg):
        daemon.parse(cmd, arg)


class Preferences(object):
    def __init__(self):
        if os.path.isfile(PREFERENCES_FILE) and os.stat(PREFERENCES_FILE).st_size > 0:
            self.load()
        else:
            self.db = PREFERENCES_DEFAULT
            with open(PREFERENCES_FILE, "w") as f:
                f.write(json.dumps(self.db, indent=2, sort_keys=False))
            logger.info("Created preferences file")
        self.parse()

    def load(self):
        with open(PREFERENCES_FILE, "r") as f:
            self.db = json.load(f)
        logger.info("Loaded preferences database")

    def set(self, name, entry, value=None):
        if name == "actives":
            self.db[name] = entry
            self.save()
        else:
            self.db[name][entry] = value

    def save(self):
        with open(PREFERENCES_FILE, "w") as f:
            f.write(json.dumps(self.db, indent=2, sort_keys=False))
        self.parse()
        logger.info("Saved preferences database")

    def parse(self):
        self.q = {}
        for category in self.db:
            if type(self.db[category]) is dict:
                for key in self.db[category]:
                    self.q[key] = self.db[category][key]
            else:
                self.q[category] = self.db[category]

    def query(self, entry):
        if entry not in self.q:
            db = {}
            for category in PREFERENCES_DEFAULT:
                for key in PREFERENCES_DEFAULT[category]:
                    db[key] = PREFERENCES_DEFAULT[category][key]

            self.q[entry] = db[entry]
            logger.error("Key '" + entry + "' is missing in preferences database, using default value (" + str(db[entry]) + ")")
        return self.q[entry]


class PreferencesDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__()
        if "qtpad.gui_preferences" in sys.modules:
            self.ui = qtpad.gui_preferences.Ui_Dialog()
            self.ui.setupUi(self)
        else:
            self.ui = uic.loadUi(LOCAL_DIR + 'gui_preferences.ui', self)
        self.parent = parent
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setFixedSize(530, 250)

        actions = ['Toggle actives', 'New note', 'Fetch clipboard or new note', 'Show all', 'Hide all', 'Reverse all', 'Reset positions', 'Fetch clipboard', 'Exec', 'None']
        self.ui.leftClickCombo.addItems(actions)
        self.ui.middleClickCombo.addItems(actions)
        self.ui.startupCombo.addItems(actions)
        self.ui.leftClickCombo.setCurrentText(preferences.query("leftClickAction"))
        self.ui.cmdLeftText.setText(preferences.query("cmdLeft"))
        self.ui.middleClickCombo.setCurrentText(preferences.query("middleClickAction"))
        self.ui.cmdMiddleText.setText(preferences.query("cmdMiddle"))
        self.ui.startupCombo.setCurrentText(preferences.query("startupAction"))
        self.ui.cmdStartupText.setText(preferences.query("cmdStartup"))
        self.ui.defaultNameTxtText.setText(preferences.query("defaultNameTxt"))
        self.ui.defaultNameImgText.setText(preferences.query("defaultNameImg"))
        self.ui.alwaysOnTopBox.setChecked(preferences.query("alwaysOnTop"))
        self.ui.minimizeBox.setChecked(preferences.query("minimize"))
        self.ui.hotkeysBox.setChecked(preferences.query("hotkeys"))
        self.ui.safeDeleteBox.setChecked(preferences.query("safeDelete"))
        self.ui.deleteEmptyNotesBox.setChecked(preferences.query("deleteEmptyNotes"))
        self.ui.framelessBox.setChecked(preferences.query("frameless"))
        self.ui.fetchClearBox.setChecked(preferences.query("fetchClear"))
        self.ui.fetchUrlBox.setChecked(preferences.query("fetchUrl"))
        self.ui.fetchFileBox.setChecked(preferences.query("fetchFile"))
        self.ui.fetchTxtBox.setChecked(preferences.query("fetchTxt"))
        self.ui.fetchIconBox.setChecked(preferences.query("fetchIcon"))
        self.ui.leftClickCombo.currentTextChanged.connect(self.toggleCmdWidgets)
        self.ui.middleClickCombo.currentTextChanged.connect(self.toggleCmdWidgets)
        self.ui.startupCombo.currentTextChanged.connect(self.toggleCmdWidgets)
        self.ui.listWidget.selectionModel().selectionChanged.connect(self.menuEvent)
        self.ui.listWidget.setFocus()
        self.toggleCmdWidgets()
        self.done = self.exec_()
        self.close()

    def toggleCmdWidgets(self):
        if self.ui.leftClickCombo.currentText() == "Exec":
            self.ui.cmdLeftLabel.show()
            self.ui.cmdLeftText.show()
            self.ui.cmdLeftLine.show()
        else:
            self.ui.cmdLeftLabel.hide()
            self.ui.cmdLeftText.hide()
            self.ui.cmdLeftLine.hide()

        if self.ui.middleClickCombo.currentText() == "Exec":
            self.ui.cmdMiddleLabel.show()
            self.ui.cmdMiddleText.show()
            self.ui.cmdMiddleLine.show()
        else:
            self.ui.cmdMiddleLabel.hide()
            self.ui.cmdMiddleText.hide()
            self.ui.cmdMiddleLine.hide()

        if self.ui.startupCombo.currentText() == "Exec":
            self.ui.cmdStartupLabel.show()
            self.ui.cmdStartupText.show()
        else:
            self.ui.cmdStartupLabel.hide()
            self.ui.cmdStartupText.hide()

    def menuEvent(self):
        self.ui.stackedWidget.setCurrentIndex(self.ui.listWidget.currentRow())

    def closeEvent(self, event):
        if self.done:
            alwaysOnTopChanged = not self.ui.alwaysOnTopBox.isChecked() == preferences.query("alwaysOnTop")
            frameChanged = not self.ui.framelessBox.isChecked() == preferences.query("frameless")
            preferences.load()
            preferences.set("general", "leftClickAction", self.ui.leftClickCombo.currentText())
            preferences.set("general", "cmdLeft", self.ui.cmdLeftText.text())
            preferences.set("general", "middleClickAction", self.ui.middleClickCombo.currentText())
            preferences.set("general", "cmdMiddle", self.ui.cmdMiddleText.text())
            preferences.set("general", "startupAction", self.ui.startupCombo.currentText())
            preferences.set("general", "cmdStartup", self.ui.cmdStartupText.text())
            preferences.set("general", "defaultNameTxt", self.ui.defaultNameTxtText.text())
            preferences.set("general", "defaultNameImg", self.ui.defaultNameImgText.text())
            preferences.set("general", "minimize", self.ui.minimizeBox.isChecked())
            preferences.set("general", "hotkeys", self.ui.hotkeysBox.isChecked())
            preferences.set("general", "safeDelete", self.ui.safeDeleteBox.isChecked())
            preferences.set("general", "deleteEmptyNotes", self.ui.deleteEmptyNotesBox.isChecked())
            preferences.set("general", "alwaysOnTop", self.ui.alwaysOnTopBox.isChecked())
            preferences.set("general", "frameless", self.ui.framelessBox.isChecked())
            preferences.set("general", "fetchClear", self.ui.fetchClearBox.isChecked())
            preferences.set("general", "fetchUrl", self.ui.fetchUrlBox.isChecked())
            preferences.set("general", "fetchFile", self.ui.fetchFileBox.isChecked())
            preferences.set("general", "fetchTxt", self.ui.fetchTxtBox.isChecked())
            preferences.set("general", "fetchIcon", self.ui.fetchIconBox.isChecked())
            preferences.save()

            if alwaysOnTopChanged or frameChanged:
                for name in self.parent.children:
                    isVisible = self.parent.children[name].isVisible()
                    self.parent.children[name].refreshWindowState(updateFrame=frameChanged)
                    time.sleep(0.1)
                    if isVisible:
                        self.parent.children[name].display()
        event.accept()


class Profile(object):
    def __init__(self, path, mother):
        self.path = path
        self.name = path.rsplit('/', 1)[-1].rsplit('.', 1)[0]
        if os.path.isfile(PROFILES_FILE) and os.stat(PROFILES_FILE).st_size > 0:
            self.load()
        else:
            self.db = {}
        if self.name not in self.db:
            self.db[self.name] = preferences.db["styleDefault"]

            x = QtWidgets.QDesktopWidget().screenGeometry().width() - preferences.query("width")
            x = x - (len(mother.children) * 28)
            y = (preferences.query("height")/2) + (len(mother.children) * 28)
            self.db[self.name]["x"] = x
            self.db[self.name]["y"] = y

            with open(PROFILES_FILE, 'w') as f:
                f.write(json.dumps(self.db, indent=2, sort_keys=False))
            logger.info("Created profile for '" + self.name + "'")
        self.parse()

    def load(self):
        with open(PROFILES_FILE) as f:
            self.db = json.load(f)
        logger.info("Loaded profiles database (" + self.name + ")")

    def set(self, entry, value):
        if self.name in self.db:
            self.db[self.name][entry] = value

    def save(self, entry=None, value=None):
        if entry and value is not None:
            self.load()
            self.set(entry, value)

        with open(PROFILES_FILE, "w") as f:
            f.write(json.dumps(self.db, indent=2, sort_keys=False))
        self.parse()
        logger.info("Saved profile database (" + self.name + ")")

    def parse(self):
        if self.name in self.db:
            self.q = {}
            for entry in self.db[self.name]:
                self.q[entry] = self.db[self.name][entry]

    def query(self, entry):
        if entry not in self.q:
            self.q[entry] = PREFERENCES_DEFAULT["styleDefault"][entry]
            logger.error("Key '" + entry + "' is missing in profiles database, using default value (" + str(self.q[entry]) + ")")
        return self.q[entry]


class ProfileDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__()
        if "qtpad.gui_profile" in sys.modules:
            self.ui = qtpad.gui_profile.Ui_Dialog()
            self.ui.setupUi(self)
        else:
            self.ui = uic.loadUi(LOCAL_DIR + 'gui_profile.ui', self)
        self.parent = parent
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setWindowTitle("Style for '" + parent.name + "'")
        self.setFixedSize(450, 170)

        fetch = parent.profile.query
        self.width = fetch("width")
        self.height = fetch("height")
        self.background = fetch("background")
        self.fontColor = fetch("fontColor")
        self.fontSize = fetch("fontSize")
        self.fontFamily = fetch("fontFamily")

        font = QtGui.QFont()
        font.setFamily(self.fontFamily)
        self.ui.fontFamilyCombo.setCurrentFont(font)

        self.ui.backgroundLabel.setText(self.background.upper())
        self.ui.fontColorLabel.setText(self.fontColor.upper())
        self.ui.widthBox.setValue(self.width)
        self.ui.heightBox.setValue(self.height)
        self.ui.fontSizeBox.setValue(self.fontSize)

        self.ui.fontFamilyCombo.currentFontChanged.connect(self.updateFontfamily)
        self.ui.backgroundButton.clicked.connect(self.pickBackgroundColor)
        self.ui.fontColorButton.clicked.connect(self.pickFontColor)
        self.ui.widthBox.valueChanged.connect(self.updateWidth)
        self.ui.heightBox.valueChanged.connect(self.updateHeight)
        self.ui.fontSizeBox.valueChanged.connect(self.updateFontsize)

        self.done = self.exec_()
        self.close()

    def closeEvent(self, event):
        if self.done:
            if self.ui.defaultBox.isChecked():
                preferences.set("styleDefault", "width", self.width)
                preferences.set("styleDefault", "height", self.height)
                preferences.set("styleDefault", "background", self.background)
                preferences.set("styleDefault", "fontColor", self.fontColor)
                preferences.set("styleDefault", "fontSize", self.fontSize)
                preferences.set("styleDefault", "fontFamily", self.fontFamily)
                preferences.save()

            if self.ui.allBox.isChecked():
                children = self.parent.parent.children
                for f in list(children):
                    children[f].profile.load()
                    children[f].profile.set("width", self.width)
                    children[f].profile.set("height", self.height)
                    children[f].profile.set("background", self.background)
                    children[f].profile.set("fontColor", self.fontColor)
                    children[f].profile.set("fontSize", self.fontSize)
                    children[f].profile.set("fontFamily", self.fontFamily)
                    children[f].profile.save()
                    children[f].loadStyle()

            self.parent.profile.load()
            self.parent.profile.set("width", self.width)
            self.parent.profile.set("height", self.height)
            self.parent.profile.set("background", self.background)
            self.parent.profile.set("fontColor", self.fontColor)
            self.parent.profile.set("fontSize", self.fontSize)
            self.parent.profile.set("fontFamily", self.fontFamily)
            self.parent.profile.save()
            self.parent.ui.textEdit.viewport().update()
            self.parent.resize(self.parent.profile.query("width"), self.parent.profile.query("height"))
        self.parent.loadStyle()
        event.accept()

    def pickColor(self, target, color):
        self.target = target
        self.colorWidget = QtWidgets.QColorDialog(QtGui.QColor(color))
        self.colorWidget.setWindowFlags(self.colorWidget.windowFlags() | Qt.WindowStaysOnTopHint)
        self.colorWidget.currentColorChanged.connect(self.colorChanged)
        self.colorWidget.exec_()
        return self.colorWidget.selectedColor()

    def colorChanged(self):
        color = self.colorWidget.currentColor()
        if self.target == "background":
            self.parent.setBackgroundColor(color)
        elif self.target == "font":
            self.parent.setFontColor(color)

    def pickBackgroundColor(self):
        color = self.pickColor("background", self.background)
        if color.isValid():
            self.background = color.name()
            self.ui.backgroundLabel.setText(color.name().upper())
            self.parent.setBackgroundColor(color)
        else:
            color = QtGui.QColor(self.ui.backgroundLabel.text())
            self.parent.setBackgroundColor(color)

    def pickFontColor(self):
        color = self.pickColor("font", self.fontColor)
        if color.isValid():
            self.fontColor = color.name()
            self.ui.fontColorLabel.setText(color.name().upper())
            self.parent.setFontColor(color)
        else:
            color = QtGui.QColor(self.ui.fontColorLabel.text())
            self.parent.setFontColor(color)

    def updateWidth(self):
        self.width = self.ui.widthBox.value()
        self.parent.resize(self.width, self.parent.height())

    def updateHeight(self):
        self.height = self.ui.heightBox.value()
        self.parent.resize(self.parent.width(), self.height)

    def updateFontsize(self):
        self.fontSize = self.ui.fontSizeBox.value()
        font = self.parent.ui.textEdit.font()
        font.setPointSize(self.fontSize)
        self.parent.ui.textEdit.setFont(font)

    def updateFontfamily(self):
        self.fontFamily = self.ui.fontFamilyCombo.currentText()
        font = self.parent.ui.textEdit.font()
        font.setFamily(self.fontFamily)
        self.parent.ui.textEdit.setFont(font)


class Mother(object):
    def __init__(self, parent=None):
        self.children = {}
        self.load()
        icons = ["tray", "quit", "file_active", "file_inactive", "new", "hide", "show", "reverse",
                  "preferences", "image", "toggle", "reset", "file_pinned", "file_image"]
        self.icon = {}
        for icon in icons:
            self.icon[icon] = QtGui.QIcon(ICONS_DIR + icon + ".svg")

        self.menu = QtWidgets.QMenu()
        self.menu.aboutToShow.connect(self.refreshMenu)
        self.trayIcon = QtWidgets.QSystemTrayIcon()
        self.trayIcon.activated.connect(self.clickEvent)

        # Handle svg to pixmap conversion (KDE compatibility)
        trayIcon = self.icon["tray"].pixmap(64, 64)
        trayIcon = QtGui.QIcon(trayIcon)
        self.trayIcon.setIcon(trayIcon)

        self.refreshMenu()
        self.trayIcon.setContextMenu(self.menu)
        self.trayIcon.show()

        if preferences.query("startupAction"):
            action = preferences.query("startupAction")
            cmd = preferences.query("cmdStartup")
            self.action(action, cmd)

    def parse(self, cmd, arg):
        if cmd == "-a" or cmd == "--action":
            logger.info("Call action '%s' from command" % cmd + " " + arg)
            self.action(arg)

    def load(self):
        for f in os.listdir(DB_DIR):
            name = f.rsplit('.', 1)[0]
            if name not in self.children:
                if f.endswith(".txt"):
                    if os.stat(DB_DIR + f).st_size == 0 and preferences.query("deleteEmptyNotes"):
                        logger.warning("Removed '" + name + "' (empty)")
                        os.remove(DB_DIR + f)
                    else:
                        self.children[name] = Child(self, DB_DIR + f)
                elif f.endswith(".png"):
                    self.children[name] = Child(self, DB_DIR + f, image=QtGui.QPixmap(f))
        self.cleanProfiles()

    def new(self, image=None, text=None):
        if image:
            prefix = preferences.query("defaultNameImg")
        else:
            prefix = preferences.query("defaultNameTxt")
        name = prefix + " 1"
        n = 1
        while name in self.children:
            n += 1
            name = prefix + " " + str(n)

        if image:
            self.children[name] = Child(self, DB_DIR + name + ".png", isNew=True, image=image)
        else:
            self.children[name] = Child(self, DB_DIR + name + ".txt", isNew=True, text=text)
        return name

    def refreshMenu(self):
        # Monitor changes in the database directory, clear old menu
        self.load()
        self.cleanOrphans()
        self.menu.clear()

        self.menu.addAction(self.icon["new"], 'New note', lambda: self.action("New note"))
        self.menu.addAction(self.icon["toggle"], 'Toggle actives', lambda: self.action("Toggle actives"))
        if preferences.query("fetchIcon") and self.fetchClipboard():
            self.menu.addAction(self.icon["image"], 'Fetch clipboard', lambda: self.action("Fetch clipboard"))
        self.menu.addSeparator()
        self.menu.addAction(self.icon["hide"], 'Hide all', lambda: self.action("Hide all"))
        self.menu.addAction(self.icon["show"], 'Show all', lambda: self.action("Show all"))
        self.menu.addAction(self.icon["reverse"], 'Reverse all', lambda: self.action("Reverse all"))
        self.menu.addAction(self.icon["reset"], 'Reset positions', lambda: self.action("Reset positions"))
        self.menu.addSeparator()

        # List of children windows
        for name in self.children:
            if self.children[name].profile.query("pin"):
                icon = self.icon["file_pinned"]
            elif name in preferences.query("actives"):
                icon = self.icon["file_active"]
            elif self.children[name].isImage:
                icon = self.icon["file_image"]
            else:
                icon = self.icon["file_inactive"]
            self.menu.addAction(icon, self.children[name].name, self.children[name].display)
        self.menu.addSeparator()

        self.menu.addAction(self.icon["preferences"], "Preferences", lambda: PreferencesDialog(self))
        self.menu.addAction(self.icon["quit"], 'Quit', app.exit)

    def action(self, action, cmd=None):
        if action == "New note":
            self.new()

        elif action == "Fetch clipboard":
            fetch = self.fetchClipboard(newNote=True)

        elif action == "Fetch clipboard or new note":
            fetch = self.fetchClipboard(newNote=True)
            if not fetch:
                self.new()

        elif action == "Toggle actives":
            actives = []
            for name in self.children:
                children = self.children[name]
                if children.profile.query("pin"):
                    children.activateWindow()
                elif children.isVisible():
                    actives.append(children.name)

            if actives:
                preferences.set("actives", actives)
                self.action("Hide all")
            elif preferences.query("actives"):
                for note in preferences.query("actives"):
                    if note in self.children:
                        self.children[note].display()

        elif action == "Hide all":
            for name in list(self.children):
                children = self.children[name]
                if children.isVisible() and not children.profile.query("pin"):
                    children.close()

        elif action == "Show all":
            for name in self.children:
                if not self.children[name].isVisible():
                    self.children[name].display()

        elif action == "Reverse all":
            for name in list(self.children):
                children = self.children[name]
                if children.isVisible():
                    if not children.profile.query("pin"):
                        children.close()
                else:
                    children.display()

        elif action == "Reset positions":
            # Remove orhans and unassigned profiles
            self.cleanOrphans()
            self.cleanProfiles()

            # Reset position
            n = 0
            _x = QtWidgets.QDesktopWidget().screenGeometry().width() - preferences.query("width")
            _y = preferences.query("height") / 2
            for name in self.children:
                children = self.children[name]
                width = preferences.query("width")
                height = preferences.query("height")
                n += 28
                x = _x - n
                y = _y + n
                children.display()
                children.setGeometry(x, y, width, height)
                children.profile.load()
                children.profile.set("x", x)
                children.profile.set("y", y)
                children.profile.set("width", width)
                children.profile.set("height", height)
                children.profile.save()

        elif action == "Exec":
            if cmd:
                logger.info("Starting '%s'", cmd)
                slave = QProcess()
                slave.startDetached(cmd)

    def fetchClipboard(self, newNote=False):
        pixmap = clipboard.pixmap()
        path = clipboard.text().rstrip()
        textContent = None
        if pixmap.isNull():
            if os.path.isfile(path) and os.stat(path).st_size > 0:
                allowed = ["txt", "gif", "png", "bmp", "jpg", "jpeg", "svg"]
                ext = path.lower().rsplit('.', 1)[-1]
                if ext in allowed:
                    if preferences.query("fetchTxt") and ext == "txt":
                        with open(path) as f:
                            textContent = f.read()
                    elif preferences.query("fetchFile"):
                        pixmap = QtGui.QPixmap(path)

            elif preferences.query("fetchUrl") and (path.startswith("http://") or path.startswith("https://") or path.startswith("www.")):
                # Do not try to get header if the link point to a pdf
                if path.lower().find(".pdf") == -1:
                    allowed = ['jpeg', 'gif', 'png', 'bmp', 'svg+xml']
                    try:
                        mimetype = requests.get(path).headers["content-type"].split('/')[1]
                        if mimetype in allowed:
                            fetch = requests.get(path)
                            pixmap.loadFromData(fetch.content)
                    except:
                        logger.warning(str(sys.exc_info()[0]), str(sys.exc_info()[1]))

        if textContent or not pixmap.isNull():
            if newNote:
                if textContent:
                    self.children[self.new(text=textContent)]
                    logger.info("Fetched text from " + path)
                else:
                    self.children[self.new(image=pixmap)]
                    logger.info("Fetched image from " + (path if path else "clipboard"))

                if preferences.query("fetchClear"):
                    clipboard.setText("")
                    logger.warning("Emptied clipboard content")
            return True
        return False

    def cleanOrphans(self):
        for f in list(self.children):
            if not os.path.isfile(self.children[f].path):
                logger.warning("Removed '" + self.children[f].name + "' (orphan)")
                self.children[f].remove()

    def cleanProfiles(self):
        if os.path.isfile(PROFILES_FILE):
            with open(PROFILES_FILE, "r+") as db:
                profiles = json.load(db)
                for entry in list(profiles):
                    txtPath = DB_DIR + entry + ".txt"
                    pngPath = DB_DIR + entry + ".png"
                    if not os.path.isfile(pngPath) and (not os.path.isfile(txtPath) or os.stat(txtPath).st_size < 0):
                        del profiles[entry]
                db.seek(0)
                db.truncate()
                db.write(json.dumps(profiles, indent=2, sort_keys=False))

    def clickEvent(self, event):
        # Left click
        if event == 3:
            action = preferences.query("leftClickAction")
            cmd = preferences.query("cmdLeft")
            self.action(action, cmd)

        # Middle click
        elif event == 4:
            action = preferences.query("middleClickAction")
            cmd = preferences.query("cmdMiddle")
            self.action(action, cmd)


class Child(QtWidgets.QWidget):
    def __init__(self, parent, path, isNew=False, image=None, text=None):
        super().__init__()

        # Load common settings
        if "qtpad.gui_child" in sys.modules:
            self.ui = qtpad.gui_child.Ui_Form()
            self.ui.setupUi(self)
        else:
            self.ui = uic.loadUi(LOCAL_DIR + 'gui_child.ui', self)

        self.profile = Profile(path, parent)
        self.parent = parent
        self.path = path
        self.name = path.rsplit('/', 1)[-1].rsplit('.', 1)[0]
        if os.environ.get('DESKTOP_SESSION') == "openbox":
            self.setAttribute(Qt.WA_X11NetWmWindowTypeToolBar)
        else:
            self.setAttribute(Qt.WA_X11NetWmWindowTypeUtility)
        self.ui.renameText.hide()
        self.ui.renameLabel.hide()
        self.ui.line.hide()
        self.ui.renameText.keyPressEvent = self.renameEvent
        self.ui.renameText.focusOutEvent = self.renameEvent
        self.ui.titleLabel.mousePressEvent = self.titleLabelMousePressEvent
        self.ui.titleLabel.mouseMoveEvent = self.titleLabelMouseMoveEvent
        self.sizeGrip = QtWidgets.QSizeGrip(self)
        self.ui.bottomLayout.addWidget(self.sizeGrip)
        self.ui.bottomLayout.setAlignment(self.sizeGrip, Qt.AlignRight)

        # Loading context menu
        icons = ["hide", "delete", "rename", "tray", "pin_menu", "pin_title", "toggle", "style", "image", "file_inactive", "preferences", "new"]
        self.icon = {}
        for icon in icons:
            self.icon[icon] = QtGui.QIcon(ICONS_DIR + icon + ".svg")
        self.menu = QtWidgets.QMenu()
        self.menu.addAction(self.icon["new"], 'New note', lambda: self.parent.action("New note"))
        self.menu.addAction(self.icon["rename"], 'Rename', self.renameEvent)
        self.submenu = QtWidgets.QMenu("Style")
        self.submenu.setIcon(self.icon["style"])
        self.submenu.addAction(self.icon["preferences"], "Customize", lambda: ProfileDialog(self))
        self.submenu.addSeparator()

        # Load style presets and replace transparency with background color, foreground with 'fontColor'
        for entry in preferences.db["stylePreset"]:
            background = preferences.db["stylePreset"][entry]["background"]
            fontColor = preferences.db["stylePreset"][entry]["fontColor"]
            pixmap = QtGui.QPixmap(ICONS_DIR + "rename.svg")
            painter = QtGui.QPainter(pixmap)
            painter.setCompositionMode(painter.CompositionMode_Xor)
            painter.fillRect(pixmap.rect(), QtGui.QColor(background))
            painter.setCompositionMode(painter.CompositionMode_Overlay)
            painter.fillRect(pixmap.rect(), QtGui.QColor(fontColor))
            painter.end()
            icon = QtGui.QIcon(pixmap)
            self.submenu.addAction(icon, entry, lambda background=background, fontColor=fontColor: self.setStyle(background, fontColor, updateProfile=True))
        self.menu.addMenu(self.submenu)
        self.menu.addAction(self.icon["pin_menu"], 'Pin', self.pin)

        # Customize context menu according to note type (image or text)
        if image:
            self.isImage = True
            self.ui.textEdit.hide()
            self.ui.imageLabel.setScaledContents(True)
            self.ui.imageLabel.setContextMenuPolicy(Qt.CustomContextMenu)
            self.ui.imageLabel.customContextMenuRequested.connect(lambda: self.menu.popup(QtGui.QCursor.pos()))
            self.ui.imageLabel.setFocusPolicy(Qt.StrongFocus)
            self.ui.imageLabel.focusOutEvent = self.focusOutEvent
            self.menu.addAction(self.icon["image"], 'Save image as', self.saveImageToFile)
            self.menu.addAction(self.icon["image"], 'Copy to clipboard', self.saveImageToClipboard)
            if not os.path.isfile(path):
                f = QtCore.QFile(DB_DIR + self.name + ".png")
                f.open(QtCore.QIODevice.WriteOnly)
                image.save(f, "PNG")
                width, height = image.width(), image.height()
            else:
                width, height = self.profile.query("width"), self.profile.query("height")

            with open(path) as f:
                image = QtGui.QPixmap(path)
            widthMax = QtWidgets.QDesktopWidget().screenGeometry().width() * 0.8
            heightMax = QtWidgets.QDesktopWidget().screenGeometry().height() * 0.8
            if width > widthMax or height > heightMax:
                width = widthMax
                height = heightMax
            self.resize(width, height)
            self.ui.imageLabel.setPixmap(image)
        else:
            self.isImage = False
            self.ui.imageLabel.hide()
            self.ui.textEdit.focusOutEvent = self.focusOutEvent
            self.ui.textEdit.focusInEvent = self.focusInEvent
            self.ui.textEdit.dropEvent = self.dropEvent
            self.ui.textEdit.keyPressEvent = self.keyPressEvent
            self.ui.textEdit.setContextMenuPolicy(Qt.CustomContextMenu)
            self.ui.textEdit.customContextMenuRequested.connect(lambda: self.menu.popup(QtGui.QCursor.pos()))
            self.ui.textEdit.setAttribute(Qt.WA_TranslucentBackground)
            self.menu.addAction(self.icon["file_inactive"], 'Save text as', self.saveTextToFile)
            if text:
                self.ui.textEdit.setPlainText(text)
            elif os.path.isfile(path):
                with open(path) as f:
                    self.ui.textEdit.setPlainText(f.read())
            else:
                with open(path, 'w') as f:
                    f.write('')
        self.menu.addSeparator()
        self.menu.addAction(self.icon["delete"], 'Delete', self.delete)

        # Apply settings and display children
        self.refreshWindowState(updateFrame=True)
        self.resize(self.profile.query("width"), self.profile.query("height"))
        if isNew or self.profile.query("pin") or not preferences.query("minimize"):
            self.display(updateState=False)

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

    def save(self):
        if self.windowTitle()[-1] == "*" or self.ui.titleLabel.text()[-1] == "*":
            self.setWindowTitle(self.windowTitle()[:-1])
            self.ui.titleLabel.setText(self.ui.titleLabel.text()[:-1])
        if not self.isImage:
            with open(self.path, 'w') as f:
                f.write(self.ui.textEdit.toPlainText())
        self.profile.load()
        self.profile.set("x", self.pos().x())
        self.profile.set("y", self.pos().y())
        self.profile.set("width", self.width())
        self.profile.set("height", self.height())
        self.profile.save()

    def delete(self):
        if os.path.isfile(self.path):
            logger.warning("Removed '" + self.name + "' (user)")
            if preferences.query("safeDelete") and os.stat(self.path).st_size > 0:
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
        if self.name in preferences.db["actives"]:
            preferences.db["actives"].remove(self.name)
            preferences.set("actives", preferences.db["actives"])

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

    def renameEvent(self, event=None):
        if event is None:
            self.ui.renameLabel.show()
            self.ui.line.show()
            self.ui.renameText.setText(self.name)
            self.ui.renameText.show()
            self.ui.renameText.setFocus()
            self.ui.renameText.selectAll()

        elif event.type() == QtCore.QEvent.FocusOut:
            self.ui.renameText.hide()
            self.ui.renameLabel.hide()
            self.ui.line.hide()

        elif event.type() == QtCore.QEvent.KeyPress:
            if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
                # Remove illegal characters
                name = self.ui.renameText.text()
                name = "".join(x for x in name if x.isalnum() or x is " ")
                if name and not name == self.name and name not in self.parent.children:
                    self.rename(name)
                # Trigger focusOutEvent
                self.ui.renameText.hide()
            else:
                QtWidgets.QLineEdit.keyPressEvent(self.ui.renameText, event)

    def rename(self, name):
        # Replace name in profiles database
        with open(PROFILES_FILE, "r+") as db:
            profiles = json.load(db)
            profiles[name] = profiles.pop(self.name)
            db.seek(0)
            db.truncate()
            db.write(json.dumps(profiles, indent=2, sort_keys=False))

        # Replace name in children list
        self.parent.children[name] = self.parent.children.pop(self.name)

        # Rename note file
        if os.path.isfile(self.path):
            if self.isImage:
                os.rename(self.path, DB_DIR + name + ".png")
                self.path = DB_DIR + name + ".png"
            else:
                os.rename(self.path, DB_DIR + name + ".txt")
                self.path = DB_DIR + name + ".txt"

        # Update child proprieties
        self.name = self.path.rsplit('/', 1)[-1].rsplit('.', 1)[0]
        self.profile.path = self.path
        self.profile.name = self.name
        self.setWindowTitle(name)

        # Update profile database
        self.profile.load()
        self.profile.parse()

    def setBackgroundColor(self, color):
        palette = self.ui.textEdit.viewport().palette()
        palette.setColor(QtGui.QPalette.Base, color)  # textEdit
        palette.setColor(QtGui.QPalette.Background, color)  # widget
        palette.setColor(QtGui.QPalette.Light, color)  # line
        self.ui.textEdit.viewport().setPalette(palette)
        self.ui.textEdit.viewport().update()
        self.setPalette(palette)
        self.update()

    def setFontColor(self, color):
        palette = self.ui.textEdit.viewport().palette()
        palette.setColor(QtGui.QPalette.Text, color)  # textEdit
        palette.setColor(QtGui.QPalette.WindowText, color)  # label
        palette.setColor(QtGui.QPalette.Dark, color)  # line
        self.ui.textEdit.viewport().setPalette(palette)
        self.ui.renameLabel.setPalette(palette)
        self.ui.line.setPalette(palette)

    def setStyle(self, background, fontColor, updateProfile):
        self.setBackgroundColor(QtGui.QColor(background))
        self.setFontColor(QtGui.QColor(fontColor))
        if updateProfile:
            self.profile.set("background", background)
            self.profile.set("fontColor", fontColor)
            self.profile.save()

    def loadStyle(self):
        font = self.ui.textEdit.font()
        font.setFamily(self.profile.query("fontFamily"))
        font.setPointSize(self.profile.query("fontSize"))
        self.ui.textEdit.setFont(font)
        self.setStyle(self.profile.query("background"), self.profile.query("fontColor"), updateProfile=False)
        logger.info("Loaded style for '" + self.name + "'")

    def refreshWindowState(self, updateFrame=False):
        # Handle window icon
        if self.profile.query("pin"):
            icon = self.icon["pin_title"]
        elif self.name in preferences.query("actives"):
            icon = self.icon["toggle"]
        else:
            icon = self.icon["tray"]
        self.ui.iconLabel.setPixmap(icon.pixmap(14, 14))
        self.setWindowIcon(icon)

        # Choose between native and custom frame
        if updateFrame:
            self.ui.titleLabel.setText(self.name)
            self.setWindowTitle(self.name)
            if preferences.query("frameless"):
                self.setWindowFlags(Qt.FramelessWindowHint)
                self.ui.closeButton.clicked.connect(self.close)
                with open(STYLESHEET_FILE) as f:
                    stylesheet = f.read()
                    self.ui.iconLabel.setStyleSheet(stylesheet)
                    self.ui.titleLabel.setStyleSheet(stylesheet)
                    self.ui.closeButton.setStyleSheet(stylesheet)
                self.ui.iconLabel.show()
                self.ui.titleLabel.show()
                self.ui.closeButton.show()
            else:
                self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
                self.ui.iconLabel.hide()
                self.ui.titleLabel.hide()
                self.ui.closeButton.hide()

        # Handle resize corner
        if self.profile.query("sizeGrip") or preferences.query("frameless"):
            self.sizeGrip.show()
        else:
            self.sizeGrip.hide()

        # Handle 'always on top'
        if self.profile.query("pin") or preferences.query("alwaysOnTop"):
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~ Qt.WindowStaysOnTopHint)
        logger.info("Updated window state for '" + self.name + "'")

    def closeEvent(self, event):
        if self.name:
            self.hide()
            logger.info("Closed '" + self.name + "'")
            event.ignore()

            # Remove empty notes
            if not self.isImage:
                if preferences.query("deleteEmptyNotes") and self.ui.textEdit.toPlainText() == "":
                    logger.warning("Removed '" + self.name + "' (empty)")
                    self.remove()

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
        clipboard.setPixmap(self.ui.imageLabel.pixmap())

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

    def keyPressEvent(self, event):
        if preferences.query("hotkeys"):
            isCtrlShift = int(event.modifiers()) == (Qt.ControlModifier + Qt.ShiftModifier)
            isCtrl = (event.modifiers() == Qt.ControlModifier)
            key = event.key()

            # Actions hotkeys
            if key == Qt.Key_H and isCtrl:
                self.hide()
            elif key == Qt.Key_P and isCtrl:
                self.pin()
            elif key == Qt.Key_R and isCtrl:
                self.renameEvent()
            elif key == Qt.Key_S and isCtrl:
                self.save()

            # Special actions hotkeys
            elif key == Qt.Key_R and isCtrlShift:
                if self.sizeGrip.isVisible():
                    self.sizeGrip.hide()
                    self.profile.save("sizeGrip", False)
                else:
                    self.sizeGrip.show()
                    self.profile.save("sizeGrip", True)

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
                cursor.movePosition(QtGui.QTextCursor.StartOfLine)
                cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.KeepAnchor)
                line = cursor.selectedText()

                # Duplicate line
                if key == Qt.Key_D:
                    cursor.insertText(line + "\n" + line)

                # Shift line up
                elif key == Qt.Key_Up:
                    cursor.removeSelectedText()
                    cursor.movePosition(QtGui.QTextCursor.Left, QtGui.QTextCursor.KeepAnchor)
                    newline = cursor.selectedText()
                    cursor.removeSelectedText()
                    cursor.movePosition(QtGui.QTextCursor.StartOfLine)
                    cursor.insertText(line + newline)
                    cursor.movePosition(QtGui.QTextCursor.Up)
                    cursor.movePosition(QtGui.QTextCursor.StartOfLine)

                # Shift line down
                elif key == Qt.Key_Down:
                    cursor.removeSelectedText()
                    cursor.movePosition(QtGui.QTextCursor.Right, QtGui.QTextCursor.KeepAnchor)
                    newline = cursor.selectedText()
                    cursor.removeSelectedText()
                    cursor.movePosition(QtGui.QTextCursor.EndOfLine)
                    cursor.insertText(newline + line)

                self.ui.textEdit.setTextCursor(cursor)
                self.ui.textEdit.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
                self.handleAsterisk()

            # Resize hotkeys
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

            # No valid hotkeys
            else:
                QtWidgets.QPlainTextEdit.keyPressEvent(self.ui.textEdit, event)
                self.handleAsterisk()

            # Apply settings, if any
            if 'size' in locals() and size > 0:
                font.setPointSize(size)
                self.ui.textEdit.setFont(font)
                self.profile.save("fontSize", size)
            if 'width' in locals() and width > 50:
                self.resize(width, self.height())
            if 'height' in locals() and height > 50:
                self.resize(self.width(), height)

        # No hotkeys
        else:
            QtWidgets.QPlainTextEdit.keyPressEvent(self.ui.textEdit, event)
            self.handleAsterisk()


LOG_LEVEL = logging.INFO
LOG_FORMAT_DATE = "%H:%M:%S"
LOG_FORMAT = "%(levelname)s\t[%(asctime)s] %(message)s"

PREFERENCES_DEFAULT = \
{
    'general':
    {
        'defaultNameTxt': 'Untitled',
        'defaultNameImg': 'Image',
        'leftClickAction': 'Toggle actives',
        'cmdLeft': '',
        'middleClickAction': 'Fetch clipboard or new note',
        'cmdMiddle': '',
        'startupAction': 'None',
        'cmdStartup': '',
        'minimize': True,
        'alwaysOnTop': True,
        'safeDelete': True,
        'hotkeys': True,
        'frameless': False,
        'deleteEmptyNotes': False,
        'fetchClear': True,
        'fetchUrl': True,
        'fetchFile': True,
        'fetchTxt': True,
        'fetchIcon': True,
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
        'fontColor': '#000000',
        'fontSize': 9,
        'fontFamily': 'Sans Serif',
    },

    'stylePreset':
    {
        'Black on yellow': {'background': '#ffff7f', 'fontColor': '#000000'},
        'Black on white': {'background': '#ffffff', 'fontColor': '#000000'},
        'White on black': {'background': '#2a2a2a', 'fontColor': '#ffffff'},
        'Low priority': {'background': '#c6efce', 'fontColor': '#004000'},
        'Mid priority': {'background': '#ffeb9c', 'fontColor': '#553400'},
        'High priority': {'background': '#ffc7ce', 'fontColor': '#9c0006'},
    },
    'actives': '',
}

STYLESHEET_DEFAULT = \
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

def main():
    # Verify if a bus already exist
    bus = QtDBus.QDBusInterface("org.qtpad.session", "/org/qtpad/session", "org.qtpad.session", QtDBus.QDBusConnection.sessionBus())
    if bus.isValid():
        if len(sys.argv) > 2:
            bus.call("parse", sys.argv[1], sys.argv[2])
        sys.exit(0)

    # Init logger
    global logger
    logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT, datefmt=LOG_FORMAT_DATE)
    logger = logging.getLogger()
    logger.info("Init of a new instance")
    if "qtpad.gui_child" in sys.modules and "qtpad.gui_profile" in sys.modules and "qtpad.gui_preferences" in sys.modules:
        logger.info("Found pre-compiled ui files")
    else:
        logger.warning("Some or all compiled ui files are missing")

    # Set paths
    global LOCAL_DIR, ICONS_DIR, PREFERENCES_FILE, PROFILES_FILE, DB_DIR, STYLESHEET_FILE
    LOCAL_DIR = os.path.dirname(os.path.realpath(__file__)) + '/'
    ICONS_DIR = LOCAL_DIR + 'icons/'
    CONFIG_DIR = os.path.expanduser("~/.config/qtpad/")
    PREFERENCES_FILE = CONFIG_DIR + "preferences.json"
    PROFILES_FILE = CONFIG_DIR + "profiles.json"
    STYLESHEET_FILE = CONFIG_DIR + "custom_frame.css"
    DB_DIR = CONFIG_DIR + "notes/"
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)

    # Set style
    if not os.path.isfile(STYLESHEET_FILE) or os.stat(STYLESHEET_FILE).st_size == 0:
        # Format python dict to CSS syntax
        stylesheet = ""
        for item in STYLESHEET_DEFAULT:
            stylesheet += item + "\n{\n"
            for attribute in STYLESHEET_DEFAULT[item]:
                stylesheet += "  " + attribute + ": " + STYLESHEET_DEFAULT[item][attribute] + ";\n"
            stylesheet += "}\n"
        with open(STYLESHEET_FILE, 'w') as f:
            f.write(stylesheet)

    # Init a Qt application
    global preferences, app, clipboard, daemon
    preferences = Preferences()
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    clipboard = app.clipboard()
    bus = QtDBus.QDBusConnection.sessionBus()
    server = QDBusServer()
    bus.registerObject('/org/qtpad/session', server)
    bus.registerService('org.qtpad.session')
    daemon = Mother()
    if len(sys.argv) > 2:
        daemon.parse(sys.argv[1], sys.argv[2])
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
