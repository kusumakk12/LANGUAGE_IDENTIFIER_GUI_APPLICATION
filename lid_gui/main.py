from layout import Ui_MainWindow
import audio_recorder
import xlrd
import csv
import os
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton,
    QMenu, QFileDialog, QAction, QTextEdit,QDialog,QMessageBox , QSizePolicy,QComboBox,QWidget, QHBoxLayout, QLabel
)
from PyQt5.QtMultimedia import QAudioRecorder, QAudioEncoderSettings
from PyQt5.QtCore import QUrl, QDir
import pandas as pd
import threading
from threading import Timer
from PyQt5 import QtWidgets
import openpyxl
from PyQt5.QtCore import QObject,QThread,pyqtSlot
from PyQt5.QtCore import pyqtSignal as Signal
from PyQt5.QtCore import QThreadPool, QRunnable
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)



class MainWindow(QMainWindow, Ui_MainWindow):
    capacity=3
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.setStyleSheet(open("layout.qss", "r").read())
        self.add_plus_symbol()
        self.recordButton.clicked.connect(self.show_audio_recording_dialog)
        self.runButton.clicked.connect(self.run_button_clicked)
        self.stopButton.clicked.connect(self.stop_button_clicked)
        self.saveButton.clicked.connect(self.save_button_clicked)
        self.clearButton.clicked.connect(self.clear_button_clicked)
        self.clearfilesButton.clicked.connect(self.clearfiles_clicked)
        self.actionNew.triggered.connect(self.newWindow)
        self.actionOpen_File.triggered.connect(self.upload_file)
        self.actionOpen_Folder.triggered.connect(self.upload_folder)
        self.saveButton.setEnabled(False)
        self.clearButton.setEnabled(False)
        self.runButton.setEnabled(False)
        self.stopButton.setEnabled(False)
        self.clearfilesButton.setEnabled(False)

    def newWindow(self):
        window = MainWindow()
        self.windows = getattr(self, 'windows', []) + [window]
        window.show()
        window.raise_()        
    def show_audio_recording_dialog(self):
        self.statusbar.showMessage("recording")
        dialog = audio_recorder.AudioRecorderDialog()
        dialog.file_saved.connect(self.on_file_saved)
        dialog.exec_()
    def on_file_saved(self, filename):
        self.add_file_to_table([filename])
    global stop_insertion
    global timers
    timers=[]
    def populate_table(self):
        self.resultTable.setRowCount(0)
        self.resultTable2.setRowCount(0)
        global stop_insertion
        global timers
        timers=[]
        if stop_insertion:
            return

        data = pd.read_excel("LID_RESULT.xls")

        def insert_row(i):
            global stop_insertion 
            if i >= len(data) or stop_insertion:
                if i>=len(data):
                    self.saveButton.setEnabled(True)
                    self.clearButton.setEnabled(True)
                    self.runButton.setEnabled(True)
                    self.stopButton.setEnabled(False)
                    self.statusbar.showMessage("files processed")
                else:
                     self.statusbar.showMessage("processing has been stopped externally")
                return  
            if i <= len(data) and  stop_insertion==False:
                filename_item = QtWidgets.QTableWidgetItem(data.loc[i, 'Filename'])
                language_item1 = QtWidgets.QTableWidgetItem(data.loc[i, 'Language1'])
                confidence_item1= QtWidgets.QTableWidgetItem(str(data.loc[i, 'Confidence1']))
                self.resultTable.setRowCount(self.resultTable.rowCount() + 1)
                self.resultTable.setItem(i, 0, filename_item)
                self.resultTable.setItem(i, 1, language_item1)
                self.resultTable.setItem(i, 2, confidence_item1)
                self.resultTable.update()
                self.resultTable.scrollToBottom()
                filename_item = QtWidgets.QTableWidgetItem(data.loc[i, 'Filename'])
                language_item1 = QtWidgets.QTableWidgetItem(data.loc[i, 'Language1'])
                confidence_item1= QtWidgets.QTableWidgetItem(str(data.loc[i, 'Confidence1']))
                language_item2= QtWidgets.QTableWidgetItem(data.loc[i, 'Language2'])
                confidence_item2 = QtWidgets.QTableWidgetItem(str(data.loc[i, 'Confidence2']))
                self.resultTable2.setRowCount(self.resultTable2.rowCount() + 1)
                self.resultTable2.setItem(i, 0, filename_item)
                self.resultTable2.setItem(i, 1, language_item1)
                self.resultTable2.setItem(i, 2, confidence_item1)
                self.resultTable2.setItem(i, 3, language_item2)
                self.resultTable2.setItem(i, 4, confidence_item2)
                self.resultTable2.update()
                self.resultTable2.scrollToBottom()
                # Schedule next row insertion with 5 seconds delay
                timer = Timer(2.0, lambda: insert_row(i + 1))
                timer.start()
        timer=Timer(2.0,lambda:insert_row(0))
        timers.append(timer)
        timer.start()

    def run_button_clicked(self):
        global stop_insertion
        stop_insertion=False
        self.saveButton.setEnabled(False)
        self.recordButton.setEnabled(False)
        self.clearButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.runButton.setEnabled(False)
        if self.filesTable.rowCount()>1:
            self.statusbar.showMessage("files processing")
            timer = Timer(3.0, self.populate_table)
            timer.start()
        else:
            self.statusbar.showMessage("no files selected")

    def stop_button_clicked(self):
        self.saveButton.setEnabled(True)
        self.clearButton.setEnabled(True)
        self.runButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.recordButton.setEnabled(True)
        global stop_insertion
        print("stop_button_clicked")
        stop_insertion=True
        for timer in timers:
            timer.cancel()
        timers.clear()

        
    def clear_button_clicked(self):
        self.saveButton.setEnabled(False)
        self.clearButton.setEnabled(False)
        self.runButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.statusbar.showMessage("results have been cleared")
        self.resultTable.setRowCount(0)
        self.resultTable2.setRowCount(0)
        
    def save_to_csv(self, filename, table):
        try:
            with open(filename, 'w', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                header_row = []
                for col in range(table.columnCount()):
                    header_row.append(table.horizontalHeaderItem(col).text())
                csv_writer.writerow(header_row)
                for row in range(table.rowCount()):
                    data_row = []
                    for col in range(table.columnCount()):
                        item = table.item(row, col)
                        if item:
                            data_row.append(item.text())
                        else:
                            data_row.append("")  # Handle empty cells
                    csv_writer.writerow(data_row)
            return True 
        except Exception as e:
            print("Error", f"Failed to save file: {e}")
            self.statusbar.showMessage("Failed to save file", 2000)
            return False 

    

    def save_button_clicked(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        if self.resultTable.rowCount()>0:
             fileName, _ = QFileDialog.getSaveFileName(None, "Save Results", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
             if fileName:
                if self.save_to_csv(fileName, self.resultTable2):
                    print("successfully saved")
                    self.statusbar.showMessage("File saved successfully", 2000)
                else:
                    print("error not saved")
                    self.statusbar.showMessage("Failed to save file", 2000)
        else:
             self.statusbar.showMessage("no data to save")
    def clearfiles_clicked(self):  
        self.filesTable.setRowCount(0)
        self.add_plus_symbol()  

    def add_plus_symbol(self):
        row_position = self.filesTable.rowCount()
        self.filesTable.insertRow(row_position)
        self.spinner = QComboBox()
        self.spinner.setObjectName("spinner")
        self.spinner.addItem("select upload")
        self.spinner.addItem("Upload File")
        self.spinner.addItem("Upload Folder")
        self.spinner.setStyleSheet("""QComboBox{ 
	selection-color: rgb(170, 85, 255);
selection-background-color: rgb(170, 255, 255);
}""")
        self.spinner.currentTextChanged.connect(self.spinner_selected)
        self.filesTable.setCellWidget(row_position, 0, self.spinner) 
        if self.filesTable.rowCount()>self.capacity:
            self.spinner.setEnabled(False)

    def spinner_selected(self, text):
        if text == "Upload File":
            self.upload_file()
        elif text == "Upload Folder":
            self.upload_folder()
    def remove_plus_symbol(self):
        row_position = self.filesTable.rowCount()-1
        print(row_position)
        if row_position >= 0 :
            self.filesTable.removeCellWidget(row_position, 0)
            self.filesTable.removeRow(row_position)
            print("plus_button_removed")
    def upload_file(self):
        print("Upload file clicked")
        if self.filesTable.rowCount()<=self.capacity:
            file_name, _ = QFileDialog.getOpenFileName(None, "Upload File", filter="MP3 files (*.mp3);WAV fies(*.wav)")
            if file_name:
                self.add_file_to_table([file_name])

    def upload_folder(self):
        print("Upload folder clicked")
        if self.filesTable.rowCount()<=self.capacity:
            folder_name = QFileDialog.getExistingDirectory(None, "Upload Folder")
            if folder_name:
                file_paths = [
                    os.path.join(folder_name, f) for f in os.listdir(folder_name)
                    if os.path.isfile(os.path.join(folder_name, f)) and (f.lower().endswith('.mp3') or f.lower().endswith('.wav')) 
                ]
                non_mp3_files = [
                    f for f in os.listdir(folder_name)
                    if os.path.isfile(os.path.join(folder_name, f)) and not (f.lower().endswith('.mp3') or f.lower().endswith('.wav'))
               ]
                if non_mp3_files:
                    self.statusbar.showMessage(f"Selected folder '{os.path.basename(folder_name)}' has non-MP3 files which will not be processed: {', '.join(non_mp3_files)}")
                self.add_file_to_table(file_paths)
    
    def add_file_to_table(self, file_paths):
        existing_files = []
        for row in range(self.filesTable.rowCount()):
            cell_widget = self.filesTable.cellWidget(row, 0)
            if cell_widget:
                layout = cell_widget.layout()
                if layout:
                    label = layout.itemAt(0).widget()
                    if label:
                        existing_files.append(label.text().split(' (')[0])
        new_files = [file_path for file_path in file_paths if os.path.basename(file_path) not in existing_files]
        duplicate_files = [file_path for file_path in file_paths if os.path.basename(file_path) in existing_files]
        if duplicate_files:
            duplicate_names = ', '.join(os.path.basename(file_path) for file_path in duplicate_files)
            self.statusbar.showMessage(f"The following files are already uploaded: {duplicate_names}")
            QMessageBox.information(self, "Duplicate Files", f"The following files are already uploaded:\n{duplicate_names}")
        self.remove_plus_symbol()
        self.statusbar.showMessage(" ")
        for file_path in new_files:
            if self.filesTable.rowCount()<self.capacity:
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                row_position = self.filesTable.rowCount()
                self.filesTable.insertRow(row_position)
                layout = QHBoxLayout()
                layout.setContentsMargins(0,0,0,0)
                label = QLabel(f"{file_name} ({file_size} bytes)")
                label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                layout.setSpacing(0)
                delete_button = QPushButton("X")
                delete_button.setMinimumSize(20, 20)
                delete_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
                delete_button.setStyleSheet("""QPushButton{color:black;background-color:rgb(255, 115, 97);}
                                                               QPushButton:hover{color:red;background-color:white;border:2px solid red;}
                                                               QPushButton:focus{color:white;background-color:red;}""")
                delete_button.setFocusPolicy(QtCore.Qt.ClickFocus)
                delete_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                delete_button.clicked.connect(lambda checked, file_name=file_name: self.delete_file(file_name))
                layout.addWidget(label)
                layout.addWidget(delete_button)
                widget = QWidget()
                widget.setStyleSheet("QWidget { background-color: transparent; }")
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                widget.setLayout(layout)
                self.filesTable.setCellWidget(row_position, 0, widget)
            else:
                QMessageBox.information(self.centralwidget,"Information!", 'uploaded more files than the processing capacity for a time! only few files are uploaded',buttons=QMessageBox.Ok)
                break
        self.add_plus_symbol()
        if self.filesTable.rowCount() > 1:
             self.runButton.setEnabled(True)
             self.clearfilesButton.setEnabled(True)
        else:
             self.runButton.setEnabled(False)
             self.clearfilesButton.setEnabled(False)
  
    def delete_file(self, file_name):
        reply = QMessageBox.question(self.centralwidget, 'Delete File', 'Are you sure you want to delete this file?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            for row in range(self.filesTable.rowCount()):
                widget = self.filesTable.cellWidget(row, 0)
                layout = widget.layout()
                label = layout.itemAt(0).widget()
                file_label_text = label.text().split(' (')[0]
                if file_label_text == file_name:
                    self.filesTable.removeRow(row)
                    break
        if self.filesTable.rowCount()==self.capacity:
             self.spinner.setEnabled(True)
        
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
