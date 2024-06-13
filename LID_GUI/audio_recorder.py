# audio_recorder.py
import sys
import pyaudio
import wave
import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QFileDialog, QLineEdit, QHBoxLayout, QWidget
from PyQt5.QtCore import QThread, pyqtSignal
from pydub import AudioSegment

class AudioRecorderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Audio Recorder')
        self.setGeometry(300, 300, 400, 250)
        
        self.audio_recorder = AudioRecorder()
        
        layout = QVBoxLayout()
        layout.addWidget(self.audio_recorder)
        self.setLayout(layout)

class AudioRecorder(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle('Audio Recorder')
        self.setGeometry(100, 100, 400, 200)
        
        self.record_button = QPushButton('Start Recording', self)
        self.stop_button = QPushButton('Stop Recording', self)
        self.save_button = QPushButton('Save as WAV', self)
        self.status_label = QLabel('Status: Ready', self)
        self.filename_label = QLabel('Filename:', self)
        self.filename_edit = QLineEdit(self)
        
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.record_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addWidget(self.save_button)
        
        layout = QVBoxLayout()
        layout.addWidget(self.filename_label)
        layout.addWidget(self.filename_edit)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.status_label)
        self.setLayout(layout)
        
        self.record_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        self.save_button.clicked.connect(self.save_as_wav)
        
        self.audio_thread = None
        self.temp_wav_filename = "output.wav"
        
    def start_recording(self):
        filename = self.filename_edit.text().strip()
        if not filename:
            self.status_label.setText('Status: Please enter a filename.')
            return
        
        self.audio_thread = AudioThread(filename)
        self.audio_thread.finished.connect(self.recording_finished)
        self.audio_thread.start()
        self.status_label.setText('Status: Recording...')
        
    def stop_recording(self):
        if self.audio_thread and self.audio_thread.isRunning():
            self.audio_thread.stop_recording()
            self.status_label.setText('Status: Stopping...')
        
    def save_as_wav(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setNameFilter("WAV files (*.wav)")
        file_dialog.setDefaultSuffix("wav")
        if file_dialog.exec_():
            save_path = file_dialog.selectedFiles()[0]
            try:
                os.rename(self.temp_wav_filename, save_path)
                self.status_label.setText(f'Status: WAV saved as {save_path}')
            except Exception as e:
                self.status_label.setText(f"Error: {e}")
        
    def recording_finished(self):
        self.status_label.setText('Status: Finished')

class AudioThread(QThread):
    finished = pyqtSignal()
    
    def __init__(self, filename):
        super().__init__()
        self.filename = filename
        self.is_recording = False
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.CHUNK = 1024
        self.frames = []
    
    def run(self):
        self.is_recording = True
        self.frames = []
        audio = pyaudio.PyAudio()
        
        stream = audio.open(format=self.FORMAT,
                            channels=self.CHANNELS,
                            rate=self.RATE,
                            input=True,
                            frames_per_buffer=self.CHUNK)

        while self.is_recording:
            data = stream.read(self.CHUNK)
            self.frames.append(data)

        stream.stop_stream()
        stream.close()
        audio.terminate()

        # Save the recorded data as a WAV file
        with wave.open("output.wav", 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(self.frames))
        
        self.finished.emit()
    
    def stop_recording(self):
        self.is_recording = False

def call():
    app = QApplication(sys.argv)
    recorder = AudioRecorderDialog()
    recorder.exec_()
