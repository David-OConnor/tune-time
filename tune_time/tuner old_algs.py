{   # Tune Time - Chromatic instrument tuner and metronome
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
    } 

import math    
import struct
import time

import numpy as np
import scipy
import scipy.fftpack
import scipy.signal
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pyaudio 
from PyQt5 import QtCore, QtWidgets


#Smoothing algorithm. Kalman filter?
#Checks past few freqs, ideally with windowing, and doesn't update if it's messed up.
#Time each element, set a frameFS.


class Tuner(QtCore.QObject):
    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent) 

    freqSignal = QtCore.pyqtSignal(str)
    noteSignal = QtCore.pyqtSignal(str)
    centsSignal = QtCore.pyqtSignal(str)
    hs_centsSignal = QtCore.pyqtSignal(float)

    def update_tuner(self, freq, note, cents):
        print("freq:", freq, "note:", note, "cents off:", cents)
        self.freqSignal.emit(str(freq))
        self.noteSignal.emit(note)
        self.centsSignal.emit(str(cents))
        self.hs_centsSignal.emit(cents)
 
notes_oct1 = {
    'A': 27.5, 'A#': 29.1352, 'B': 30.8677, 'C': 32.7032, 'C#': 34.6478, 'D': 36.7081,
    'D#': 38.8909, 'E': 41.2034, 'F': 43.6535, 'F#': 46.2493, 'G': 48.9994, 'G#': 51.9131,
}

# Populate octaves 2 - 8 by doubling notes in octave one each iteration. Ex use: notes[C#5] = 554.3648
notes = {k + str(exp+1): v*(2**exp) for k, v in notes_oct1.items() for exp in range(8)}
# An (ordered) list is used to fix the log vs absolute scale issue described in the freq_to_note func.
notes_ordered_1 = sorted(list(notes_oct1.keys()))
notes_ordered = [note + str(octave) for note in notes_ordered_1 for octave in range(1,9)]
  
def freq_to_note(freq):
    differences = {k: math.fabs(v - freq) for k, v in notes.items()}
    nearest = min(differences, key=differences.get)
    # Could take min difference in cents instead of below code; current method may be faster due to
    # Multiple subtraction calls instead of multiple log calls. Code below takes into account
    # that taking an absolute (non-log) difference could lead to showing an A, being sharp 51 cents
    # instead of an A# 49 cents flat.
    if cents_off(freq, notes[nearest]) > 50:
        note_above = notes_ordered.index(nearest) + 1
        try:
            note = notes_ordered[note_above]
        except IndexError: #sort out later
            print("INDEXERROR")
            note = 'C1'
        return note
    else: 
        return nearest

def cents_off(measured_freq, note_freq):
    #try:
    return 1200 * math.log2(measured_freq/note_freq)
   # except ValueError:
    #    print(measured_freq, note_freq, sep='---')


    
FORMAT = pyaudio.paInt16
CHANNELS = 1
FS = 44100 # Sample rate
#chunk_time = CHUNK / FS
FPS = 30
CHUNK = 1024
CHUNKS_PER_BUFFER = 50
NOISE_FLOOR = 0

PFSIZE = 10


def start(): #Make creating the stream and p not thread-specific? Pass it to each thread(s)?
    global past_freqs
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=FS,
                    input=True, 
                    frames_per_buffer=CHUNK)
    
                    
   # global timer
    #timer = QtCore.QTimer(interval=(1/FPS) * 1000)
   # timer.timeout.connect(lambda: find_freq(stream, p))
    analysis(stream, p)
    #timer.start()
 

