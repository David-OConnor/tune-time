# Tune Time - Chromatic instrument tuner and metronome
# Copyright (C) <2013>  <David O'Connor>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import functools
import json
import math
import os
import sys
import time

from PyQt5 import QtCore, QtGui, QtWidgets, QtSvg

import metronome
import tuner
from tuner_gui import Ui_Main
from about_gui import Ui_About
#from settings_gui import Ui_Settings
from hotkeys_gui import Ui_Hotkeys
import module_locator
 
DIR = module_locator.path()

#to-do:
#Glitch with visbeat: Sometimes the off marker will remain visible after disabling visbeat. Usually during high-temp playback.
#visualization
#improve tuner algorithm
# Support for a second, (lighter, or customizable?) accent
#Use images/tooltips instead of text
#log scale on tuner image
#make whole window scalable, including tuning dislay widget size.
#have the tuner needle fade out when there's no signal after a time.
#better metronome vis: Make a line that bounces back and forth like a real metronome.
#Add setting for min/max bpm
#Possibly have metronome volume/instrument etc only update when changed, instead of at each beat. Changed flag check only?
#Add a notification on screen whenever in nonstandard tuning.
     
class Main(QtWidgets.QMainWindow):
    start_icon = QtGui.QIcon()
    stop_icon = QtGui.QIcon()
    
    tickitems = []
    accentitems = []
    visbeatOnSignal = QtCore.pyqtSignal()
    visbeatOffSignal = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = Ui_Main()
        self.ui.setupUi(self)
        
        self.ui.action_save.triggered.connect(self.save)
        self.ui.action_about.triggered.connect(self.about)
        #self.ui.action_settings.triggered.connect(self.settings)
        self.ui.action_visbeat.triggered.connect(self.visbeat_enable) ###check what the signal name is
        self.ui.action_hotkeys.triggered.connect(self.hotkeys)
        self.ui.btn_tuner.clicked.connect(self.start_tuner)
        self.ui.btn_metronome.clicked.connect(self.start_metronome)
        self.ui.d_bpm.valueChanged.connect(self.update_bpm_dial)
        self.ui.sb_bpm.valueChanged.connect(self.update_bpm_le)
        self.ui.vs_volume.valueChanged.connect(self.update_volume_slider)
        self.ui.sb_meter.valueChanged.connect(self.update_meter)
        
        self.start_icon.addPixmap(QtGui.QPixmap(":/metronome button/start.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.stop_icon.addPixmap(QtGui.QPixmap(":/metronome button/stop.svg"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        
        self.ui.svg_visbeat_on = QtSvg.QSvgWidget('lighton.svg', self.ui.centralwidget)
        self.ui.svg_visbeat_off = QtSvg.QSvgWidget('lightoff.svg', self.ui.centralwidget)
        self.ui.svg_visbeat_on.setGeometry(QtCore.QRect(250, 490, 60, 60))
        self.ui.svg_visbeat_on.hide()
        self.ui.svg_visbeat_off.setGeometry(QtCore.QRect(250, 490, 60, 60))
        self.visbeatOnSignal.connect(self.visbeat_on)
        self.visbeatOffSignal.connect(self.visbeat_off)
        self.visbeat_enable()
        
        self.ui.action_nonstandard_tuning.triggered.connect(self.nonstandard_tuning)
        self.A = 0 # Initial value; 440 or loaded value set in set_defaults.
    
        self.ui.tuner_display = TunerDisplay(self.ui.centralwidget)
        self.ui.tuner_display.setGeometry(QtCore.QRect(10, 10, 360, 200))
        self.set_defaults()
        
    def visbeat_enable(self):
        """Shows or hides the off visbeat circle, depending on if it's checked in Settings."""
        if self.ui.action_visbeat.isChecked():
            self.visbeat_enabled = True
            self.ui.svg_visbeat_off.show()
        else:
            self.visbeat_enabled = False
            self.ui.svg_visbeat_off.hide()
        
    def visbeat(self):
        """Set timing for visual "light" flash on metronome beat. 
        Appears to require a separate thread for the timing, and signals to update the GUI thread."""
        # Offset for the beat not reaching peak intensity immediately.
        # 0.015s as measured between start/peak of beat wave, seems too low. .09 feels right.
        if self.ui.action_visbeat.isChecked():
            time.sleep(.09) 
            main.visbeatOnSignal.emit()
            time.sleep(.06)
            main.visbeatOffSignal.emit()
    
    def visbeat_on(self):
        self.ui.svg_visbeat_off.hide()
        self.ui.svg_visbeat_on.show()
    
    def visbeat_off(self):
        self.ui.svg_visbeat_on.hide()
        self.ui.svg_visbeat_off.show()

    def set_defaults(self):
        """Sets metronomte.Metronome's class variables based on GUI widgets values, or a save file.""" 
        # Populates Instruments using values from metronome.py; somewhat of a reversal
        # Here instead of in Designer, so assignments can be changed from a single source.
        ag_tick = QtWidgets.QActionGroup(self.ui.menuTick, exclusive=True)
        ag_accent = QtWidgets.QActionGroup(self.ui.menuAccent, exclusive=True)
             
        for inst in metronome.Metronome.instruments:
            tick = QtWidgets.QAction(inst, self.ui.menuTick, checkable=True) 
            accent = QtWidgets.QAction(inst, self.ui.menuAccent, checkable=True) 
            
            ag_tick.addAction(tick)
            ag_accent.addAction(accent)
            self.ui.menuTick.addAction(tick)
            self.ui.menuAccent.addAction(accent)
            
            self.tickitems.append(tick)
            self.accentitems.append(accent)
            # functools instead of lambda to avoid a scoping issue, returning the last instrument on every action.
            tick.toggled.connect(functools.partial(self.update_tick, inst)) 
            accent.toggled.connect(functools.partial(self.update_accent, inst))
        
        settings = self.load('save.json')
        if settings:
            self.ui.d_bpm.setValue(settings['bpm'])
            self.ui.vs_volume.setValue(settings['volume'])
            self.ui.sb_meter.setValue(settings['meter'])
            self.ui.action_visbeat.setChecked(settings['visbeat'])
            self.visbeat_enable() # This function is required to be run to show or hide the visbeat.
            self.update_A(settings['A'])
            try:
                self.set_instruments(settings['tick'], settings['accent'])
            except ValueError:
                self.set_instruments("Metronome click", "Castanets")
        else:
            self.set_instruments("Metronome click", "Castanets")
            self.update_A(440)
        #self.update_instrument_tick()
        #self.update_instrument_accent() 
        self.update_meter()
        self.update_bpm_dial()
        self.update_volume_slider()
        self.update_tempo()
    
    def load(self, filename):
        filename = os.path.join(DIR, filename)
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save(self):
        for item in self.tickitems:
            if item.isChecked():
                tick = item.text()
        for item in self.accentitems:
            if item.isChecked():
                accent = item.text()
        filename = os.path.join(DIR, 'save.json')
        settings = {
            'bpm': self.ui.d_bpm.value(),
            'volume': self.ui.vs_volume.value(),
            'meter': self.ui.sb_meter.value(),
            'tick': tick,
            'accent': accent,
            'visbeat': self.visbeat_enabled,
            'A': self.A
        }
        try:
            with open(filename, 'w') as f:
                json.dump(settings, f)
            self.ui.statusbar.showMessage("Settings saved")
        except PermissionError:
            print("Error saving:", filename, "is open. Close and try again.")
      
    def set_instruments(self, tick, accent):
        for item in self.tickitems:
            if item.text() == tick:
                    item.setChecked(True)
            for item in self.accentitems:
                if item.text() == accent:
                    item.setChecked(True)

    def about(self):
        """Displays the About window."""
        self.w = About()
        self.w.show()
     
    def nonstandard_tuning(self):
        self.w = NonstandardTuning()
        self.w.show()
     
    #def settings(self):
     #   """Displays the Settings window."""
      #  self.w = Settings()
       # self.w.show()
        
    def hotkeys(self):
        """Displays the Hotkeys window."""
        self.w = Hotkeys()
        self.w.show()
    
    def update_A(self, A):
        tuner.notes, tuner.notes_ordered = {}, {} # Required to prevent TypeError: 'dict' object is not callable.
        tuner.notes, tuner.notes_ordered = tuner.populate_notes(A)[0], tuner.populate_notes(A)[1] #potentailly clean this up in the tuner module.
        self.A = A #Used for setting the value on the Nonstard_Tuning window.
    
    def update_tick(self, inst):
        metronome.m.instrument_tick = metronome.m.instruments[inst]
        
    def update_accent(self, inst):
        metronome.m.instrument_accent = metronome.m.instruments[inst]
           
    def update_meter(self):
        metronome.m.meter = self.ui.sb_meter.value()

    def start_tuner(self):
        tuner.stop_flag = False
        #tuner.t.freqSignal.connect(lambda freq: self.ui.lbl_freq.setText(' '.join([freq, "Hz"])))
        #tuner.t.noteSignal.connect(lambda note: self.ui.lbl_note.setText(note))
        #tuner.t.centsSignal.connect(lambda cents: self.ui.lbl_cents.setText(cents))
        #tuner.t.hs_centsSignal.connect(lambda hs_cents: self.ui.tuner_display.setValue(hs_cents))
        tuner.t.updateSignal.connect(lambda freq, note, cents: self.update_tuner(freq, note, cents))
        
        tuner_instance.start(priority=5)
        print("PRIORITY",tuner_instance.Priority()) #why isn't this working?
        #self.ui.btn_tuner.setText("Stop")
        self.ui.btn_tuner.setIcon(self.stop_icon)
        self.ui.btn_tuner.disconnect()
        self.ui.btn_tuner.clicked.connect(self.stop_tuner)
        
    def update_tuner(self, freq, note, cents):
        self.ui.lbl_freq.setText(' '.join([freq, "Hz"]))
        letter = note[:2] if "#" in note else note[0]
        oct = note[-1]
        self.ui.lbl_note.setText(''.join([letter,'<sub>',oct,'</sub>']))
        
        sign = "+" if cents >= 0 else ""
        self.ui.lbl_cents.setText(sign + str(int(cents)) + " ¢")
        self.ui.tuner_display.setValue(cents)
        print("CENTS:", cents)
        
    def stop_tuner(self):
        tuner.stop_flag = True
        tuner_instance.quit()
        #self.ui.btn_tuner.setText("Start")
        self.ui.btn_tuner.setIcon(self.start_icon)
        self.ui.btn_tuner.disconnect()
        self.ui.btn_tuner.clicked.connect(self.start_tuner)
        
    def start_metronome(self):
        metronome.m.volume = self.ui.vs_volume.sliderPosition() / 100      
        metronome_instance.start()
        metronome.m.visbeatSignal.connect(lambda: visbeat_instance.start())
        self.ui.btn_metronome.setIcon(self.stop_icon)
        self.ui.btn_metronome.clicked.disconnect()
        self.ui.btn_metronome.clicked.connect(self.stop_metronome)

    def stop_metronome(self):
        metronome_instance.quit() # Closes the thread's event loop, killing the metronome's QTimer.
        self.ui.btn_metronome.setIcon(self.start_icon)
        self.ui.btn_metronome.clicked.disconnect()
        self.ui.btn_metronome.clicked.connect(self.start_metronome)
       
    def update_bpm_dial(self):
        bpm = self.ui.d_bpm.sliderPosition()
        metronome.m.bpm = bpm
        self.update_tempo()
        self.ui.sb_bpm.setValue(bpm)

    def update_volume_slider(self):
        metronome.m.volume = self.ui.vs_volume.sliderPosition() / 100
          
    def update_bpm_le(self):
        try:
            bpm = int(self.ui.sb_bpm.value())
        except ValueError:
            print("VALUEE RROR WHAT's UP?")
            return None
        metronome.m.bpm = bpm
        self.update_tempo()
        self.ui.d_bpm.setValue(bpm)
            
    def update_tempo(self):
        bpm = self.ui.d_bpm.sliderPosition()
        tempo = str([tempo for tempo, range in metronome.m.tempos.items() if range[0] <= bpm <= range[1]][0]) 
        self.ui.lbl_tempo.setText(tempo)
               
    def keyPressEvent(self, e):
        #if e.key() == QtCore.Qt.Key_Space:
            #main.start_metronome()
        
        if e.key() == QtCore.Qt.Key_S and e.modifiers() == QtCore.Qt.ControlModifier:
            self.save()
 

class TunerDisplay(QtWidgets.QWidget):
    #centralize the configurable settings, and possibly add qt-style methods to change them.
    # possibly have tick size scale with widget size.
    def __init__(self, parent=None):
        super(TunerDisplay, self).__init__(parent)
        self.cents = 0
        self.RANGE = 140 #number of degrees to cover full deflection, centered on vertical
        self.theta_min = 90 - self.RANGE/2 # 0 degrees is at the left; counts up counter-clockwise.
        self.theta_max = self.theta_min + self.RANGE
        self.marg_t = 20
        # marg_b does not take bottom half of needle-base-circle into account. 
        #0 margin sets the needle base on the bottom of the widget.
        self.marg_b = 20 
        
    def setValue(self, cents):
        self.cents = cents
        self.update()
 
    def setRange(self, range):
        self.RANGE = range
        self.update()
        
    def setMargins(self, marg_t, marg_b):
        self.marg_t = marg_t
        self.marg_b = marg_b
        
    def paintEvent(self, event=None):
        self.w = self.size().width()
        self.h = self.size().height()
        # min and max full scale deflection in degrees left to right, 0 degrees = full left.
        #Set the else option to be not just if h>w, but if the full deflection can't be included. This occurs
        #if wider than tall, but not wide enough.
        self.r = self.h - (self.marg_t+self.marg_b) if self.w > self.h else self.w/2 # Needle length, aka circle radius.
        self.r_b = 10 # Radius of the circle at the nonmoving needle end.
        
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setRenderHint(QtGui.QPainter.Antialiasing) 
        self.draw_circle(qp)
        self.draw_background(qp)       
        self.draw_needle(qp)
        qp.end()
      
    def draw_background(self, qp):
        # Bounding box.
        qp.setPen(QtGui.QPen(QtCore.Qt.black, 1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap))
        qp.setBrush(QtGui.QBrush(QtGui.QColor(255,0,0,0))) #find cleanear way to set empty brush than setting 0 alpha
       # qp.drawRect(0, 0, self.w, self.h)
        
        # Main arc.
        qp.setPen(QtGui.QPen(QtCore.Qt.black, 2, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap))
        qp.drawArc(QtCore.QRect(self.w/2 - self.r, self.h-(self.r+self.marg_b), self.r*2, self.r*2), 
            self.theta_min*16, self.RANGE*16) #0 starts on the right side

        #theta_l = theta_r + 2*(math.pi/2-theta_r)
        #qp.drawLine(*self.tick_coords(tick_len, tick_cents, theta_r))
        
        # Bounding ticks.
        base = self.r / 5 #base tick size  Change this behavior. ie make it a self.? and set with a setTickSize method?
        qp.setPen(QtGui.QPen(QtGui.QColor(255,128,0), 1))
        self.draw_tick(0, qp, base*2)
       # qp.setPen(QtGui.QPen(QtGui.QColor(0,255,64), 2))
        qp.setPen(QtGui.QPen(QtCore.Qt.black, 1))
        self.draw_tick(5, qp, base*1.5, 'inside', label=True, shade=True)
        self.draw_tick(10, qp, base*.5, 'inside', label=False)
        self.draw_tick(15, qp, base*.5, 'inside', label=False)
        self.draw_tick(20, qp, base, 'inside', label=True)
        self.draw_tick(30, qp, base, 'inside', label=True)
        self.draw_tick(40, qp, base, 'inside', label=True)
        self.draw_tick(50, qp, base*2, 'inside', label=True)
        
    def draw_circle(self, qp):
        alpha_sharp, alpha_flat = 0, 0
        if self.cents > 0:
            alpha_sharp, alpha_flat = abs(self.cents) * 256/50 - 1, 0
        elif self.cents < 0:
            alpha_flat, alpha_sharp = abs(self.cents) * 256/50 - 1, 0
            
        # In-tune base.
        qp.setPen(QtGui.QPen(QtCore.Qt.black, 1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap))
        qp.setBrush(QtGui.QBrush(QtGui.QColor(0,255,0)))
        qp.drawEllipse(QtCore.QRect(self.w/2 - self.r_b, (self.h-self.marg_b) - self.r_b, 2*self.r_b, 2*self.r_b))
        # Sharp mask.
        qp.setBrush(QtGui.QBrush(QtGui.QColor(0,0,255, alpha_sharp)))
        qp.drawEllipse(QtCore.QRect(self.w/2 - self.r_b, (self.h-self.marg_b) - self.r_b, 2*self.r_b, 2*self.r_b))
        # Flat mask.
        qp.setBrush(QtGui.QBrush(QtGui.QColor(255,0,0, alpha_flat)))
        qp.drawEllipse(QtCore.QRect(self.w/2 - self.r_b, (self.h-self.marg_b) - self.r_b, 2*self.r_b, 2*self.r_b))
        
    def draw_needle(self, qp):
        theta = self.find_theta(self.cents)
        qp.setPen(QtGui.QPen(QtGui.QColor(0, 0, 230), 1.5, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap))
        qp.drawLine(*self.needle_coords(theta, self.r))   
        
    def needle_coords(self, theta, r):
        # x0 and y0 define the nonmoving, bottom needle end. x1 and y1 define the moving, top end.
        x0 = self.w/2 
        y0 = self.h - self.marg_b
        x1 = self.w/2 - (r*math.cos(theta))
        y1 = self.h - (r*math.sin(theta) + self.marg_b)   ###
        return(x0, y0, x1, y1)
     
    def draw_tick(self, cents, qp, base, side='both', label=False, shade=False):
        qp.drawLine(*self.tick_coords(base, -cents, side))
        qp.drawLine(*self.tick_coords(base, cents, side))
        if label:
            theta_neg = self.find_theta(-cents)
            theta_pos = self.find_theta(cents)
            coords_neg = self.needle_coords(theta_neg, self.r+10)[2:]
            coords_pos = self.needle_coords(theta_pos, self.r+10)[2:]
            # This offset simulates right text alignment, which I can't seem to do otherwise without a qrect.
            x_neg = coords_neg[0] - self.r / 10.7
            qp.setFont(QtGui.QFont('Decorative', self.r / 18))
            qp.drawText(x_neg, coords_neg[1], "-" + str(cents))
            qp.drawText(coords_pos[0], coords_pos[1], "+" + str(cents))
        if shade:
            #theta_neg = math.degrees(self.find_theta(-cents))
            #theta_pos = math.degrees(self.find_theta(cents))
            qp.setPen(QtGui.QPen(QtGui.QColor(0,255,64, 0), 0))
            qp.setBrush(QtGui.QBrush(QtGui.QColor(0, 255, 64, 60)))
            neg = self.tick_coords(base, -cents, 'inside')
            pos = self.tick_coords(base, cents, 'inside')
            
            
            
            path = QtGui.QPainterPath()
            path.setFillRule(QtCore.Qt.WindingFill)
            path.moveTo(neg[0], neg[1]) #Should probably be using arcs when appropriate. Lines are a good approx for now.
            path.lineTo(pos[0], pos[1])
            path.lineTo(pos[2], pos[3])
            path.lineTo(neg[2], neg[3])
            path.lineTo(neg[0], neg[1])

            qp.drawPath(path)
            qp.setPen(QtGui.QPen(QtCore.Qt.black, 1, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap))
    
    def tick_coords(self, len, cents, side='both'):
        # len is the length for a tick on both sides.  Length of inside or outside ticks is half len.
        theta = self.find_theta(cents)
        #Finds the center of the tick. Uses trig to calculate a point on either side of it, following
        # angle theta, and half tick length (hypotenuse).
        c_coords = self.needle_coords(theta, self.r)
        xc, yc = c_coords[2], c_coords[3] # Center point for the tick; located on the arc.
        a = len*.5 * math.cos(theta) # Horizontal distance between center point and tick end.
        b = len*.5 * math.sin(theta) # Vertical distance between center point and tick end.
        if side == 'both' or side == 'outside':
            x0, y0 = xc - a, yc - b
        else:
            x0, y0 = xc, yc
        if side == 'both' or side == 'inside':
            x1, y1 = xc + a, yc + b
        else:
            x1, y1 = xc, yc
        return(x0, y0, x1, y1)
        
        #x0, y0, x1, y1 = self.needle_coords(theta, self.r)
        #m = (y1-y0) / (x1-x0)
        #b = y0 - m*x0 #you're reusing x0 etc, and b. stop.
        #x0 = 110
        #y0 = (m*x0 + b)
        #(x1_t-x0_t)**2 + (y0_t-y1_t)**2 = len**2
        #a = len * math.cos(theta) # Horizontal triangle side.
        #b = len * math.sin(theta)  # Vertical triangle side.
        #sin(theta) = b / len #solve
        #cos(theta = a / len
        #theta is the angle between horizontal and the line. theta2 is the angle between vertical and the line
        #theta2 = 180 - (theta + 90) 
        #sin(theta) = o/len
        #tan(theta) = o/a
        #cos(theta) = a/len
        #x1_t = math.sqrt(len**2 - (y0_t-y1_t)**2) + x0_t # re-arranged pythagorean formula
        #x1_t = 120
        #y1_t = (m*x1_t + b)
    
    def find_theta(self, cents):
        """Returns the angle, in radians, correspnoding to an input cents"""
        ratio = (self.theta_max-self.theta_min) / 100 # 100 is the range of cents, -50 to 50.
        theta = math.radians(((cents + 50) * ratio) + self.theta_min)
        return theta
   

class About(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = Ui_About()
        self.ui.setupUi(self)

class NonstandardTuning(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.resize(160, 100)
        self.setWindowTitle(" ")
        
        self.lbl_a = QtWidgets.QLabel(self)
        self.lbl_a.setGeometry(QtCore.QRect(10, 10, 40, 30))
        self.lbl_a.setText("A = ")
        
        self.sb_freq = QtWidgets.QSpinBox(self)
        self.sb_freq.setGeometry(QtCore.QRect(70, 10, 80, 30))
        self.sb_freq.setMinimum(400)
        self.sb_freq.setMaximum(500)
        self.sb_freq.setValue(main.A)
        
        self.btn_set = QtWidgets.QPushButton(self)
        self.btn_set.setGeometry(QtCore.QRect(70, 50, 80, 30))
        self.btn_set.setText("Set")
        self.btn_set.clicked.connect(self.set)
        
    def set(self):
        A = self.sb_freq.value()
        main.update_A(A)
        self.close()
        
#class Settings(QtWidgets.QWidget):
 #   def __init__(self, parent = None):
  #      QtWidgets.QWidget.__init__(self, parent)
   #     self.ui = Ui_Settings()
    #    self.ui.setupUi(self)
  
  
class Hotkeys(QtWidgets.QWidget):
    def __init__(self, parent = None):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = Ui_Hotkeys()
        self.ui.setupUi(self) 
       
       
class TunerThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)

    def __del__(self):
        self.wait()
        
    def run(self):
        tuner.start()
        tuner_instance.exec_()

        
class VisbeatThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
        
    def __del__(self):
        self.wait()
        
    def run(self):
        main.visbeat()
        
        
class MetronomeThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self):
        metronome.m.start()
        metronome_instance.exec_()
 
  
class PlotThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self):
        plot()

 
         
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = Main()
    main.show()
    
    metronome_instance = MetronomeThread()
    tuner_instance = TunerThread()
    visbeat_instance = VisbeatThread() #can these go in the Main __init__??
    plot_instance = PlotThread()
    sys.exit(app.exec_())