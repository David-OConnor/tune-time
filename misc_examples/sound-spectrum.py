#!/usr/bin/env python
# Written by Yu-Jie Lin
# Public Domain
#
# Deps: PyAudio, NumPy, and Matplotlib
# Blog: http://blog.yjl.im/2012/11/frequency-spectrum-of-sound-using.html

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pyaudio
import struct
import wave



TITLE = ''
FPS = 25.0

CHUNK = 512
BUF_SIZE = 4 * CHUNK
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100


def animate(i, line, stream, wf, MAX_y):

  # Read n*CHUNK frames from stream, n > 0
  N = max(stream.get_read_available() / CHUNK, 1) * CHUNK
  data = stream.read(int(N))  #had to add int here to make it work. Possibly a python 3 issue.


  # Unpack data, LRLRLR...
  y = np.array(struct.unpack("%dh" % (N * CHANNELS), data)) / MAX_y
  y_L = y[::2]
  y_R = y[1::2]

  Y_L = np.fft.fft(y_L, CHUNK)
  Y_R = np.fft.fft(y_R, CHUNK)

  # Sewing FFT of two channels together, DC part uses right channel's
  Y = abs(np.hstack((Y_L[-CHUNK/2:-1], Y_R[:CHUNK/2])))

  line.set_ydata(Y)
  return line,


def init(line):

  # This data is a clear frame for animation
  line.set_ydata(np.zeros(CHUNK - 1))
  return line,


def main():
  
  fig = plt.figure()

  # Frequency range
  x_f = 1.0 * np.arange(-CHUNK / 2 + 1, CHUNK / 2) / CHUNK * RATE
  #ax = fig.add_subplot(111, title=TITLE, xlim=(x_f[0], x_f[-1]),
   #                    ylim=(0, 2 * np.pi * CHUNK**2 / RATE))
                       
  ax = fig.add_subplot(111, title=TITLE, xlim=(0, 6000),
                       ylim=(0, 2 * np.pi * CHUNK**2 / RATE))
  ax.set_yscale('symlog', linthreshy=CHUNK**0.5)
  
  fig.show()

  line, = ax.plot(x_f, np.zeros(CHUNK - 1))


  p = pyaudio.PyAudio()
  # Used for normalizing signal. If use paFloat32, then it's already -1..1.
  # Because of saving wave, paInt16 will be easier.
  MAX_y = 2.0**(p.get_sample_size(FORMAT) * 8 - 1)

  frames = None
  wf = None


  stream = p.open(format=FORMAT,
                  channels=CHANNELS,
                  rate=RATE,
                  input=True,
                  frames_per_buffer=BUF_SIZE)

  ani = animation.FuncAnimation(fig, animate, frames,
      init_func=lambda: init(line), fargs=(line, stream, wf, MAX_y),
      interval=1000.0/FPS, blit=True)

  plt.show()

  stream.stop_stream()
  stream.close()
  p.terminate()

    
if __name__ == '__main__':
  main()
