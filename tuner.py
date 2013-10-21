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


import math
import struct

import numpy as np
#import matplotlib.mlab
#import matplotlib.pyplot as plt
#import matplotlib.animation as animation
#import scipy
#import scipy.fftpack
#import scipy.signal
import pyaudio 
from PyQt5 import QtCore


#peak finding: find linear, or otherwise regression of sample. Use the values as dynamic zeros, per sample position
#find the maximum and minimum values that occur between these '0' crossings using a climber.
#maybe divide the sample into subsamples and get a linear regress for each??
#Stretch goal: Tune multiple notes (strings) at once.
#Analze the highest few points in the fft/autocorr intead of the highest. use this to determine if the tone is harmonic or not.
# Use FFT or autocorr depending on othe result? 
#log/exp tuner display scale
#support for nonstandard tuning
#smarter windowing for the smoothing and outlier rejection.
#Option to display flats instead of sharps
#set 0 if there's no valid freq for a few seconds, instead of holding last measured vaalue indefinitely
#stretch goal: Program a strobe tuner

class Tuner(QtCore.QObject):
    updateSignal = QtCore.pyqtSignal(str, str, float)
    
    def __init__(self, parent=None):
        QtCore.QObject.__init__(self, parent) 

    def update(self, freq, note, cents):
        #print("freq:", freq, "note:", note, "cents off:", cents)
        freq = str(round(freq, 2))
        self.updateSignal.emit(freq, note, cents)

def cents_off(measured_freq, note_freq):
    return 1200 * math.log2(measured_freq/note_freq)
    
def hz_off(cents, ref_freq):
   new_freq = 2**(cents/1200) * ref_freq
   return abs(ref_freq - new_freq)

def populate_notes(A):
    """Returns a tuple: A dict of all octaves of note names and their freqs, and an ordered list of note names.
    Input A is the frequency of A5.  Standard tuning is A=440."""
    # Populate octave 1 by adding 100 cents to each note, starting with A1 = A5 (ie 440) / 16.
    note_names = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']
    notes_oct1 = {'A': A / 16}
    for i in range(1, len(note_names)):
        prev_freq = notes_oct1[note_names[i-1]]
        notes_oct1[note_names[i]] = prev_freq + hz_off(100, prev_freq)
    # Populate octaves 2 - 8 by doubling notes in octave one each iteration. Ex use: notes[C#5] = 554.3648
    notes = {k + str(exp+1): v*(2**exp) for k, v in notes_oct1.items() for exp in range(8)}
    # An (ordered) list is used to fix the log vs absolute scale issue described in the freq_to_note func.
    notes_ordered_1 = sorted(list(notes_oct1.keys())) #No octave. ie: ['A', 'A#' ... 'G#']
    notes_ordered = [note + str(octave) for octave in range(1,9) for note in notes_ordered_1] # With octaves, in order low-hight.
    return(notes, notes_ordered)

notes, notes_ordered = populate_notes(440)[0], populate_notes(440)[1] # Perhaps change to not run the func twice.

def freq_to_note(freq):
    differences = {k: abs(v - freq) for k, v in notes.items()}
    nearest = min(differences, key=differences.get)
    # Could take min difference in cents instead of below code; current method may be faster due to
    # multiple subtraction calls instead of multiple log calls. Code below takes into account
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

FORMAT = pyaudio.paInt16
FS = 44100 # Sample rate
#chunk_time = CHUNK / FS
FPS = 10
CHUNK = 4096
NOISE_FLOOR = 0
PF_SIZE = 100
MIN_FREQ = 30
#Autocorrelation will sometimes give very low results when unable to detect the freq. FFT will often still be correct.
AUTOCORR_MIN = 60 
FREQ_AGREEMENT = .02 #Max threshhold for difference between measured autocorr and corrected FFT.

def read_stream(stream, size):
    sig_bin = stream.read(size)
    return np.array(struct.unpack('{0}h'.format(size), sig_bin))

