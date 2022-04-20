import sys
import qdarkstyle
from PyQt5.QtWidgets import (QWidget, QPushButton, QApplication, QCheckBox,
                             QTableWidget, QTableWidgetItem, QHBoxLayout, QVBoxLayout, QLineEdit,QLabel, QComboBox)
import PyQt5.QtCore as qc
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

import numpy as np
import mutils, wavio, os


class PyQtLayout(QWidget):
    """
    Main layout widget class.

    ...

    Attributes
    ----------
    current_wave : str
        file name for most recently saved .wav file
    max_dur : int
        current maximum wave duration entered by the user. kept up to date and used for padding shorter waves so everything adds nicely.
    wave_objects : list[mutils.WaveInfo]
        list of WaveInfo objects, each representing a wave the user has added.
    rate: int
        sample rate for generating waves.
    """
    def __init__(self):
        """
        Runs initialization of the main layout widget, and sets up some variables that we'll use throughout.
        """
        super().__init__()
        #Used for input fields
        self.fieldNames = ['Freq', 'Duration', 'Amplitude']
        self.lineFields = {}

        #Wave related setup.
        self.current_wave = ""
        self.max_dur = 3
        self.wave_objects = []
        self.rate = 44100
        self.plot_all = False
        
        #get directory we can write to, create if not present
        self.wavedir = mutils.get_datadir()
        try: 
            self.wavedir.mkdir() 
        except FileExistsError: 
            pass
        
        #Widget instantiation for 
        self.waveTable = QTableWidget()
        self.canvas = MplCanvas(self, width=5, height=6, dpi=100)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.player = QMediaPlayer()

        self.UI()

    def play_audio_file(self):
        """
        Plays the most recently generated .wav file. Called when the user clicks on either play or add_wave buttons. 
        """
        url = qc.QUrl.fromLocalFile(str(self.current_wave))
        content = QMediaContent(url)

        self.player.setMedia(content)
        self.player.setVolume(15)
        self.player.play()
    
    def clear_wave_files(self):
        """
        Deletes wave files and clears everything else.
        """
        files = self.wavedir.glob("*.wav")
        try:
            for f in files:
                os.remove(f)
        except OSError as e:
            print(e)
        finally:
            self.wave_objects = []
            self.update_plot()
            self.tableSetup()

    def update_plot(self):
        """
        Updates the two plots.
        """

        # clear axes for both subplots and reset some params
        self.canvas.axes.cla()
        self.canvas.axes_fft.cla()
        self.canvas.setAxParams()

        # check to see if the user has added any waves
        if self.wave_objects:
            # creates the t array, evenly spaced values going from 0 to self.max_dur. Total number of values generated is max_dur*rate
            max_t = np.linspace(0, self.max_dur, self.max_dur*self.rate, endpoint=False)
            #set up a 0 vector of appropriate length, wave accumulator
            final_vec = 0 * max_t
            for v in self.wave_objects:
                # generates the wave from the params of the current WaveInfo object 
                current = v.gen_wave(self.rate)

                #if the current wave is shorter than the accumulator, pad it on the right with 0's
                #we don't check the other case as final_vec is built using the maximum duration of all present WaveInfo objects
                if (current.shape[0]<final_vec.shape[0]):
                    current = np.pad(current, (0, final_vec.shape[0]-current.shape[0]))
                if (self.plot_all):
                    self.canvas.axes.plot(max_t, current)
                #add to running total
                final_vec += current
            #plot the wave
            self.canvas.axes.plot(max_t, final_vec)

            #plot the frequency content
            x,y = mutils.get_fft(self.rate, final_vec)
            self.canvas.axes_fft.plot(x, y)
            
            #save the file and play it
            file_end = "wave_sum_{}.wav".format(str(len(self.wave_objects)))
            self.current_wave = self.wavedir / file_end
            try:
                wavio.write(str(self.current_wave), final_vec, self.rate, sampwidth=3)
            except OSError as e:
                print(e)
                pass
            self.play_audio_file()
        #redraw the plots
        self.canvas.draw()
    
    def plot_all_toggle(self):
        cbutton = self.sender()
        self.plot_all = cbutton.isChecked()
        self.update_plot()
 
    def UI(self):
        """
        Sets up everything for the main UI.
        """

        #set up wave, clear, and play buttons
        add_button = QPushButton('Add Wave', clicked=self.addWave)
        clear_button = QPushButton('Reset',clicked=self.clear_wave_files)
        play_button = QPushButton('Play', clicked=self.play_audio_file)
        plot_all_radio = QCheckBox('Plot all waves')
        plot_all_radio.toggled.connect(self.plot_all_toggle)
        #horizontal box for plot area and table
        figs_and_data_hbox = QHBoxLayout()
        #vertical box to put both the plot toolbar and plot canvas 
        figs_and_toolbar_vbox = QVBoxLayout()

        #main layout is this vbox. everything in the end gets added to this
        vbox = QVBoxLayout()

        #create input fields and put them in hbox
        hbox = QHBoxLayout()
        for i in self.fieldNames:
            hbox.addLayout(self.addLineEditField(i))
        
        #combo selector for wave shape, combo_container gets the dropdown and label, then added to hbox
        combo = QComboBox()
        combo.addItems(['sine', 'sawtooth', 'square', 'triangle'])
        combo_container = QVBoxLayout()
        dropdownName = QLabel()
        dropdownName.setText("Wave Shape")
        dropdownName.adjustSize()
        combo_container.addWidget(dropdownName)
        combo_container.addWidget(combo)
        self.lineFields['waveshape'] = combo
        hbox.addLayout(combo_container)
        
        hbox.addWidget(add_button)
        hbox.addWidget(plot_all_radio)
        vbox.addLayout(hbox)
        vbox.addWidget(clear_button)
        
        figs_and_toolbar_vbox.addWidget(self.toolbar)
        figs_and_toolbar_vbox.addWidget(self.canvas)
        figs_and_data_hbox.addLayout(figs_and_toolbar_vbox)
        figs_and_data_hbox.addWidget(self.waveTable, alignment=qc.Qt.AlignCenter)
        
        vbox.addLayout(figs_and_data_hbox)
        vbox.addWidget(play_button)
        
        self.setLayout(vbox)
        self.setGeometry(0,0,1920, 1080)
        self.setWindowTitle('Wave Playground')
        
        
        self.show()

    def addLineEditField(self, fieldName):
        retBox = QVBoxLayout()
        nameField = QLabel()
        nameField.setText(fieldName)
        nameField.adjustSize()
        lineWidget = QLineEdit()
        retBox.addWidget(nameField)
        retBox.addWidget(lineWidget)
        self.lineFields[fieldName] = lineWidget
        return retBox

    def addWave(self):
        try:
            frequency = float(eval(self.lineFields['Freq'].text()))
            duration = int(self.lineFields['Duration'].text())
            shape = self.lineFields['waveshape'].currentText()
            amplitude = float(eval(self.lineFields['Amplitude'].text()))
        except:
            return
        if (duration > self.max_dur):
            self.max_dur = duration
        
        self.wave_objects.append(mutils.WaveInfo(shape, duration, frequency, amplitude))
        
        self.update_plot()
        self.tableSetup()

    def tableSetup(self):
        nrows = len(self.wave_objects)
        self.waveTable.setRowCount(nrows)
        self.waveTable.setColumnCount(4)
        tmp_data = {}
        
        for i in ['shape', 'duration', 'freq', 'amplitude']:
            tmp_data[i] = [w_obj.get_kv_dict()[i] for w_obj in self.wave_objects]
        horHeaders = []
        for n, key in enumerate(sorted(tmp_data.keys())):
            horHeaders.append(key)
            for m, item in enumerate(tmp_data[key]):
                newitem = QTableWidgetItem(str(item))
                self.waveTable.setItem(m, n, newitem)
        self.waveTable.setHorizontalHeaderLabels(horHeaders)
        self.waveTable.resizeColumnsToContents()
        self.waveTable.resizeRowsToContents()
        

        


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(211)
        self.axes_fft = self.fig.add_subplot(212)
        self.setAxParams()
        super(MplCanvas, self).__init__(self.fig)

    def setAxParams(self):
        self.axes.set_ylim(-2, 2)
        self.axes.set_xlim(0,0.025)
        self.axes.set_title("Current Wave")
        self.axes.set_ylabel("Level")
        self.axes.set_xlabel("Time (seconds)")
        self.axes_fft.set_title("Frequency Content")
        self.axes_fft.set_ylabel("Vol")
        self.axes_fft.set_xlabel("Frequency")
    

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    ex = PyQtLayout()
    sys.exit(app.exec_())
 
if __name__ == '__main__':
    main()