def find_peaks(a, new_width, maxThresh, minThresh, LEV, i, aver, min_indices, max_indices):
    max_count = np.zeros(LEV)
    min_count = np.zeros(LEV)
    max_count[i], min_count[i] = 0, 0
    climber = 1 if a[i, 1] - a[i,0] > 0 else -1 # 1 if ascending, -1 if descending.
    peak_possible = True # Tracks whether an extreme can be found (based on zero crossings)
    too_close = 0 # Tracks how many more samples must be moved before another extreme. Counts down. 
    #Peaks are allowed to be can be found when too_close == 0.
    for j in range(1, new_width-1):
        current, previous = a[i, j], a[i, j-1]
        change = current - previous
        if peak_possible and not too_close:
            if climber == 1 and change < 0 and previous >= maxThresh: # Indicates last sample was a positive peak.
                max_count[i] += 1
                max_indices[i, max_count[i]] = j - 1
                peak_possible = False
                too_close = min_dist
                climber *= -1 # Reverses climber status, eg. Ascending to descending.
            elif climber == -1 and change > 0 and previous <= minThresh: # Indicates last sample was a negative peak.
                min_count[i] += 1
                min_indices[i, min_count[i]] = j - 1
                peak_possible = False
                too_close = min_dist
                climber *= -1 # Reverses climber status, eg. Ascending to descending.
        if current <= aver < previous or previous < aver <= current:  # This statement is true if at an adjusted zero-crossing.
            peak_possible = True
        if too_close:
            too_close -= 1
    return (min_indices, max_indices, min_count, max_count)  #possibly just return the row, and append it



def wavePitch(data, old_freq=None):
    print("old_freq:", old_freq)
    old_mode = 0
    if old_freq:
        old_mode = FS/old_freq

    LEV = 6 # Six levels of analysis. 
    GLOBALMAXTHRESH = .6 # Thresholding of maximum values to consider.
    MAX_FREQ = 3000 # Yields minimum distance to consider valid .
    DIFF_LEVS = 3 # Number of differences to go through (3 is diff @ third neighbor).
    
    #max_count = np.zeros((LEV, data.size))
    #min_count = np.zeros((LEV, data.size))
    

    
    a = np.zeros((LEV, data.size))
    d = np.zeros((LEV, data.size))
    a[0] = data
    print("a", a)
    aver = np.mean(a[0])
    globalMax = np.max(a[0])
    globalMin = np.min(a[0])
    maxThresh = GLOBALMAXTHRESH * (globalMax-aver) + aver # Adjust for DC offset
    minThresh = GLOBALMAXTHRESH * (globalMin-aver) + aver # Adjust for DC offset
    
    #setting up matrices; not in orgiginal matlab file. Figure out what else goes here.
    mode = np.zeros(LEV) #mode of the distance between peaks for the original (non halved) spectrum
    max_indices = np.zeros((LEV, 20)) #fix this 60 nonsense. Have it expand with appends?
    min_indices = np.zeros((LEV, 20))
    
    # Begin pitch detection.
    for i in range (1, LEV):
        print("i:", i)
        new_width = data.size // (2**i)  #? Divides data in powers of 2. ie turns 1024 in 512, 256, 128, 64, 32
    
        # Performs a fast lifting wavelet transform. 
        j = np.arange(new_width)
        d[i, j] = a[i-1, 2*j] - a[i-1, 2*j-1]
        a[i, j] = a[i-1, 2*j-1] + d[i, j] / 2

        #find the maxes of the current approximation
        min_dist = np.maximum(np.floor(FS/MAX_FREQ/(2**i)),1) #7, 3, 1, 1, 1 for i=0 to i=5. Threshold for peak spacings.
        

        
        min_indices, max_indices, min_count, max_count =\
            find_peaks(a, new_width, maxThresh, minThresh, LEV, i, aver, min_indices, max_indices)
       
        
        print("max_indices:", max_indices)
        print("min_indices:", min_indices)
        print("max_count:", max_count)
        print("min_count:", min_count)

        if max_count[i] >= 2 and min_count[i] >= 2: # Can't find a distance between fewer than two peaks.
           # print("MAX_INDICES:", max_indices)
           # print("MAX COUNT:", max_count)
           # print("MAX_count[i]:", max_count[i])
            #print("Min_count[i]:", min_count[i])
           # Calculate the difference at DIFF_LEVS distances.
            differs = np.array([])
            for j in range(1, DIFF_LEVS+1): # Inteveral of differences (neighbor, next-neighbor)
                k = max_count[i] - j #Days to look back
                differs = np.append(differs, abs(max_indices[i, max_count[i]-1] - max_indices[i, k-1]))
                k = min_count[i] - j
                differs = np.append(differs, abs(min_indices[i, min_count[i]-1] - min_indices[i, k-1]))
            print("Differs:", differs)
            d_count = differs.size
            print("d_count:", d_count)


        
            # Find the center mode of the differences.
            numer = 1 # Require at least two agreeing differs to yield a mode
            mode[i] = 0 # If none is found, leave as zero
            for j in range(d_count):
                # Find the # of times that distance j is within min_dist samples of another distance
                numerJ = len(matplotlib.mlab.find(abs(differs[:d_count] - differs[j]) <= min_dist))
                print("numerJ:", numerJ)
                #If there are more, set the new standard
                if numerJ >= numer and numerJ > np.floor(new_width/differs[j])/4:
                    if numerJ == numer:
                        if old_mode and abs(differs[j] - old_mode/(2**i)) < min_dist:
                            mode[i] = differs[j]
                        elif not old_mode and 1.95*mode[i] < differs[j] < 2.05*mode[i]:
                            mode[i] = differs[j]
                    else:
                        numer = numerJ
                        mode[i] = differs[j]
                elif numerJ == numer-1 and old_mode and abs(differs[j] - old_mode/(2**i)) < min_dist:
                    mode[i] = differs[j]
                    
            # Set the mode via averaging
            print("MODE", mode)
            
            if mode[i]:
                mode[i] = np.mean(differs[matplotlib.mlab.find(abs(mode[i] - differs[:d_count]) <= min_dist)]) #numpy.nonzero for find?
            
            # Determine if the modes are shared
            
            print("mode[i]1", mode[i-1])
            print("max_count[i-1]:", max_count[i-1])
            print("min_count[i-1]:", min_count[i-1])
            if mode[i-1] and max_count[i-1] >= 2 and min_count[i-1] >= 2:
                #If the modes are within a sample of one another, return the calculated frequency
                
                print("mode:", mode)
                print("min_dist:", min_dist)
                print("Mode[i-1]-2:", mode[i-1]-2)
                print("mode[i]:", mode[i])
                print("Non-returned freq:", FS/mode[i-1] / 2**(i-1))
                
                if abs(mode[i-1] - 2*mode[i]) <= min_dist:
                    freq = FS/mode[i-1] / 2**(i-1)
                    return freq
            
            plt.subplot(2,1,1)
            plt.plot(data)
            plt.subplot(2,1,2)
            plt.plot(a[i])
            plt.show()
    return 0
    
    