def start(): #Make creating the stream and p not thread-specific? Pass it to each thread(s)?
    global past_freqs
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=1,
                    rate=FS,
                    input=True, 
                    frames_per_buffer=CHUNK)
                        
    global timer
    timer = QtCore.QTimer(interval=(1/FPS) * 1000)
    timer.timeout.connect(lambda: analysis(stream, p))
    past_freqs = np.array([]) #Set the size ahead of time, and alter that way instead of appending/slicing?
    timer.start()
    
def process_output(raw_freq):
    global past_freqs
    past_freqs = np.append(past_freqs, raw_freq) #matrix?
    if past_freqs.size > PF_SIZE:
        past_freqs = past_freqs[1:]
   # print("BEFORE:", past_freqs[-10:])
    pf_filtered = filter_output(past_freqs, 20) #weight this with a window weighted more to the right.
   # print("AFTER:", pf_filtered)
    
    
    #if pf_filtered.size < PF_SIZE/2:
    #    return raw_freq
    
    #smoothed1 = smooth3(pf_filtered, PF_SIZE/2)
    #smoothed2 = smoothListGaussian(pf_filtered, 3)
    '''
    if past_freqs.size >= PF_SIZE:
        plt.subplot(3,1,1)
        plt.plot(past_freqs)
        plt.title("Raw")
        plt.subplot(3,1,2)
        plt.plot(smoothed1)
        plt.title("smooth3")
        plt.subplot(3,1,3)
        plt.plot(smoothed2)
        plt.title("Gaussian")
      #  plt.show()
    '''
    
    return np.mean(pf_filtered) #weight this more  heavily towards the end. Ie a window function that does that? If you do it, increase window size.
    #return pf_filtered[-1]
    #return smoothed1[-1]

def filter_output(data, window_size):
    """Return the input, with outliers removed. Returns only values within a fixed distance
    of the most-occuring value-area."""
    window = data[-window_size:]
    min_dist = hz_off(10, window[-1])
    counts = []
    for j in range(len(window)):
        #k = len(matplotlib.mlab.find(np.abs(window - window[j]) <= min_dist))
        k = len(np.where(np.abs(window - window[j]) <= min_dist)[0])
        counts.append(k) #Instead of a list, change this to a numpy array; possibly just adding rows to k.
    mode = np.argmax(counts) # Index of the value with the most other values within min_dist of it.
    #mode_vals = matplotlib.mlab.find(np.abs(window-window[mode]) <= min_dist) # Values within min_dist of mode.
    mode_vals = np.where(np.abs(window-window[mode]) <= min_dist)[0] # Values within min_dist of mode.
    #avg = np.mean(window[mode_vals]) #possibly skip the averaging steps to make it faster
    '''
    if data.size == PF_SIZE+1000:
        plt.subplot(2,1,1)
        plt.plot(data)
        plt.subplot(2,1,2)
        plt.plot(data[mode_vals])
        plt.show()
    '''
    return window[mode_vals]

'''    
def smooth3(x,window_len=11,window='hanning'):
    if x.ndim != 1:
        raise ValueError("smooth only accepts 1 dimension arrays.")
    if x.size < window_len:
        raise ValueError("Input vector needs to be bigger than window size.")
    if window_len<3:
        return x
    if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
        raise ValueError("Window is on of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'")

    s=np.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
    #print(len(s))
    if window == 'flat': #moving average
        w=np.ones(window_len,'d')
    else:
        w=eval('np.'+window+'(window_len)')

    y=np.convolve(w/w.sum(),s,mode='valid')
    return y    
    
def smoothListGaussian(list,degree=3):  
    window=degree*2-1  
    weight=np.array([1.0]*window)  
    weightGauss=[]  
    for i in range(window):  
        i=i-degree+1  
        frac=i/float(window)  
        gauss=1/(np.exp((4*(frac))**2))  
        weightGauss.append(gauss)  
    weight=np.array(weightGauss)*weight  
    smoothed=[0.0]*(len(list)-window)  
    for i in range(len(smoothed)):  
        smoothed[i]=sum(np.array(list[i:i+window])*weight)/sum(weight)  
    return smoothed  
'''
    
