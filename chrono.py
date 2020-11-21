import sys
import os
from datetime import time, datetime, timedelta

from PySide2.QtCore import QTimer, Qt, QTime, QUrl
from PySide2.QtGui import QIcon
from PySide2.QtMultimedia import QMediaPlayer, QMediaContent
from PySide2.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMessageBox,
                               QProgressBar, QPushButton, QVBoxLayout, QWidget, QMainWindow, QMenuBar, QStatusBar,
                               QStyle, QDialog, QSpinBox, QGroupBox, QCheckBox, QAction, QTimeEdit, QSystemTrayIcon,
                               QMenu)

TITLE = "Chrono"
VERSION = 1.0
AUTHOR = "Almazys"


class Chrono(QMainWindow):
    def __init__(self, parent=None):
        super(Chrono, self).__init__(parent)

        self.createMenus()
        self.createSystemTrayIcon()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.isRunning = False

        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)
        self.hours = self.minutes = self.seconds = 0

        self.label = QLabel(" ")
        self.button = QPushButton()
        self.button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

        bottomLayout = QHBoxLayout()
        bottomLayout.addWidget(self.progressBar)
        bottomLayout.addWidget(self.button)
        self.button.clicked.connect(self.pause)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.label)
        mainLayout.addLayout(bottomLayout)
        centralWidget = QWidget()
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)

        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)

        self.notification = self.notification_popup = self.notification_tray = self.notification_sound = True
        self.notification_soundfile = os.path.dirname(sys.argv[0]) + '/notification.mp3' # os.path.dirname(__file__) + 

        self.setWindowTitle(TITLE)
        self.resize(400, self.sizeHint().height())
        self.setFixedHeight(self.sizeHint().height())

    def createMenus(self):
        menus = QMenuBar()
        fileMenu = menus.addMenu("&Fichier")
        file_newMenu = fileMenu.addMenu(self.style().standardIcon(QStyle.SP_FileIcon), "Nouveau")
        file_newMenu.addAction("Date", self.createDateDialog, 'CTRL+D')
        file_newMenu.addAction("Durée", self.createDurationDialog, 'CTRL+N')
        fileMenu.addSeparator()
        fileMenu.addAction(self.style().standardIcon(QStyle.SP_BrowserStop), "Quitter", sys.exit, 'CTRL+Q')

        optionMenu = menus.addMenu("&Options")
        optionMenu.addAction(self.style().standardIcon(QStyle.SP_MessageBoxInformation), "Évènements",
                             self.createNotificationPopup, 'CTRL+O')
        optionMenu.addAction(QAction("Rester au premier plan", optionMenu, triggered=self.stayOnTop, checkable=True))
        aideMenu = menus.addMenu("&Aide")
        aideMenu.addAction(self.style().standardIcon(QStyle.SP_DialogHelpButton), "À propos",
                           lambda: QMessageBox.information(self, "À propos",
                                                           TITLE + " " + str(
                                                               VERSION)), 'CTRL+H')
        aideMenu.addSeparator()
        aideMenu.addAction(self.style().standardIcon(QStyle.SP_TitleBarMenuButton), "À propos de Qt",
                           QApplication.aboutQt, 'CTRL+A')

        self.setMenuBar(menus)

    def createSystemTrayIcon(self):
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon(os.path.dirname(sys.argv[0]) + '/icon.svg')) # os.path.dirname(__file__) + 
        self.tray.setToolTip(TITLE)
        self.tray.show()

        systemTrayMenu = QMenu()
        pauseAction = QAction(self.style().standardIcon(QStyle.SP_MediaPause), "Pause / Reprendre", systemTrayMenu)
        pauseAction.triggered.connect(self.pause)

        systemTrayMenu.addAction(pauseAction)

        systemTrayMenu.addSeparator()
        systemTrayMenu.addAction(self.style().standardIcon(QStyle.SP_BrowserStop), "Quitter", sys.exit)
        self.tray.setContextMenu(systemTrayMenu)
        self.tray.activated.connect(self.show)

    def stayOnTop(self):
        self.setWindowFlags(self.windowFlags() ^ Qt.WindowStaysOnTopHint)
        #self.windowFlags() | Qt.CustomizeWindowHint | Qt.Window | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)  # Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.show()

    def createNotificationPopup(self):
        popup = QDialog(self)
        popup.setFixedSize(popup.sizeHint().height(), popup.sizeHint().width())
        popup.setWindowTitle("Évènements")
        innerLayout = QVBoxLayout()

        GroupBox = QGroupBox("Activer les notifications")
        GroupBox.setCheckable(True)
        GroupBox.setChecked(self.notification)

        checkBox_popup = QCheckBox("Afficher une popup")
        checkBox_notification = QCheckBox("Afficher une notification")
        checkBox_sound = QCheckBox("Jouer un son")

        if self.notification_popup:
            checkBox_popup.setCheckState(Qt.Checked)
        if self.notification_tray:
            checkBox_notification.setCheckState(Qt.Checked)
        if self.notification_sound:
            checkBox_sound.setCheckState(Qt.Checked)

        innerLayout.addWidget(checkBox_popup)
        innerLayout.addWidget(checkBox_notification)
        innerLayout.addWidget(checkBox_sound)
        innerLayout.addStretch(1)
        GroupBox.setLayout(innerLayout)

        button = QPushButton("Ok")
        button.clicked.connect(
            lambda: self.changeNotificationSettings(popup, GroupBox, checkBox_popup, checkBox_notification, checkBox_sound)
        )

        outerLayout = QVBoxLayout()
        outerLayout.addWidget(GroupBox)
        outerLayout.addWidget(button)
        popup.setLayout(outerLayout)

        popup.exec_()

    def changeNotificationSettings(self, popup, GroupBox, checkBox_popup, checkBox_notification, checkBox_sound):
        self.notification, self.notification_popup, self.notification_tray, self.notification_sound = GroupBox.isChecked(), checkBox_popup.isChecked(), checkBox_notification.isChecked(), checkBox_sound.isChecked()
        if not any([self.notification_popup, self.notification_tray, self.notification_sound]):
            self.notification = False
        popup.close()

    def createDateDialog(self):
        popup = QDialog(self)
        popup.setFixedSize(270, 60)
        popup.setWindowTitle("Nouvelle date")
        layout = QHBoxLayout()

        prefix = QLabel("Heure cible: ")
        layout.addWidget(prefix)

        qline = QTimeEdit()
        qline.setDisplayFormat("hh:mm:ss")
        qline.setTime(QTime.currentTime())
        layout.addWidget(qline)

        button = QPushButton("Ok")
        button.clicked.connect(
            lambda: self.createDate(popup, qline.time().hour(), qline.time().minute(), qline.time().second())
        )

        layout.addWidget(button)

        popup.setLayout(layout)
        popup.exec_()

    def createDurationDialog(self):
        popup = QDialog(self)
        popup.setFixedSize(150, 150)
        popup.setWindowTitle("Nouvelle durée")
        layout = QVBoxLayout()

        hourLayout = QHBoxLayout()
        hourLabel = QLabel("Heures:")
        hourSpin = QSpinBox()
        hourLayout.addWidget(hourLabel)
        hourLayout.addWidget(hourSpin)

        minuteLayout = QHBoxLayout()
        minuteLabel = QLabel("Minutes:")
        minuteSpin = QSpinBox()
        minuteLayout.addWidget(minuteLabel)
        minuteLayout.addWidget(minuteSpin)

        secondLayout = QHBoxLayout()
        secondLabel = QLabel("Secondes:")
        secondSpin = QSpinBox()
        secondLayout.addWidget(secondLabel)
        secondLayout.addWidget(secondSpin)

        layout.addLayout(hourLayout)
        layout.addLayout(minuteLayout)
        layout.addLayout(secondLayout)

        button = QPushButton("Ok")
        button.clicked.connect(
            lambda: self.createDuration(popup, hourSpin.value(), minuteSpin.value(), secondSpin.value()))
        layout.addWidget(button)

        popup.setLayout(layout)
        popup.exec_()

    def createDuration(self, popup: QDialog, hours: int, minutes: int, seconds: int):
        popup.close()
        self.hours, self.minutes, self.seconds = hours, minutes, seconds
        self.progressBar.setRange(0, seconds + minutes * 60 + hours * 3600)
        self.progressBar.setValue(0)
        self.label.setText(f'{self.hours:02}:{self.minutes:02}:{self.seconds:02}')

        self.isRunning = True
        self.timer.stop()
        self.timer.start(1000)

    def createDate(self, popup: QDialog, hours: int, minutes: int, seconds: int):
        popup.close()

        now = datetime.now().time()
        target = time(hours, minutes, seconds)
        now_delta = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
        target_delta = timedelta(hours=target.hour, minutes=target.minute, seconds=target.second)
        d = target_delta - now_delta

        _ = [d.total_seconds() if d.total_seconds() > 0 else d.total_seconds() + 24 * 60 * 60][0]

        self.progressBar.setRange(0, _)

        self.hours = int(_ / 3600)
        _ -= self.hours * 3600
        self.minutes = int(_ / 60)
        _ -= self.minutes * 60
        self.seconds = int(_)

        self.progressBar.setValue(0)
        self.label.setText(f'{self.hours:02}:{self.minutes:02}:{self.seconds:02}')

        self.isRunning = True
        self.timer.stop()
        self.timer.start(1000)

    def tick(self):
        self.progressBar.setValue(self.progressBar.value() + 1)

        if self.seconds:
            self.seconds -= 1
        elif self.minutes:
            self.seconds = 59
            self.minutes -= 1
        elif self.hours:
            self.seconds = self.minutes = 59
            self.hours -= 1

        self.label.setText(f'{self.hours:02}:{self.minutes:02}:{self.seconds:02}')
        self.setWindowTitle(f'{self.hours:02}:{self.minutes:02}:{self.seconds:02} - {TITLE}')
        self.tray.setToolTip(f'{self.hours:02}:{self.minutes:02}:{self.seconds:02}')

        if self.progressBar.value() == self.progressBar.maximum():
            self.isRunning = False
            self.timer.stop()
            self.progressBar.setRange(0, 0)
            self.show()
            self.notify()

    def notify(self):
        if not self.notification:
            return
        if self.notification_tray:
            self.tray.showMessage("Finished", "Le décompte est terminé", self.style().standardIcon(QStyle.SP_MessageBoxInformation))
        if self.notification_sound:
            test = QMediaPlayer()
            test.setMedia(QUrl.fromLocalFile(self.notification_soundfile))
            test.play()
        if self.notification_popup:
            QMessageBox.information(self, "Finished", "Le décompte est terminé")

    def pause(self):
        if not self.isRunning:
            return
        self.progressBar.setDisabled(self.timer.isActive())
        if self.timer.isActive():
            self.statusBar.showMessage("Pause")
            self.tray.setToolTip(self.tray.toolTip() + ' - Pause')
            self.timer.stop()
            self.button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        else:
            self.statusBar.clearMessage()
            self.timer.start()
            self.button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))

    # Override
    def closeEvent(self, event):
        self.hide()
        event.ignore()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    chrono = Chrono()
    chrono.show()
    sys.exit(app.exec_())