'''
  #   global past_freqs
    #amps = read_stream(stream, CHUNK * CHUNKS_PER_BUFFER)  #for basic windowing
   # amps = np.array([])
         #amps = np.hstack([amps, read_stream(stream, CHUNK)]) #For basic windowing
        #amps = scipy.signal.resample(amps, CHUNK * 20)
        #freq_peaks = Peaks.find_freq(filtered, freq_fft)
        #dif = abs(freq_fft-freq_peaks)
       # freq = freq_peaks if dif < FS/CHUNK else past_freqs[-1]
        #freq = freq_fft      
      #  plot(amps, filtered, data_fft)
        #if amps.size > CHUNK * CHUNKS_PER_BUFFER:  #for windowing
         #   amps = amps[CHUNK:]     #for windowing        
'''


    
def analysis(stream, p):
    global old_freq
    old_freq = None
    while not stop_flag:
        amps = read_stream(stream, CHUNK)
        #data_fft = scipy.fft(amps)
        #freq_fft = freq_from_fft(data_fft)
        #cutoff_low = freq_fft + ((FS/CHUNK) * 1.0) # cutoff_low is the cutoff for the lowpass filter; it's the higher number.
        #cutoff_high = freq_fft - ((FS/CHUNK) * 1.0) #1.x = buffer 
        #filtered = Peaks.bandpass(amps, cutoff_low, cutoff_high) 
        #freq_zeros = find_zeros(filtered, freq_fft)
        
        freq_flwt = wavePitch(amps, old_freq) #Sends "None" as old_freq on first run. Sends previous freq otherwise.
        freq = freq_flwt
        old_freq = freq_flwt
        #data = amps
        #avgs = [(a+b)/2 for a, b in zip(data[::2], data[1::2])] #lowpass?
        #residues = [a - avg for a, avg in zip(data[::2], avgs)] #highpass?
        
        
        #plot(data, residues, data_fft)
        
        print("Freq:", freq)
        #print(freq_peaks, "freq_peaks")
        #print(freq_fft, "FFT")
        #print(dif, "DIF")
        #print(freq_zeros, "ZEROS FREQ")


        if not freq: #figure out what this is for, then describe it with this comment
            continue
        
        
        #past_freqs.append(freq)
        #if len(past_freqs) > PFSIZE:
         #   past_freqs = past_freqs[1:]
        note = freq_to_note(freq)
        cents = cents_off(freq, notes[note])
        print(freq, note, cents)
        t.update_tuner(freq, note, cents)
        
        time.sleep(0)
         
    stream.stop_stream()
    stream.close()
    p.terminate()

