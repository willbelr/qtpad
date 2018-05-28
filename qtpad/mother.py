#!/usr/bin/python3
import time
import json
import os
import requests
import sys
from PyQt5 import QtGui, QtWidgets, QtCore, QtDBus, uic
from PyQt5.QtCore import Qt, QObject, QProcess, pyqtSlot

try:
    import qtpad.gui_search
    from qtpad.preferences import Preferences, PreferencesDialog
    from qtpad.child import Child
    from qtpad.common import *
except ImportError:
    from preferences import Preferences, PreferencesDialog
    from child import Child
    from common import *

# Init common settings
LOCAL_DIR, ICONS_DIR, PREFERENCES_FILE, PROFILES_FILE = getStaticPaths()
logger = getLogger()
logger.info("Init of a new instance")
if not "qtpad.common" in sys.modules:
    logger.warning("Could not load pre-compiled modules")


class Mother(object):
    def __init__(self, parent=None):
        self.clipboard = app.clipboard()
        self.preferences = Preferences()
        notesDir = self.preferences.query("general", "notesDb")
        configPath = os.path.expanduser("~/.config/qtpad")
        if not os.path.exists(notesDir):
            os.makedirs(notesDir)
        if not os.path.exists(configPath):
            os.makedirs(configPath)

        if self.preferences.query("general", "deleteEmptyNotes"):
            self.deleteEmptyNotes()
        self.children = {}
        self.load(notesDir)

        icons = ["tray", "quit", "file_active", "file_inactive", "new", "hide", "show", "reverse", "delete",
                  "preferences", "image", "toggle", "reset", "file_pinned", "file_image", "folder_active", "folder_inactive"]
        self.icon = {}
        for icon in icons:
            self.icon[icon] = QtGui.QIcon(ICONS_DIR + icon + ".svg")

        self.menu = QtWidgets.QMenu()
        self.menu.aboutToShow.connect(self.menuRefresh)
        self.trayIcon = QtWidgets.QSystemTrayIcon()
        self.trayIcon.activated.connect(self.clickEvent)

        self.lastActive = ""
        self.searchForm = SearchForm(self)

        # Handle svg to pixmap conversion (KDE compatibility)
        trayIcon = self.icon["tray"].pixmap(64, 64)
        trayIcon = QtGui.QIcon(trayIcon)
        self.trayIcon.setIcon(trayIcon)

        self.preferencesMenuIndex = 0
        self.menuRefresh()
        self.trayIcon.setContextMenu(self.menu)
        self.trayIcon.show()

        if self.preferences.query("actions", "startupAction"):
            action = self.preferences.query("actions", "startupAction")
            cmd = self.preferences.query("actions", "startupCmd")
            self.action(action, cmd)

    def parse(self, cmd, arg):
        if cmd == "-a" or cmd == "--action":
            logger.info("Call action '%s' from command" % cmd + " " + arg)
            self.action(arg)

    def listFolders(self, root):
        folders = []
        for folder in os.listdir(root):
            if os.path.isdir(root + folder):
                folders.append(folder)
        return sorted(folders, key=str.lower)

    def loadFolders(self):
        notesDir = self.preferences.query("general", "notesDb")
        dbFolders = self.preferences.db["folders"]
        osFolders = self.listFolders(notesDir)

        for folder in list(dbFolders):
            # Remove deleted folders from database
            if folder not in osFolders:
                logger.info("Deleted orphan database entry for folder '%s'" % folder)
                del self.preferences.db["folders"][folder]
                self.preferences.save()

        for folder in osFolders:
            # Create a preference entry for new folders
            if not folder in dbFolders:
                self.preferences.db["folders"][folder] = True
                self.preferences.save()

            # Load all notes from the folder
            if os.path.isdir(notesDir + folder):
                for f in os.listdir(notesDir + folder):
                    if dbFolders[folder]:
                        self.load(notesDir + folder)

    def unloadFolder(self, folder):
        for f in os.listdir(self.preferences.query("general", "notesDb") + folder):
            name = folder + "/" + f
            name = name.rsplit('.', 1)[0]
            if name in self.children:
                self.children[name].name = ""
                self.children[name].close()
                del self.children[name]
        logger.info("Unloaded folder '%s'" % folder)

    def deleteFolder(self, folder):
        folder = self.preferences.query("general", "notesDb") + folder
        if len(os.listdir(folder)) == 0:
            if os.path.isdir(folder):
                os.rmdir(folder)
                logger.warning("Removed empty folder '" + folder + "' (user)")
        else:
            msg = QtWidgets.QMessageBox()
            msg.setWindowFlags(msg.windowFlags() | Qt.WindowStaysOnTopHint)
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setWindowTitle("Delete confirmation")
            msg.setText("Please confirm deletion of folder\n" + folder)
            msg.setStandardButtons(QtWidgets.QMessageBox.Apply | QtWidgets.QMessageBox.Cancel)
            if msg.exec_() == QtWidgets.QMessageBox.Apply:
                for f in os.listdir(folder):
                    os.remove(folder + "/" + f)
                os.rmdir(folder)
                logger.warning("Removed folder '" + folder + "' (user)")
                self.cleanOrphans()

    def deleteEmptyNotes(self):
        notesDir = self.preferences.query("general", "notesDb")
        for f in os.listdir(notesDir):
            if os.path.isdir(notesDir + f):
                for note in os.listdir(notesDir + f):
                    if os.stat(notesDir + f + "/" + note).st_size == 0:
                        logger.warning("Removed '" + note + "' (empty)")
                        os.remove(notesDir + f + "/" + note)
            else:
                if os.stat(notesDir + f).st_size == 0:
                    logger.warning("Removed '" + f + "' (empty)")
                    os.remove(notesDir + f)

    def load(self, folder):
        notesDir = self.preferences.query("general", "notesDb")
        folder = folder[len(notesDir):]
        if folder:
            folder = folder + "/"

        # Create a new note if needed
        for f in os.listdir(notesDir + folder):
            name = folder + f.rsplit('.', 1)[0]
            if name not in self.children:
                path = notesDir + folder + f
                if f.endswith(".txt"):
                    self.children[name] = Child(self, path)
                elif f.endswith(".png"):
                    self.children[name] = Child(self, path, image=QtGui.QPixmap(f))
        self.cleanProfiles()

    def new(self, image=None, text=None):
        notesDir = self.preferences.query("general", "notesDb")
        if image:
            prefix = self.preferences.query("general", "nameImage")
        else:
            prefix = self.preferences.query("general", "nameText")

        name = getNameIndex(prefix, self.children)
        if image:
            self.children[name] = Child(self, notesDir + name + ".png", popup=True, image=image)
        else:
            self.children[name] = Child(self, notesDir + name + ".txt", popup=True, text=text)
        return name

    def pollFolderIcon(self, entry):
        if self.preferences.query("folders", entry):
            return self.icon["folder_active"]
        else:
            return self.icon["folder_inactive"]

    def toggleFolder(self, folder):
        self.preferences.db["folders"][folder] = not self.preferences.db["folders"][folder]
        self.preferences.save()
        if not self.preferences.db["folders"][folder]:
            self.unloadFolder(folder)
        self.loadFolders()

    def menuAddOption(self, option):
        option = option.lower()
        if option == "(separator)":
            self.menu.addSeparator()

        elif option == "new note":
            self.menu.addAction(self.icon["new"], 'New note', lambda: self.action("New note"))

        elif option == "toggle actives":
            self.menu.addAction(self.icon["toggle"], 'Toggle actives', lambda: self.action("Toggle actives"))

        elif option == "fetch clipboard":
            if self.preferences.query("general", "fetchIcon") and self.fetchClipboard():
                self.menu.addAction(self.icon["image"], 'Fetch clipboard', lambda: self.action("Fetch clipboard"))

        elif option == "hide all":
            self.menu.addAction(self.icon["hide"], 'Hide all', lambda: self.action("Hide all"))

        elif option == "show all":
            self.menu.addAction(self.icon["show"], 'Show all', lambda: self.action("Show all"))

        elif option == "reverse all":
            self.menu.addAction(self.icon["reverse"], 'Reverse all', lambda: self.action("Reverse all"))

        elif option == "reset positions":
            self.menu.addAction(self.icon["reset"], 'Reset positions', lambda: self.action("Reset positions"))

        elif option == "folders list":
            # List all folders in notes directory
            notesDir = self.preferences.query("general", "notesDb")
            folders = self.listFolders(notesDir)
            for folder in folders:
                count = len(os.listdir(notesDir + folder))
                name = folder + " (" + str(count) + ")"
                self.menu.addAction(self.pollFolderIcon(folder), name, lambda folder=folder: self.toggleFolder(folder))

        elif option == "delete folders":
            # Make a dynamic menu to remove folders
            notesDir = self.preferences.query("general", "notesDb")
            folders = self.listFolders(notesDir)
            if folders:
                self.deleteFolderMenu = QtWidgets.QMenu("Delete folder...")
                self.deleteFolderMenu.setIcon(self.icon["delete"])
                for folder in folders:
                    self.deleteFolderMenu.addAction(self.icon["quit"], folder, lambda folder=folder: self.deleteFolder(folder))
                self.menu.addMenu(self.deleteFolderMenu)

        elif option == "notes list":
            noteList = []
            # Sort children list, add notes without folder first
            for name in sorted(self.children, key=str.lower):
                if name.count("/") == 0:
                    noteList.append(name)

            for name in sorted(self.children, key=str.lower):
                if name.count("/") > 0:
                    noteList.append(name)

            # Define the appropriate icon and display the list
            for name in noteList:
                if self.children[name].profile.query("pin"):
                    icon = self.icon["file_pinned"]
                elif name in self.preferences.query("actives"):
                    icon = self.icon["file_active"]
                elif self.children[name].isImage:
                    icon = self.icon["file_image"]
                else:
                    icon = self.icon["file_inactive"]
                self.menu.addAction(icon, self.children[name].name, self.children[name].display)

        elif option == "preferences":
            self.menu.addAction(self.icon["preferences"], "Preferences", lambda: PreferencesDialog(self))

        elif option == "quit":
            self.menu.addAction(self.icon["quit"], 'Quit', app.exit)

        else:
            logger.error("Invalid main menu option '%s'" % option)

    def menuRefresh(self):
        # Monitor changes in the database directory
        self.load(self.preferences.query("general", "notesDb"))
        self.loadFolders()
        self.cleanOrphans()

        # Generate dynamic menu
        self.menu.clear()
        for option in self.preferences.query("menus", "mother"):
            self.menuAddOption(option)

    def action(self, action, cmd=None):
        action = action.lower()
        if action == "new note":
            self.new()

        elif action == "fetch clipboard":
            fetch = self.fetchClipboard(newNote=True)

        elif action == "fetch clipboard or new note":
            fetch = self.fetchClipboard(newNote=True)
            if not fetch:
                self.new()

        elif action == "toggle actives":
            actives = []
            for name in self.children:
                children = self.children[name]
                if children.profile.query("pin"):
                    children.activateWindow()
                elif children.isVisible():
                    actives.append(children.name)

            if actives:
                self.preferences.set("actives", actives)
                self.action("hide all")
            elif self.preferences.query("actives"):
                for note in self.preferences.query("actives"):
                    if note in self.children:
                        self.children[note].display()

        elif action == "hide all":
            for name in list(self.children):
                children = self.children[name]
                if children.isVisible() and not children.profile.query("pin"):
                    children.close()

        elif action == "show all":
            for name in self.children:
                if not self.children[name].isVisible():
                    self.children[name].display()

        elif action == "reverse all":
            for name in list(self.children):
                children = self.children[name]
                if children.isVisible():
                    if not children.profile.query("pin"):
                        children.close()
                else:
                    children.display()

        elif action == "reset positions":
            # Remove orhans and unassigned profiles
            self.cleanOrphans()
            self.cleanProfiles()

            # Reset position
            n = 0
            _x = QtWidgets.QDesktopWidget().screenGeometry().width() - self.preferences.query("styleDefault", "width")
            _y = self.preferences.query("styleDefault", "height") / 2
            width = self.preferences.query("styleDefault", "width")
            height = self.preferences.query("styleDefault", "height")
            for name in self.children:
                children = self.children[name]
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

        elif action == "exec":
            if cmd:
                logger.info("Starting '%s'", cmd)
                slave = QProcess()
                slave.startDetached(cmd)

    def fetchClipboard(self, newNote=False):
        pixmap = self.clipboard.pixmap()
        path = self.clipboard.text().rstrip()
        textContent = None
        if pixmap.isNull():
            if os.path.isfile(path) and os.stat(path).st_size > 0:
                allowed = ["txt", "gif", "png", "bmp", "jpg", "jpeg", "svg"]
                ext = path.lower().rsplit('.', 1)[-1]
                if ext in allowed:
                    if self.preferences.query("general", "fetchTxt") and ext == "txt":
                        with open(path) as f:
                            textContent = f.read()
                    elif self.preferences.query("general", "fetchFile"):
                        pixmap = QtGui.QPixmap(path)

            elif self.preferences.query("general", "fetchUrl") and (path.startswith("http://") or path.startswith("https://") or path.startswith("www.")):
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

                if self.preferences.query("general", "fetchClear"):
                    self.clipboard.setText("")
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
            notesDir = self.preferences.query("general", "notesDb")
            with open(PROFILES_FILE, "r+") as db:
                profiles = json.load(db)
                for entry in list(profiles):
                    txtPath = notesDir + entry + ".txt"
                    pngPath = notesDir + entry + ".png"
                    if not os.path.isfile(pngPath) and (not os.path.isfile(txtPath) or os.stat(txtPath).st_size < 0):
                        del profiles[entry]
                db.seek(0)
                db.truncate()
                db.write(json.dumps(profiles, indent=2, sort_keys=False))

    def clickEvent(self, event):
        if event == QtWidgets.QSystemTrayIcon.Trigger:
            action = self.preferences.query("actions", "leftAction")
            cmd = self.preferences.query("actions", "leftCmd")
            self.action(action, cmd)

        elif event == QtWidgets.QSystemTrayIcon.MiddleClick:
            action = self.preferences.query("actions", "middleAction")
            cmd = self.preferences.query("actions", "middleCmd")
            self.action(action, cmd)


