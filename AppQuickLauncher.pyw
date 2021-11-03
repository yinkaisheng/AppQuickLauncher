#!python3
# -*- coding: utf-8 -*-
# author: yinkaisheng@foxmail.com
import os
import sys
import time
import json
import ctypes
from PyQt5.QtCore import QObject, Qt
from PyQt5.QtGui import QCloseEvent, QCursor, QIcon, QKeyEvent, QPixmap
from PyQt5.QtWidgets import (QAction, QApplication, QDialog, QMenu, QMessageBox, QSystemTrayIcon)
from PyQt5.QtWinExtras import QtWin

ExePath = os.path.abspath(sys.argv[0])
ExeDir, ExeName = os.path.split(ExePath)
ExeNameNoExt = ExeName.split('.')[0]


class TrayDlg(QDialog):
    def __init__(self, parent: QObject = None):
        super(TrayDlg, self).__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.setWindowTitle(ExeNameNoExt)
        self.resize(400, 300)
        self.configPath = os.path.join(ExeDir, os.path.splitext(ExeName)[0] + '.config')
        with open(self.configPath, 'rt', encoding='utf-8', errors='ignore') as fin:
            self.configJson = json.loads(fin.read())
        self.createUI()

    def createUI(self) -> None:
        icon = QIcon(f'{ExeNameNoExt}.ico')
        self.setWindowIcon(icon)
        self.actions = []
        self.trayIconMenu = QMenu(self)
        for app in self.configJson['appList']:
            hicon = ctypes.windll.shell32.ExtractIconW(0, app['exe'], app.get('icon', 0))
            qpixmp = QtWin.fromHICON(hicon)  # qpixmp.save('exe.ico')
            ctypes.windll.user32.DestroyIcon(ctypes.c_void_p(hicon))
            qico = QIcon()
            qico.addPixmap(qpixmp)
            action = QAction(qico, app['name'], self, triggered=self.onLaunchAppAction)
            self.actions.append(action)
            self.trayIconMenu.addAction(action)
        self.quitAction = QAction('Quit', self, triggered=QApplication.instance().quit)
        self.trayIconMenu.addSeparator()
        self.trayIconMenu.addAction(self.quitAction)
        self.trayIconMenu.keyPressEvent = self.MenuKeyPressEvent
        self.trayIcon = QSystemTrayIcon(self)
        self.trayIcon.setIcon(icon)
        self.trayIcon.setContextMenu(self.trayIconMenu)
        self.trayIcon.activated.connect(self.showTrayMenu)
        self.trayIcon.show()

    def MenuKeyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        if key == Qt.Key_Space:
            action = self.trayIconMenu.activeAction()
            if action:
                action.trigger()
                self.trayIconMenu.hide()
        QMenu.keyPressEvent(self.trayIconMenu, event)

    def showTrayMenu(self) -> None:
        self.trayIconMenu.exec_(QCursor.pos())

    def onLaunchAppAction(self) -> None:
        action = self.sender()
        index = self.actions.index(action)
        app = self.configJson['appList'][index]
        print('onLaunchAppAction', index, app['name'])
        exePath = app['exe']
        exeArgv = app.get('argv', '')
        exeWorkDir = app.get('dir', '')
        if not exeWorkDir:
            exeWorkDir = os.path.split(exePath)[0]
        print(f'dir:{exeWorkDir}, {exePath} {exeArgv}')
        ctypes.windll.shell32.ShellExecuteW(None, "", exePath, exeArgv, exeWorkDir, 1)

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
        self.hide()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "SysTray", "I couldn't detect any system tray on this system.")
        sys.exit(1)
    QApplication.setQuitOnLastWindowClosed(False)
    window = TrayDlg()
    sys.exit(app.exec_())
