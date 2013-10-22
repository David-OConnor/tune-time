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
    
import collections
    
import pygame.midi
from PyQt5 import QtCore


class Metronome(QtCore.QObject):
    visbeatSignal = QtCore.pyqtSignal() #Change visbeat signal for accent
    instruments = collections.OrderedDict([
        ("Bass drum", 36),
        ("Bongo - high", 60),
        ("Bongo - low", 61),
        ("Castanets", 85),
        ("Conga", 62),
        ("Cowbell", 56),
        ("Metronome click", 33),
        ("Side stick", 37),
        ("Squared click", 32),
        ("Wood block - High", 76),
        ("Wood block - Low", 77),
     ])

    tempos = {"Lento": (40, 59),
        "Larghetto": (60, 65),
        "Adagio": (66, 75),
        #"Adagietto": (70, 75),
        "Andante": (76, 89),
        #"Andantino": (70, 88),
        "Moderato": (90, 114),
        "Allegretto": (115, 119), #?
        "Allegro": (120, 167),
        #"Vivace": (135, 88),
        "Presto": (168, 199),
        "Prestissimo": (200, 240),                  
    }

    pygame.midi.init()
    port = pygame.midi.get_default_output_id()
    midi_out = pygame.midi.Output(port)

    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent) 
    
    def start(self):
        self.current_beat = 1 # Counting starts at 1; the downbeat.
        self.timer = QtCore.QTimer()
        self.timer.setTimerType(0) # This sets "precise" (ms) accuracy.
        self.timer.timeout.connect(lambda: self.play_beat())
        self.timer.start()
        
    def play_beat(self):
        try: # Sets "Metronome click" in the case a bug prevents an instrument from being selected in the menu.
            active_instrument = self.instrument_accent if self.current_beat == 1 and self.meter != 1 else self.instrument_tick
        except AttributeError:
            active_instrument = 33
        # Converts volume on 0-1 scale to 0-127 scale.
        midi_volume = int((128*self.volume) - 1)
        self.timer.setInterval((60/self.bpm) * 1000)
        # Channel 9 is for percussion. Instrument is set separately for other channels
        self.midi_out.note_on(active_instrument, midi_volume, channel=9) 
        self.visbeatSignal.emit()
        self.current_beat += 1
        if self.current_beat > self.meter:
            self.current_beat = 1
        
        
        #if self.stop_flag:
            #midi_out.note_off(perc_instrument, midi_volume, channel=9) #May not be necessary/doesn't seem to work
            #midi_out.close() #I don't think this is working.
            #del midi_out
            #pygame.midi.quit() # This should uninitialize the midi module, but doesn't.

m = Metronome()