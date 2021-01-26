import sys
import os
from datetime import time, datetime, timedelta
from math import ceil

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
        self.refresh_rate = 100  # ms

        self.progressBar = QProgressBar()
        self.progressBar.setValue(0)
        self.begin_time = self.end_time = 0

        self.label = QLabel(" ")
        self.button = QPushButton()
        self.button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.end_delay = self.begin_delay = 0

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
        self.notification_soundfile = os.path.dirname(sys.argv[0]) + '/notification.mp3'  # os.path.dirname(__file__) +

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
        self.tray.setIcon(QIcon(os.path.dirname(sys.argv[0]) + '/icon.svg'))  # os.path.dirname(__file__) +
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
        # self.windowFlags() | Qt.CustomizeWindowHint | Qt.Window | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)  # Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
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
            lambda: self.changeNotificationSettings(popup, GroupBox, checkBox_popup, checkBox_notification,
                                                    checkBox_sound)
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

        self.begin_time = datetime.timestamp(datetime.now())
        self.end_time = self.begin_time + seconds + minutes * 60 + hours * 3600
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)

        self.isRunning = True
        self.timer.stop()
        self.timer.start(self.refresh_rate)

    def createDate(self, popup: QDialog, hours: int, minutes: int, seconds: int):
        popup.close()

        self.begin_time = datetime.timestamp(datetime.now())

        now = datetime.now().time()
        target = time(hours, minutes, seconds)
        now_delta = timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)
        target_delta = timedelta(hours=target.hour, minutes=target.minute, seconds=target.second)

        if target_delta == now_delta:
            self.end_time = self.begin_time + 60 * 60 * 24
        else:
            d = target_delta - now_delta
            self.end_time = self.begin_time + d.seconds

        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)

        self.isRunning = True
        self.timer.stop()
        self.timer.start(self.refresh_rate)

    def tick(self):
        self.progressBar.setValue(
            100 * (datetime.timestamp(datetime.now()) - self.begin_time) / (self.end_time - self.begin_time))

        seconds = int(ceil(self.end_time - datetime.timestamp(datetime.now())) % 60)
        minutes = int(ceil(self.end_time - datetime.timestamp(datetime.now())) / 60 % 60)
        hours = int(ceil(self.end_time - datetime.timestamp(datetime.now())) / 3600)

        self.label.setText(f'{hours:02}:{minutes:02}:{seconds:02}')
        self.setWindowTitle(f'{TITLE} - {hours:02}:{minutes:02}:{seconds:02}')
        self.tray.setToolTip(f'{hours:02}:{minutes:02}:{seconds:02}')

        if datetime.timestamp(datetime.now()) >= self.end_time:
            self.isRunning = False
            self.timer.stop()
            self.progressBar.setRange(0, 0)
            self.show()
            self.notify()

    def notify(self):
        if not self.notification:
            return
        if self.notification_tray:
            self.tray.showMessage("Finished", "Le décompte est terminé",
                                  self.style().standardIcon(QStyle.SP_MessageBoxInformation))
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
            self.end_delay = self.end_time - datetime.timestamp(datetime.now())
            self.begin_delay = datetime.timestamp(datetime.now()) - self.begin_time
            print(self.begin_time)
            print(self.end_time)
            print(self.end_delay)
            self.statusBar.showMessage("Pause")
            self.tray.setToolTip(self.tray.toolTip() + ' - Pause')
            self.timer.stop()
            self.button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        else:
            self.begin_time = datetime.timestamp(datetime.now()) - self.begin_delay
            self.end_time = datetime.timestamp(datetime.now()) + self.end_delay
            print(self.begin_time)
            print(self.end_time)
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
