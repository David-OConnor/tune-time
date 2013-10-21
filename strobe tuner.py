self.ui.strobe_display = StrobeDisplay()
self.ui.strobe_display.setGeometry(QtCore.QRect(1500, 1400, 1280, 450))
self.ui.strobe_display.show()


def strobe(data):
    """WIP""" #adjust for DC offset
    THRESH = .8
    min, max = np.amin(data), np.amax(data)
    min_thresh, max_thresh = min * THRESH, max * THRESH
    squared = np.copy(data)
    print(min, max, min_thresh, max_thresh)

    for j in range(squared.size):
        squared[j] = 1 if squared[j] > 0 else 0
    
    plt.subplot(2,1,1)
    plt.plot(data)
    plt.title("raw data")
    plt.subplot(2,1,2)
    plt.plot(squared)
    plt.title("square wavelets")
    plt.show()

#class StrobeDisplay(QtWidgets.QWidget):
class StrobeDisplay(QtOpenGL.QGLWidget):    
    rect_width = 40
    rect_start = 20
    x = 0
    num_rects = 1
    render_FPS = 200
    tick_FPS = 600
    strobe_on = True

    ref_freq = 1
    move_dist = 1280 * ref_freq / (render_FPS * num_rects) #1280 / ref_freq #1280 is substitute for width, which is showing 640 for some reason
    strobe_freq = 5
    strobe_duration = 5 #ms
    #current_rect = 0
    #rects = [i for i in range(num_rects)]
    rects = []
   
    def __init__(self, parent=None):
       # super(StrobeDisplay, self).__init__(parent)
        super(StrobeDisplay, self).__init__(QtOpenGL.QGLFormat(QtOpenGL.QGL.SampleBuffers), parent)
        
        self.w = self.size().width() * 2
        print(self.w)
        self.h = self.size().height()
        
        self.newrect_timer = QtCore.QTimer() #these probably need to be multithreaded
        self.newrect_timer.setTimerType(0) # This sets "precise" (ms) accuracy.
        self.newrect_timer.timeout.connect(self.new_rect)
        self.new_rect()
        self.newrect_timer.setInterval(1000 / self.ref_freq)
        #self.newrect_timer.start()
        
        self.animate_timer = QtCore.QTimer()
        self.animate_timer.timeout.connect(self.animate)
        self.animate_timer.setInterval(1000 / self.render_FPS)
       # self.animate_timer.start()
        self.elapsed = 0
 
        
    def new_rect(self):
        self.rects.append(StrobeRect(self.rect_width))
        self.update()        
    
    def strobe(self):
        print("strobe")
        #self.qp.drawRect(10,0, 1280, self.h)
        #self.qp.drawRect(200,20,4005,400)
        self.strobe_on = True
        time.sleep(4)
        self.strobe_on = False
        
    def animate(self):
        print("TEST2")
        self.elapsed = (self.elapsed + self.sender().interval()) % 1000
        if self.elapsed >= (1/self.ref_freq)*1000:
            self.new_rect()
            self.elapsed = 0
        
        
        print(self.elapsed)
     #   move_dist = 
        for rect in self.rects:
            rect.move(self.move_dist)
            #if rect.x > self.w / self.num_rects:
             #   self.new_rect()
            
            if rect.x > self.w: #probably would be safer not to use elif here
                self.rects.remove(rect)
        self.update()
        
        
    def paintEvent(self, event=None):
        self.qp = QtGui.QPainter()
        self.qp.begin(self)
        self.qp.setRenderHint(QtGui.QPainter.Antialiasing)
        self.qp.setBrush(QtCore.Qt.SolidPattern)
        
        for rect in self.rects:
            self.qp.drawRect(rect.x, 0, self.rect_width, self.h)
        if not self.strobe_on:
            self.qp.drawRect(20,20,1200,self.h)
        self.qp.end()
    
def strobe_timer():
    strobe_timer = QtCore.QTimer()
    strobe_timer.setTimerType(0) # This sets "precise" (ms) accuracy.
    strobe_timer.timeout.connect(strobe_instance.strobe_on)
    strobe_timer.setInterval(1000 / strobe_instance.strobe_freq)
    strobe_timer.start()
    
    
class StrobeRect:
    def __init__(self, width):
        self.width = width
        self.x = 0
        
    def move(self, distance):
        self.x += distance    

class StrobeThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self):
       # self.ui.strobe_display.strobe_timer.start()
        pass
        
class AnimateThread(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)

    def run(self):
        print("gTEST")
        self.animate_timer = QtCore.QTimer()
       # self.animate_timer.timeout.connect(main.ui.strobe_display.animate)
        self.animate_timer.timeout.connect(self.lol)
       # self.animate_timer.setInterval(1000 / main.ui.strobe_display.render_FPS)
        self.animate_timer.setInterval(1000)
        self.animate_timer.start()
        #self.ui.strobe_display.animate_timer.start()
    
    def lol(self):
        print("LOL")
 
        
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = Main()
    main.show()
    
    animate_instance = AnimateThread()
    animate_instance.start()
    strobe_instance = StrobeThread()    
    
    sys.exit(app.exec_())