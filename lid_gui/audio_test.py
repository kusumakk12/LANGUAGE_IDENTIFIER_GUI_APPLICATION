import sys
import os
import time
import subprocess
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
from main import MainWindow
from audio_recorder import AudioRecorderDialog
import wave
import numpy as np
import threading
''' 1.To run this testcase ,audacity is needed to be installed in the system and modify the audacity_path with the path of audacity.exe on your system
2.the code asks for 2 file saves-(1st- save as test_recording.mp3),(2nd - save as audacity_recording.mp3))
# make sure to save these file to test the data/audio whether the spoken audio is recording acuurately or not '''

def test_audio_recording():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    recorder_dialog = AudioRecorderDialog()
    audacity_path = "C:\Program Files\Audacity\Audacity.exe"  
    def start_audacity_recording():
        audacity_script_path = "audacity_script.txt"
        with open(audacity_script_path, "w") as f:
            f.write("Select: Start\n")
            f.write("Wait: 10\n") 
            f.write("Select: Stop\n")
            f.write("ExportWav: audacity_recording.wav\n")
        audacity_process = subprocess.Popen([audacity_path, "--no-splash", "--no-plugins", "--batch", "--script", audacity_script_path])
    
    audacity_thread = threading.Thread(target=start_audacity_recording)
    audacity_thread.start()
    
    recorder_dialog.show()
    QTest.mouseClick(recorder_dialog.start_button, Qt.LeftButton)
    QTest.qWait(10000)
    QTest.mouseClick(recorder_dialog.stop_button, Qt.LeftButton)
    test_file_path = "test_recording.mp3"
    recorder_dialog.file_saved.emit(test_file_path)
    print(test_file_path)
    recorder_dialog.close()
    audacity_thread.join()
    assert os.path.exists(test_file_path), "Recorded file was not created"
    assert os.path.exists("audacity_recording.mp3"), "Audacity recording file was not created"
    compare_audio_files(test_file_path, "audacity_recording.mp3")
    os.remove(test_file_path)
    os.remove("audacity_recording.mp3")
    
    print("Audio recording test completed successfully")

def compare_audio_files(file1, file2):
    with wave.open(file1, 'rb') as wf1, wave.open(file2, 'rb') as wf2:
        assert wf1.getnchannels() == wf2.getnchannels(), "Channel count mismatch"
        assert wf1.getsampwidth() == wf2.getsampwidth(), "Sample width mismatch"
        assert wf1.getframerate() == wf2.getframerate(), "Frame rate mismatch"
        data1 = np.frombuffer(wf1.readframes(wf1.getnframes()), dtype=np.int16)
        data2 = np.frombuffer(wf2.readframes(wf2.getnframes()), dtype=np.int16)
        correlation = np.corrcoef(data1, data2)[0, 1]
        assert correlation > 0.9, f"Audio data correlation is too low: {correlation}"

if __name__ == "__main__":
    test_audio_recording()
