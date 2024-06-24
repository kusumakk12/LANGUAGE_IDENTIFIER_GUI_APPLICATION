import pyaudio
import wave
import numpy as np
from PyQt5.QtGui import QCursor, QIcon
from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox, QFileDialog
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
import pyqtgraph as pg
from scipy.signal import butter, lfilter
import os

class AudioRecorderThread(QThread):
    update_plot = pyqtSignal(np.ndarray)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.is_paused = False

    def run(self):
        self.stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, 
                                      frames_per_buffer=1024, stream_callback=self.audio_callback)
        self.stream.start_stream()
        self.is_recording = True
        while self.is_recording:
            self.sleep(1)
        self.stop_recording()

    def audio_callback(self, in_data, frame_count, time_info, status):
        if not self.is_paused:
            self.frames.append(in_data)
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            self.update_plot.emit(audio_data)
        return (in_data, pyaudio.paContinue)

    def stop_recording(self):
        self.is_recording = False
        self.stream.stop_stream()
        self.stream.close()

class AudioRecorderDialog(QDialog):
    file_saved = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.audio_thread = AudioRecorderThread()
        self.audio_thread.update_plot.connect(self.update_plot)
        self.audio_data = np.array([], dtype=np.int16)
        self.total_samples = 0
        self.max_display_samples = 44100 * 200  

    def setup_ui(self):
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
            QPushButton:hover { background-color: #45a049; }
            QLabel { color: black; font-size: 18px; }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)

        self.time_label = QLabel("00:00:00")
        self.time_label.setAlignment(Qt.AlignCenter)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.waveform_curve = self.plot_widget.plot(pen='b')
        self.plot_widget.setLabel('left', 'Amplitude')
        self.plot_widget.setLabel('bottom', 'Time (s)')
        self.plot_widget.setYRange(-32768, 32767)

        micon_path = "/home/projectstudent/Desktop/gui/Icons/record.png"
        self.start_button = self.create_button(micon_path, self.start_recording)
        picon_path = "/home/projectstudent/Desktop/gui/Icons/pause.png"
        self.pause_button = self.create_button(picon_path, self.toggle_pause)
        sicon_path = "/home/projectstudent/Desktop/gui/Icons/stop.png"
        self.stop_button = self.create_button(sicon_path, self.stop_recording_confirmation)

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

        self.update_button_states(recording=False)

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
            else:
                button.setCursor(QCursor(Qt.ArrowCursor))

    def start_recording(self):
        if not self.audio_thread.isRunning():
            self.audio_thread.start()
        else:
            self.audio_thread.is_recording = True
        self.is_paused = False
        self.update_button_states(recording=True)
        self.timer.start(20)
        self.total_samples = 0
        self.audio_data = np.array([], dtype=np.int16)
        self.plot_widget.setXRange(0, 1) 

    def update_plot(self, new_data):
        self.audio_data = np.concatenate((self.audio_data, new_data))
        self.total_samples += len(new_data)
        if len(self.audio_data) > self.max_display_samples:
            self.audio_data = self.audio_data[-self.max_display_samples:]
        
        time_axis = np.linspace(0, len(self.audio_data) / 44100, len(self.audio_data))
        self.waveform_curve.setData(time_axis, self.audio_data)
        max_time = min(self.total_samples / 44100, 10)
        self.plot_widget.setXRange(0, max_time)
        self.plot_widget.setLabel('bottom', f'Time (s) - Current: {self.total_samples / 44100:.2f}s')

    def stop_recording_confirmation(self):
        self.audio_thread.is_recording = False
        self.audio_thread.wait()  
        reply = QMessageBox.question(self, 'Save Recording', 'Do you want to save the recording?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.save_audio()
        self.reset_ui()

    def save_audio(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Audio", "recorded_audio.mp3", "MP3 Files (*.mp3)")
        if file_name:
            wf = wave.open(file_name, 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(self.audio_thread.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(44100)
            wf.writeframes(b''.join(self.audio_thread.frames))
            wf.close()
            self.file_saved.emit(file_name)

    def reset_ui(self):
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.recording_time = 0
        self.time_label.setText("00:00:00")
        self.audio_data = np.array([], dtype=np.int16)
        self.total_samples = 0
        self.waveform_curve.setData([], [])
        self.plot_widget.setXRange(0, 1)  
        self.plot_widget.setLabel('bottom', 'Time (s)')
        self.update_button_states(recording=False)

    def toggle_pause(self):
        if self.audio_thread.is_recording:
            self.audio_thread.is_paused = not self.audio_thread.is_paused
            if self.audio_thread.is_paused:
                self.timer.stop()
            else:
                self.timer.start(20)

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