class SearchForm(QtWidgets.QWidget):
    def __init__(self, parent):
        super().__init__()

        # Load the ui file in case the gui modules are not loaded
        if "qtpad.gui_search" in sys.modules:
            self.ui = qtpad.gui_search.Ui_Form()
            self.ui.setupUi(self)
        else:
            self.ui = uic.loadUi(LOCAL_DIR + 'gui_search.ui', self)

        self.parent = parent
        self.active = None
        self.setFixedSize(490, 100)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.ui.installEventFilter(self)
        self.ui.searchFindButton.clicked.connect(self.find)
        self.ui.searchFindAllButton.clicked.connect(self.findAll)
        self.ui.searchReplaceButton.clicked.connect(self.replace)
        self.ui.searchReplaceAllButton.clicked.connect(self.replaceAll)

    def updateActive(self):
        for name in self.parent.children:
            child = self.parent.children[name]
            if child.isVisible() and not child.isImage:
                return child
        return None

    def updateTitle(self):
        # Fallback to another opened note if last active is deleted or closed
        if not self.parent.lastActive.name:
            self.active = self.updateActive()
        elif not self.parent.lastActive.isVisible():
            self.active = self.updateActive()
        else:
            self.active = self.parent.lastActive

        # Hide orphan search form
        if self.active is None:
            self.hide()
        else:
            self.setWindowTitle("Search in '%s'" % self.active.name)

    def eventFilter(self, object, event):
        eventType = event.type()
        if eventType == QtCore.QEvent.Show:
            self.updateTitle()
            self.ui.searchFindLine.setText(self.active.ui.textEdit.textCursor().selectedText())
        elif eventType == QtCore.QEvent.FocusIn or eventType == QtCore.QEvent.Enter:
            self.updateTitle()
        return QtCore.QObject.event(object, event)

    def getFlag(self):
        flag = QtGui.QTextDocument.FindFlags(0)
        if self.ui.searchCaseBox.isChecked():
            flag = flag | QtGui.QTextDocument.FindCaseSensitively
        if self.ui.searchWholeBox.isChecked():
            flag = flag | QtGui.QTextDocument.FindWholeWords
        return flag

    def find(self):
        next = self.active.ui.textEdit.find(self.ui.searchFindLine.text(), self.getFlag())
        if not next and self.ui.searchWrapBox.isChecked():
            self.active.ui.textEdit.moveCursor(QtGui.QTextCursor.Start)
            self.active.ui.textEdit.find(self.ui.searchFindLine.text(), self.getFlag())

    def replace(self):
        find = self.ui.searchFindLine.text()
        replace = self.ui.searchReplaceLine.text()
        cursor = self.active.ui.textEdit.textCursor()
        if find.lower() == cursor.selectedText().lower():
            cursor.insertText(replace)
            self.active.save()
        self.find()

    def findAll(self, find=""):
        # Allow override or searched text
        if not find:
            find = self.ui.searchFindLine.text()

        # Remove previous underlines
        extraSelections = self.active.ui.textEdit.extraSelections()
        for extra in extraSelections:
            extra.format.setFontUnderline(False)

        # Underline all results
        self.active.ui.textEdit.moveCursor(QtGui.QTextCursor.Start)
        while self.active.ui.textEdit.find(find, self.getFlag()):
            extra = QtWidgets.QTextEdit.ExtraSelection()
            extra.cursor = self.active.ui.textEdit.textCursor()
            extra.format.setFontUnderline(True)
            extraSelections.append(extra)

        # Apply result and clear selection
        self.active.ui.textEdit.setExtraSelections(extraSelections)
        self.active.ui.textEdit.moveCursor(QtGui.QTextCursor.Start)

    def replaceAll(self):
        find = self.ui.searchFindLine.text()
        replace = self.ui.searchReplaceLine.text()
        extraSelections = self.active.ui.textEdit.extraSelections()
        cursor = self.active.ui.textEdit.textCursor()

        self.active.ui.textEdit.moveCursor(QtGui.QTextCursor.Start)
        while self.active.ui.textEdit.find(find, self.getFlag()):
            extra = QtWidgets.QTextEdit.ExtraSelection()
            extra.cursor = self.active.ui.textEdit.textCursor()
            end = extra.cursor.position()
            start = end - len(find)
            cursor.setPosition(start)
            cursor.setPosition(end, QtGui.QTextCursor.KeepAnchor)
            cursor.insertText(replace)
            extraSelections.append(extra)
        self.active.ui.textEdit.setExtraSelections(extraSelections)
        self.active.ui.textEdit.moveCursor(QtGui.QTextCursor.Start)
        self.findAll(replace)  # Underline replaced text
        self.active.save()


class QDBusServer(QObject):
    def __init__(self):
        QObject.__init__(self)
        self.__dbusAdaptor = QDBusServerAdapter(self)


class QDBusServerAdapter(QtDBus.QDBusAbstractAdaptor):
    QtCore.Q_CLASSINFO("D-Bus Interface", "org.qtpad.session")
    QtCore.Q_CLASSINFO("D-Bus Introspection",
    '  <interface name="org.qtpad.session">\n'
    '    <method name="parse">\n'
    '      <arg direction="in" type="ss" name="cmd"/>\n'
    '    </method>\n'
    '  </interface>\n')

    def __init__(self, parent):
        super().__init__(parent)

    @pyqtSlot(str, str, result=str)
    def parse(self, cmd, arg):
        mother.parse(cmd, arg)


def main(cmd=None, arg=None):
    global app, mother
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    bus = QtDBus.QDBusConnection.sessionBus()
    server = QDBusServer()
    bus.registerObject('/org/qtpad/session', server)
    bus.registerService('org.qtpad.session')
    mother = Mother()

    # Handle init command (if any)
    if cmd and arg:
        mother.parse(cmd, arg)
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
