import pyaudio
import wave
import numpy as np
from PyQt5.QtGui import QCursor,QIcon
from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
import pyqtgraph as pg
from scipy.signal import butter, lfilter
import os

class AudioRecorderDialog(QDialog):
    file_saved = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.plot_widget=pg.PlotWidget()
        self.waveform_curve = self.plot_widget.plot(pen='b')
        #self.plot_widget.addItem(self.waveform_curve)
        self.setWindowTitle("Audio Recorder")
        self.setGeometry(200, 250, 500, 300)
        self.setStyleSheet("""
            QDialog { background-color: white; }
            QPushButton { 
                background-color: #4CAF50; 
                color: white; 
                border: none; 
                padding: 10px; 
                margin: 5px; 
                font-size: 16px; 
            }
            QPushButton:hover {
                background-color: #45a049;
                cursor: pointer;}
            QLabel { color: black; font-size: 18px; }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.is_paused = False

        micon_path = "C:/Users/Hp/AppData/Local/Programs/Python/Python311/Lib/site-packages/qt5_applications/Qt/projects/LID_GUI/gui/lid_gui/mic_icon.png"
        self.start_button = self.create_button(micon_path, self.start_recording)
        picon_path = "C:/Users/Hp/AppData/Local/Programs/Python/Python311/Lib/site-packages/qt5_applications/Qt/projects/LID_GUI/gui/lid_gui/pause_icon.png"
        self.pause_button = self.create_button(picon_path, self.toggle_pause)
        sicon_path = "C:/Users/Hp/AppData/Local/Programs/Python/Python311/Lib/site-packages/qt5_applications/Qt/projects/LID_GUI/gui/lid_gui/stop_icon.png"
        self.stop_button = self.create_button(sicon_path, self.stop_recording)

        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)

        self.time_label = QLabel("00:00:00")
        self.time_label.setAlignment(Qt.AlignCenter)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.waveform_curve = self.plot_widget.plot(pen='b')
        self.plot_widget.setLabel('left', 'Amplitude')
        self.plot_widget.setLabel('bottom', 'Time')
        self.plot_widget.setYRange(-32768, 32767)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.stop_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.time_label)
        main_layout.addWidget(self.plot_widget)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.recording_time = 0

        self.audio_data = np.array([], dtype=np.int16)
        self.window_size = 44100  
    def create_button(self, icon_path, callback):
        button = QPushButton()
        button.setFixedSize(100, 50)
        button.clicked.connect(callback)
        button.setCursor(QCursor(Qt.PointingHandCursor))
        button.setProperty("class", "recording-button")
        icon = QIcon(icon_path)
        button.setIcon(icon)
        button.setIconSize(button.size() * 0.8)  
        return button

    def update_button_states(self, recording=False):
        self.start_button.setEnabled(not recording)
        self.pause_button.setEnabled(recording)
        self.stop_button.setEnabled(recording)
        
        for button in [self.start_button, self.pause_button, self.stop_button]:
            if button.isEnabled():
                button.setCursor(QCursor(Qt.PointingHandCursor))

    def start_recording(self):
        self.stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, 
                                      frames_per_buffer=1024, stream_callback=self.audio_callback)
        self.frames = []
        self.audio_data = np.array([], dtype=np.int16)
        self.is_recording = True
        self.is_paused = False
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.update_button_states(recording=True)
        self.stream.start_stream()
        self.timer.start(20)  

    def audio_callback(self, in_data, frame_count, time_info, status):
        if not self.is_paused:
            self.frames.append(in_data)
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            self.audio_data = np.concatenate((self.audio_data, audio_data))
            '''if len(self.audio_data) > self.window_size:
                self.audio_data = self.audio_data[-self.window_size:]'''
            self.update_plot()
        return (in_data, pyaudio.paContinue)

    def update_plot(self):
        self.waveform_curve.setData(self.audio_data)
        self.plot_widget.setXRange(0, len(self.audio_data))

    def stop_recording(self):
        if self.is_recording:
            self.is_recording = False
            self.is_paused = False
            self.stream.stop_stream()
            self.stream.close()
            self.timer.stop()
            self.update_button_states(recording=False)

            reply = QMessageBox.question(self, 'Save Recording', 'Do you want to save the recording?',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                saved=self.save_audio()
            self.close()  
            #self.reset_ui()

    def reset_ui(self):
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.recording_time = 0
        self.time_label.setText("00:00:00")
        self.audio_data = np.array([], dtype=np.int16)
        self.waveform_curve.setData(self.audio_data)
        self.update_button_states(recording=False)

    def save_audio(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Audio", "recorded_audio.wav", "MP3 Files (*.mp3)")
        if file_name:
            wf = wave.open(file_name, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(44100)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            self.file_saved.emit(file_name)
            
    def toggle_pause(self):
        if self.is_recording:
            if not self.is_paused:
                self.is_paused = True
                self.timer.stop()
            else:
                self.is_paused = False
                self.timer.start(50)

    def update_timer(self):
        self.recording_time += 1
        hours, remainder = divmod(self.recording_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

def main():
    app = QApplication([])
    recorder_dialog = AudioRecorderDialog()
    recorder_dialog.show()
    app.exec_()