def parabolic(f, x):
    """Quadratic interpolation for estimating the true position of an
    inter-sample maximum when nearby samples are known.
    f is a vector and x is an index for that vector.
    Returns (vx, vy), the coordinates of the vertex of a parabola that goes
    through point x and its two neighbors.
    Example:
    Defining a vector f with a local maximum at index 3 (= 6), find local
    maximum if points 2, 3, and 4 actually defined a parabola.
    In [3]: f = [2, 3, 1, 6, 4, 2, 3, 1]
    In [4]: parabolic(f, argmax(f))
    Out[4]: (3.2142857142857144, 6.1607142857142856)
    """
    xv = 1/2. * (f[x-1] - f[x+1]) / (f[x-1] - 2 * f[x] + f[x+1]) + x
    yv = f[x] - 1/4. * (f[x-1] - f[x+1]) * (xv - x)
    return (xv, yv)    
         
def fft(data):
    windowed = data * np.blackman(len(data))
    data_fft = np.fft.rfft(windowed)
    peak = np.argmax(abs(data_fft))
    true_i = parabolic(np.log(abs(data_fft)), peak)[0]
    return (FS * true_i / len(windowed), data_fft)

def autocorr(sig):
    # Scipy's FFT convolve may be faster, but trying to avoid scipy for distribution.
    corr = np.convolve(sig, sig[::-1])
    corr = corr[corr.size/2:] # The autocorrelation is symmetrical; we only need one half.
    d = np.diff(corr)
    try:
        #start = matplotlib.mlab.find(d > 0)[0]
        start = np.where(d > 0)[0][0]
    except IndexError: # Likely when a valid frequency cannot be found due to poor signal quality (or an unpitched signal?)
        return 0
    peak = np.argmax(corr[start:]) + start
    if peak == corr.size-1: # Prevents Indexerror, if the peak is the last value.
        return 0
    px, py = parabolic(corr, peak)
    return FS / px
   
def correct_fft(raw_fft, ref_freq):
    """Determines the fundamental of an FFT that may be returning a harmonic.  Relies on a reference freq.
    Assumes the tone being analyzed is harmonic."""
    i = np.arange(1,10)
    possible_funds = raw_fft / i
    return possible_funds[np.abs(possible_funds-ref_freq).argmin()]
   
def analysis(stream, p):
    """Main tuner analysis routine."""
    if not stop_flag: #Perhaps this flag is necessary instead of just killing the event loop due to the stream closing under the else statement.
        sig = read_stream(stream, CHUNK)
       # strobe(sig)
        freq_autocorr = autocorr(sig)
        freq_fft = fft(sig)[0]
        fft_corrected = correct_fft(freq_fft, freq_autocorr)
        print("AUTOCORR:", freq_autocorr)
        print("fft:", freq_fft)
        print("fft corrected:", fft_corrected) 
        if abs((fft_corrected-freq_autocorr) / freq_autocorr) < FREQ_AGREEMENT and\
            fft_corrected > MIN_FREQ:   # Check if FFT and autocorrelation agree.
            freq = process_output(fft_corrected)
        elif freq_autocorr < AUTOCORR_MIN < freq_fft: #tweak this as necessary. The bass seems to include cases like this where autcorr is wack.
            freq = process_output(freq_fft) #corrected fft can't be used if autocorr isn't working.
        else:
            freq = 0
        print("FREQ:", freq)       
        if freq:
            note = freq_to_note(freq)
            cents = cents_off(freq, notes[note])
            t.update(freq, note, cents)
    else:
        stream.stop_stream()
        stream.close()
        p.terminate()

t = Tuner()


'''


        
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
  
  
   
    #print(Y.size)
  
    #i = np.argmax(np.abs(Y)**2)
    
    #freq_mask = scipy.fftpack.fftfreq(Y.size)
    #freq = freq_mask[i] * CHANNELS
    #freq_in_hz = abs(freq * FS)
    #update(freq_in_hz)
    
    
    return line,
   
def init(line):
    # This data is a clear frame for animation
    line.set_ydata(np.zeros(CHUNK - 1))
    return line,
'''    