def freq_from_fft(data):
    freq_mask = scipy.fftpack.fftfreq(data.size)
    peak = np.argmax(np.abs(data)**2)
    if peak < NOISE_FLOOR:
        return 0
    freq = freq_mask[peak] * CHANNELS
    freq_in_hz = abs(freq * FS)
    return freq_in_hz

def find_zeros(data, ref_freq):
    zeros = np.where(np.diff(np.sign(data)))[0]
    print("ZEROS:", zeros)
    spacings_ = Peaks.peak_spacings(zeros)
    print("0s spacing:", spacings_)
    
    expected_spacing = (FS/ref_freq) / 2
    
    try:
        avg_spacing = np.mean(spacings_)
    except TypeError:
        return ref_freq 
    return (FS/avg_spacing) / 2

   
class Peaks:
    freq_max1 = 500
    freq_max2 = 1500 
    freq_max3 = 4000
    width = np.arange(20, 40) #What  should this be?
    cutoff = freq_max1 
    
    def find_freq(filtered, ref_freq):
        """Uses a frequency from an impreceise FFT to set peak-search parameters"""
        width_multiplier = .5 #Looks for pulse widths at expected wavelength, multiplied by this value 
        try:
            expected_peak_spacing = (FS * (1 / ref_freq)) * width_multiplier  
        except ZeroDivisionError:
            expected_peak_spacing = 25
        width = np.array(expected_peak_spacing)
   
        peaks_filtered = scipy.signal.find_peaks_cwt(filtered, Peaks.width)
        spacings = Peaks.peak_spacings(peaks_filtered)
        spacings_no_outliers = Peaks.reject_outliers3(spacings)
        try:
            avg_spacing = np.mean(spacings_no_outliers)
        except TypeError:
            return ref_freq
        freq = FS / avg_spacing 
        
        print("peaks filtered:", peaks_filtered)
        print("spacings:", spacings)
        print("spacing_no_outliers:", spacings_no_outliers)
        print("avg spacing:", avg_spacing)  
        return freq
    
    def reject_outliers3(data):
        """Returns all values equal to, or one different from the most common value in the sequence"""
        data = data[0] #Seems to be accepting a 2d array, with the second d empty??
        print(data)
        try:
            most_common = np.bincount(data).argmax()
        except TypeError:
            return data
        return [v for v in data if abs(v-most_common) <= 1]
    
    def reject_outliers2(data, m=1.0):
        """Returns a subset of data, where values greater than 1 different from the median are discarded"""
        d = np.abs(data-np.median(data))
        mdev = np.median(data)
        s2 = d - mdev if mdev else 0
        result = data[d<=1]
        return result
    
    def reject_outliers(data, m=1.0):
        try:
            d = np.abs(data - np.median(data)) #Again, median should be ideal but somethimes glitches
        except TypeError:
            return data
        mdev = np.median(d) #mean? median?
        s = d/mdev if mdev else 0
        #print("d", d)
        #print("mdev", mdev)
        #print("s", s)
        try:
            result = data[s<m]
        except IndexError:
            result = data
        return result
        
    def peak_spacings(peaks):
        spacings = []
        for i in range(len(peaks)):
            try:
                spacings.append(peaks[i+1] - peaks[i])
            except IndexError: #occurs at end of sequence
               return np.array([spacings])
             
    def lowpass(amps, cutoff_):
        N = 1001 #What should t his and the line below be?
        a = 1
        b = scipy.signal.firwin(N, cutoff=(cutoff_ / (FS/2)), window='hamming')
        filtered = scipy.signal.lfilter(b, a, amps)
        return filtered
        
    def highpass(amps, cutoff_):
        N = 1001 #What should t his and the line below be?
        a = 1
        #b = scipy.signal.firwin(N, cutoff=(cutoff_ / (FS/2)), window='hamming')
        b = -b
        b[N/2] = b[N/2] + 1
        filtered = scipy.signal.lfilter(b, a, amps)
        return filtered
        
    def bandpass(amps, cutoff_low, cutoff_high):
        N = 1001 #What should t his and the line below be?
        a = 1
        try:
            low = scipy.signal.firwin(N, cutoff=(cutoff_low / (FS/2)), window='hamming')
            high = scipy.signal.firwin(N, cutoff=(cutoff_high / (FS/2)), window='hamming')
        except ValueError:
            return amps
        high[N/2] = high[N/2] + 1
        band = - (low+high)
        band[N/2] = band[N/2] + 1
        filtered = scipy.signal.lfilter(band, a, amps)
        return filtered


