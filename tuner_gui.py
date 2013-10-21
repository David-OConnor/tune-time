# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'C:\Users\Dave\Desktop\Programming\tune_time\tune_time.ui'
#
# Created: Sun Oct 13 16:42:19 2013
#      by: PyQt5 UI code generator 5.0.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Main(object):
    def setupUi(self, Main):
        Main.setObjectName("Main")
        Main.resize(380, 600)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Main.sizePolicy().hasHeightForWidth())
        Main.setSizePolicy(sizePolicy)
        Main.setMinimumSize(QtCore.QSize(380, 600))
        Main.setMaximumSize(QtCore.QSize(380, 600))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/program icon/icon.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Main.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(Main)
        self.centralwidget.setObjectName("centralwidget")
        self.lbl_note = QtWidgets.QLabel(self.centralwidget)
        self.lbl_note.setGeometry(QtCore.QRect(164, 212, 61, 50))
        font = QtGui.QFont()
        font.setPointSize(22)
        self.lbl_note.setFont(font)
        self.lbl_note.setText("")
        self.lbl_note.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignHCenter)
        self.lbl_note.setObjectName("lbl_note")
        self.lbl_cents = QtWidgets.QLabel(self.centralwidget)
        self.lbl_cents.setGeometry(QtCore.QRect(90, 210, 61, 50))
        font = QtGui.QFont()
        font.setPointSize(16)
        self.lbl_cents.setFont(font)
        self.lbl_cents.setText("")
        self.lbl_cents.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignHCenter)
        self.lbl_cents.setObjectName("lbl_cents")
        self.lbl_freq = QtWidgets.QLabel(self.centralwidget)
        self.lbl_freq.setGeometry(QtCore.QRect(250, 210, 121, 50))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_freq.setFont(font)
        self.lbl_freq.setText("")
        self.lbl_freq.setAlignment(QtCore.Qt.AlignBottom|QtCore.Qt.AlignHCenter)
        self.lbl_freq.setObjectName("lbl_freq")
        self.btn_tuner = QtWidgets.QPushButton(self.centralwidget)
        self.btn_tuner.setGeometry(QtCore.QRect(10, 220, 70, 60))
        self.btn_tuner.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/metronome button/start.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.btn_tuner.setIcon(icon1)
        self.btn_tuner.setIconSize(QtCore.QSize(48, 48))
        self.btn_tuner.setCheckable(True)
        self.btn_tuner.setObjectName("btn_tuner")
        self.btn_metronome = QtWidgets.QPushButton(self.centralwidget)
        self.btn_metronome.setGeometry(QtCore.QRect(300, 339, 60, 70))
        self.btn_metronome.setText("")
        self.btn_metronome.setIcon(icon1)
        self.btn_metronome.setIconSize(QtCore.QSize(48, 48))
        self.btn_metronome.setCheckable(True)
        self.btn_metronome.setAutoDefault(False)
        self.btn_metronome.setDefault(False)
        self.btn_metronome.setFlat(False)
        self.btn_metronome.setObjectName("btn_metronome")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(310, 420, 50, 20))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.d_bpm = QtWidgets.QDial(self.centralwidget)
        self.d_bpm.setGeometry(QtCore.QRect(100, 340, 180, 180))
        self.d_bpm.setMinimum(40)
        self.d_bpm.setMaximum(240)
        self.d_bpm.setSingleStep(1)
        self.d_bpm.setSliderPosition(120)
        self.d_bpm.setOrientation(QtCore.Qt.Horizontal)
        self.d_bpm.setInvertedAppearance(False)
        self.d_bpm.setNotchTarget(3.7)
        self.d_bpm.setNotchesVisible(True)
        self.d_bpm.setObjectName("d_bpm")
        self.vs_volume = QtWidgets.QSlider(self.centralwidget)
        self.vs_volume.setGeometry(QtCore.QRect(0, 320, 71, 221))
        self.vs_volume.setMaximum(100)
        self.vs_volume.setProperty("value", 50)
        self.vs_volume.setOrientation(QtCore.Qt.Vertical)
        self.vs_volume.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        self.vs_volume.setTickInterval(10)
        self.vs_volume.setObjectName("vs_volume")
        self.sb_meter = QtWidgets.QSpinBox(self.centralwidget)
        self.sb_meter.setGeometry(QtCore.QRect(310, 510, 50, 30))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.sb_meter.setFont(font)
        self.sb_meter.setAlignment(QtCore.Qt.AlignCenter)
        self.sb_meter.setMinimum(1)
        self.sb_meter.setMaximum(8)
        self.sb_meter.setProperty("value", 1)
        self.sb_meter.setObjectName("sb_meter")
        self.lbl_tempo = QtWidgets.QLabel(self.centralwidget)
        self.lbl_tempo.setGeometry(QtCore.QRect(140, 520, 101, 41))
        self.lbl_tempo.setMouseTracking(True)
        self.lbl_tempo.setAutoFillBackground(False)
        self.lbl_tempo.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.lbl_tempo.setFrameShadow(QtWidgets.QFrame.Plain)
        self.lbl_tempo.setScaledContents(False)
        self.lbl_tempo.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_tempo.setObjectName("lbl_tempo")
        self.line = QtWidgets.QFrame(self.centralwidget)
        self.line.setGeometry(QtCore.QRect(10, 280, 361, 20))
        self.line.setLineWidth(1)
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.lbl_meter = QtWidgets.QLabel(self.centralwidget)
        self.lbl_meter.setGeometry(QtCore.QRect(310, 490, 50, 20))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.lbl_meter.setFont(font)
        self.lbl_meter.setAlignment(QtCore.Qt.AlignCenter)
        self.lbl_meter.setObjectName("lbl_meter")
        self.sb_bpm = QtWidgets.QSpinBox(self.centralwidget)
        self.sb_bpm.setGeometry(QtCore.QRect(310, 440, 50, 30))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.sb_bpm.setFont(font)
        self.sb_bpm.setMinimum(40)
        self.sb_bpm.setMaximum(240)
        self.sb_bpm.setProperty("value", 120)
        self.sb_bpm.setObjectName("sb_bpm")
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setGeometry(QtCore.QRect(89, 219, 271, 61))
        self.frame.setFrameShape(QtWidgets.QFrame.Box)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setLineWidth(1)
        self.frame.setMidLineWidth(0)
        self.frame.setObjectName("frame")
        Main.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(Main)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 380, 21))
        self.menubar.setObjectName("menubar")
        self.menuMenu = QtWidgets.QMenu(self.menubar)
        self.menuMenu.setObjectName("menuMenu")
        self.menuTick = QtWidgets.QMenu(self.menubar)
        self.menuTick.setObjectName("menuTick")
        self.menuAccent = QtWidgets.QMenu(self.menubar)
        self.menuAccent.setObjectName("menuAccent")
        self.menuSettings = QtWidgets.QMenu(self.menubar)
        self.menuSettings.setObjectName("menuSettings")
        Main.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(Main)
        self.statusbar.setObjectName("statusbar")
        Main.setStatusBar(self.statusbar)
        self.action_settings = QtWidgets.QAction(Main)
        self.action_settings.setObjectName("action_settings")
        self.action_about = QtWidgets.QAction(Main)
        self.action_about.setObjectName("action_about")
        self.action_hotkeys = QtWidgets.QAction(Main)
        self.action_hotkeys.setObjectName("action_hotkeys")
        self.action_save = QtWidgets.QAction(Main)
        self.action_save.setObjectName("action_save")
        self.action_visbeat = QtWidgets.QAction(Main)
        self.action_visbeat.setCheckable(True)
        self.action_visbeat.setObjectName("action_visbeat")
        self.action_nonstandard_tuning = QtWidgets.QAction(Main)
        self.action_nonstandard_tuning.setObjectName("action_nonstandard_tuning")
        self.menuMenu.addAction(self.action_save)
        self.menuMenu.addSeparator()
        self.menuMenu.addAction(self.action_hotkeys)
        self.menuMenu.addAction(self.action_about)
        self.menuSettings.addAction(self.action_nonstandard_tuning)
        self.menuSettings.addAction(self.action_visbeat)
        self.menubar.addAction(self.menuMenu.menuAction())
        self.menubar.addAction(self.menuSettings.menuAction())
        self.menubar.addAction(self.menuTick.menuAction())
        self.menubar.addAction(self.menuAccent.menuAction())

        self.retranslateUi(Main)
        QtCore.QMetaObject.connectSlotsByName(Main)

    def retranslateUi(self, Main):
        _translate = QtCore.QCoreApplication.translate
        Main.setWindowTitle(_translate("Main", "Tune Time v0.1"))
        self.btn_tuner.setShortcut(_translate("Main", "T"))
        self.btn_metronome.setShortcut(_translate("Main", "M"))
        self.label.setText(_translate("Main", "BPM"))
        self.lbl_tempo.setText(_translate("Main", "Allegro"))
        self.lbl_meter.setText(_translate("Main", "Meter"))
        self.menuMenu.setTitle(_translate("Main", "Menu"))
        self.menuTick.setTitle(_translate("Main", "Tick"))
        self.menuAccent.setTitle(_translate("Main", "Accent"))
        self.menuSettings.setTitle(_translate("Main", "Settings"))
        self.action_settings.setText(_translate("Main", "Settings"))
        self.action_about.setText(_translate("Main", "About"))
        self.action_hotkeys.setText(_translate("Main", "Hotkeys"))
        self.action_save.setText(_translate("Main", "Save (ctrl+s)"))
        self.action_visbeat.setText(_translate("Main", "Visual metronome beat"))
        self.action_nonstandard_tuning.setText(_translate("Main", "Nonstandard Tuning"))

import tuner_rc
