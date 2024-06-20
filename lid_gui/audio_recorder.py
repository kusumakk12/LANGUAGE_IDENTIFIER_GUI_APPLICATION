import sys
import pyaudio
import numpy as np
from PyQt5.QtWidgets import QApplication, QDialog, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QFileDialog, QLabel,QMessageBox
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import QThread, pyqtSignal
import pyqtgraph as pg
import scipy.io.wavfile as wav
from scipy.signal import butter, lfilter
class AudioRecorderDialog(QDialog):
    file_saved = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Audio Recorder")
        self.setGeometry(100, 300, 500, 300)
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333333;
            }
        """)

        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()

        # Create widgets
        self.start_button = QPushButton("Start Recording")
        self.stop_button = QPushButton("Stop Recording")
        self.stop_button.setEnabled(False)
        self.message_label = QLabel("Ready")

        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.pitch_curve = self.plot_widget.plot(pen='r')
        self.plot_widget.setVisible(False)

        # Create layouts
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.message_label)
        main_layout.addWidget(self.plot_widget)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # Connect button signals
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        

        self.stream = None
        self.pitch_thread = None
        self.recorded_data = []

    # The rest of the code remains the same as in the original AudioRecorder class



    def start_recording(self):
        # Open audio stream
        self.stream = self.audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        self.recorded_data = []

        # Update button and widget states
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.message_label.setText("Recording...")
        self.plot_widget.setVisible(True)

        # Start pitch visualization thread
        self.pitch_thread = PitchVisualizationThread(self.stream, self.pitch_curve, self.recorded_data)
        self.pitch_thread.data_ready.connect(self.update_plot)
        self.pitch_thread.start()

        print("Recording started...")

    def update_plot(self, data):
        self.pitch_curve.setData(data)

    def stop_recording(self):
        # Stop pitch visualization thread
        self.pitch_thread.stop()
        self.pitch_thread.wait()

        # Stop audio stream
        self.stream.stop_stream()
        self.stream.close()
        self.save_audio()

        # Update button and widget states
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.message_label.setText("Recording stopped.")
        self.plot_widget.setVisible(False)

        print("Recording stopped.")

    def save_audio(self):
         reply = QMessageBox.question(self, 'Save File', 'Are you sure you want to save the file?',
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
         if reply == QMessageBox.Yes:
             self.accept()
             # Open file dialog to choose save location
             file_name, _ = QFileDialog.getSaveFileName(self, "Save Audio", "recorded_audio.wav", "WAV Files (*.wav)")
             if file_name:
                # Save recorded audio to the chosen file
                recorded_data = np.array(self.recorded_data, dtype=np.int16)
                wav.write(file_name, 44100, recorded_data)
                # Reset recorded data and disable save button
                self.recorded_data = []
                print(f"Audio saved to {file_name}")
                self.message_label.setText("Audio saved.")
                self.file_saved.emit(file_name)
         else:
               self.accept()
               print("not saved")

class PitchVisualizationThread(QThread):
    data_ready = pyqtSignal(np.ndarray)

    def __init__(self, audio_stream, pitch_curve, recorded_data):
        super().__init__()
        self.audio_stream = audio_stream
        self.pitch_curve = pitch_curve
        self.recorded_data = recorded_data
        self.running = True

    def run(self):
        while self.running:
            data = self.audio_stream.read(1024)
            data = np.frombuffer(data, dtype=np.int16)
            self.recorded_data.extend(data)
            pitch_data = self.extract_pitch(data)
            self.data_ready.emit(pitch_data)

    def extract_pitch(self, data):
        # Apply a low-pass filter to remove high-frequency noise
        nyquist_freq = 44100 / 2
        cutoff_freq = 1000  # Set the cutoff frequency as desired
        order = 4
        norm_cutoff = cutoff_freq / nyquist_freq
        b, a = butter(order, norm_cutoff, btype='low', analog=False)
        filtered_data = lfilter(b, a, data)

        # Calculate the pitch data
        pitch_data = np.abs(np.fft.rfft(filtered_data))[:len(filtered_data) // 2]

        return pitch_data

    def stop(self):
        self.running = False
def main():
    app = QApplication(sys.argv)
    recorder_dialog = AudioRecorderDialog()
    recorder_dialog.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