def read_stream(stream, size):
    amps_bin = stream.read(size)
    amps = np.array(struct.unpack('{0}h'.format(size * CHANNELS), amps_bin))
    return amps

def plot(amps1, amps2, fft):
    plt.subplot(3,1,1)
    plt.plot(amps1)
    plt.title("amps over time")
    
    plt.subplot(3,1,2)
    plt.plot(amps2)
    plt.title("amps over time, with lowpass")
    
    plt.subplot(3,1,3)
    freq_mask = scipy.fftpack.fftfreq(amps1.size)
    plt.plot(freq_mask * FS, abs(fft))
    plt.xlim(0, 2000)
    plt.title("Frequency spectrum")
    
    plt.show() 

    
    
def plot_animate(stream, p):
    fig = plt.figure()
      # Frequency range
    x_f = 1.0 * np.arange(-CHUNK / 2 + 1, CHUNK / 2) / CHUNK * FS
    #ax = fig.add_subplot(111, title=TITLE, xlim=(x_f[0], x_f[-1]),
     #                    ylim=(0, 2 * np.pi * CHUNK**2 / FS))
                         
    ax = fig.add_subplot(111, title="test!", xlim=(0, 6000),
                         ylim=(0, 2 * np.pi * CHUNK**2 / FS))
    ax.set_yscale('symlog', linthreshy=CHUNK**0.5)
    
    fig.show()
    line, = ax.plot(x_f, np.zeros(CHUNK - 1))

    MAX_y = 2.0**(p.get_sample_size(FORMAT) * 8 - 1)
    frames = None
    wf = None
    
    ani = animation.FuncAnimation(fig, animate, frames,
        init_func=lambda: init(line), 
        fargs=(line, stream, wf, MAX_y),
        interval=1000.0/FPS, blit=True)
        
    plt.show()

def animate(i, line, stream, wf, MAX_y):
    # Read n*CHUNK frames from stream, n > 0
    N = max(stream.get_read_available() / CHUNK, 1) * CHUNK
    data = stream.read(int(N))  #had to add int here to make it work. Possibly a python 3 issue.

    # Unpack data, LRLRLR...
    y = np.array(struct.unpack('%dh' % (N * CHANNELS), data)) / MAX_y
    y_L = y[::2]
    y_R = y[1::2]

    Y_L = np.fft.fft(y_L, CHUNK)
    Y_R = np.fft.fft(y_R, CHUNK)
    #Y = np.fft.fft(y, CHUNK)

    # Sewing FFT of two channels together, DC part uses right channel's
    Y = abs(np.hstack((Y_L[-CHUNK/2:-1], Y_R[:CHUNK/2])))
    #Y = 200 * abs(Y[1:])
    line.set_ydata(Y) 
  
  
    '''
    print(Y.size)
  
    i = np.argmax(np.abs(Y)**2)
    
    freq_mask = scipy.fftpack.fftfreq(Y.size)
    freq = freq_mask[i] * CHANNELS
    freq_in_hz = abs(freq * FS)
    update(freq_in_hz)
    
    '''
    return line,
   
def init(line):
    # This data is a clear frame for animation
    line.set_ydata(np.zeros(CHUNK - 1))
    return line,
    
t = Tuner()