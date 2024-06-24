from layout import Ui_MainWindow
import audio_recorder
import csv,os,sys,xlrd,openpyxl
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton,
    QMenu, QFileDialog, QAction, QTextEdit,QDialog,QMessageBox , QSizePolicy,QComboBox,QWidget, QHBoxLayout, QLabel,QVBoxLayout
)
import pandas as pd
from threading import Timer
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QObject,QThread,pyqtSlot,QUrl, QDir,Qt, QTimer
from PyQt5.QtCore import pyqtSignal as Signal
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

class MainWindow(QMainWindow, Ui_MainWindow):
    capacity=3
    notification_signal = Signal(str)
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.add_plus_symbol()
        self.resetButton.clicked.connect(self.reset_window)
        self.uploadButton.clicked.connect(self.showUploadDialog)
        self.recordButton.clicked.connect(self.show_audio_recording_dialog)
        self.runButton.clicked.connect(self.run_button_clicked)
        self.stopButton.clicked.connect(self.stop_button_clicked)
        self.saveButton.clicked.connect(self.save_button_clicked)
        self.clearButton_2.clicked.connect(self.clear_button_clicked)
        self.clearButton.clicked.connect(self.clearfiles_clicked)
        self.newButton.clicked.connect(self.newWindow)
        self.newButton_2.clicked.connect(self.newWindow)
        self.resultsTable.cellClicked.connect(lambda row,column:self.on_resultsTable_cell_clicked(row,column))
        self.resultsTable_2.cellClicked.connect(lambda row,column:self.on_resultsTable_2_cell_clicked(row,column))
        self.saveButton.setEnabled(False)
        self.clearButton_2.setEnabled(False)
        self.runButton.setEnabled(False)
        self.stopButton.setEnabled(False)
        self.clearButton.setEnabled(False)
        self.clearButton_2.setEnabled(False)
        self.notification_signal.connect(self.show_notification)
    

    def newWindow(self):
        window = MainWindow()
        self.windows = getattr(self, 'windows', []) + [window]
        window.show()
        window.raise_()        
    def show_audio_recording_dialog(self):
        self.notification_signal.emit("Recorder on")
        dialog = audio_recorder.AudioRecorderDialog()
        dialog.raise_()
        dialog.file_saved.connect(self.on_file_saved)
        dialog.exec_()
    def on_file_saved(self, filename):
        self.add_file_to_table([filename])
    global stop_insertion
    global timers
    global timer
    timers=[]
    def populate_table(self):
        self.resultsTable.setRowCount(0)
        self.resultsTable_2.setRowCount(0)
        global stop_insertion
        stop_insertion= False
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
                    self.notification_signal.emit("Files processed")
                    self.statusbar.showMessage("Files processed")
                else:
                     self.notification_signal.emit("Processing stopped")
                     self.statusbar.showMessage("processing has been stopped externally")
                return  
            if i <= len(data) and  stop_insertion==False:
                filename_item = QtWidgets.QTableWidgetItem(data.loc[i, 'Filename'])
                language_item1 = QtWidgets.QTableWidgetItem(data.loc[i, 'Language1'])
                confidence_item1= QtWidgets.QTableWidgetItem(str(data.loc[i, 'Confidence1']))
                self.resultsTable.setRowCount(self.resultsTable.rowCount() + 1)
                self.resultsTable.setItem(i, 0, filename_item)
                self.resultsTable.setItem(i, 1, language_item1)
                self.resultsTable.setItem(i, 2, confidence_item1)
                self.resultsTable.update()
                self.resultsTable.scrollToBottom()
                filename_item = QtWidgets.QTableWidgetItem(data.loc[i, 'Filename'])
                language_item1 = QtWidgets.QTableWidgetItem(data.loc[i, 'Language1'])
                confidence_item1= QtWidgets.QTableWidgetItem(str(data.loc[i, 'Confidence1']))
                language_item2= QtWidgets.QTableWidgetItem(data.loc[i, 'Language2'])
                confidence_item2 = QtWidgets.QTableWidgetItem(str(data.loc[i, 'Confidence2']))
                self.resultsTable_2.setRowCount(self.resultsTable_2.rowCount() + 1)
                self.resultsTable_2.setItem(i, 0, filename_item)
                self.resultsTable_2.setItem(i, 1, language_item1)
                self.resultsTable_2.setItem(i, 2, confidence_item1)
                self.resultsTable_2.setItem(i, 3, language_item2)
                self.resultsTable_2.setItem(i, 4, confidence_item2)
                self.resultsTable_2.update()
                self.resultsTable_2.scrollToBottom()
                timer = Timer(2.0, lambda: insert_row(i + 1))
                timer.start()
        timer=Timer(2.0,lambda:insert_row(0))
        timers.append(timer)
        timer.start()

    def run_button_clicked(self):
        global stop_insertion
        global timer
        stop_insertion=False
        self.saveButton.setEnabled(False)
        self.recordButton.setEnabled(False)
        self.clearButton_2.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.runButton.setEnabled(False)
        if self.filestable.rowCount()>1:
            timer = Timer(3.0, self.populate_table)
            timer.start()
        else:
            QMessageBox.warning(None, "WARNING!", "FILES NOT SELECTED")
            

    def stop_button_clicked(self):
        global timer
        self.runButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.recordButton.setEnabled(True)
        global stop_insertion
        stop_insertion=True
        timer.cancel()
        timers.clear()
        if self.resultsTable.rowCount()!=0:
            self.saveButton.setEnabled(True)
            self.clearButton_2.setEnabled(True)
        
    def clear_button_clicked(self):
        self.saveButton.setEnabled(False)
        self.clearButton_2.setEnabled(False)
        self.runButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.statusbar.showMessage("results have been cleared")
        self.resultsTable.setRowCount(0)
        self.resultsTable_2.setRowCount(0)
        
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
                    csv_writer.writerow(data_row)
            return True 
        except Exception as e:
            QMessageBox.critical(None, "Failed to save file", str(e))
            return False 

    def save_button_clicked(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        if self.resultsTable.rowCount()>0:
             fileName, _ = QFileDialog.getSaveFileName(None, "Save Results", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
             if fileName:
                if self.save_to_csv(fileName, self.resultsTable_2):
                    self.notification_signal.emit("Data saved successfully")
                    self.statusbar.showMessage("File saved successfully", 2000)
                else:
                    QMessageBox.critical(None, "Failed to save file", str(e))
                    self.statusbar.showMessage("Failed to save file", 2000)
        else:
             QMessageBox.critical(None, "Failed to save file", 'no data to save')
             self.statusbar.showMessage("no data to save")

    def clearfiles_clicked(self):  
        self.filestable.setRowCount(0)
        self.notification_signal.emit("selected Files cleared")
        self.add_plus_symbol()  

    def add_plus_symbol(self):
        row_position = self.filestable.rowCount()
        self.filestable.insertRow(row_position)
        self.spinner = QComboBox()
        self.spinner.setObjectName("spinner")
        font =QFont("Arial", 12)  
        self.spinner.setFont(font)
        self.spinner.addItem("select upload")
        self.spinner.addItem("Upload File")
        self.spinner.addItem("Upload Folder")
        self.spinner.setStyleSheet("""QComboBox{ 
	selection-color: rgb(170, 85, 255);
selection-background-color: rgb(170, 255, 255);
}""")
        self.spinner.currentTextChanged.connect(self.spinner_selected)
        self.filestable.setCellWidget(row_position, 0, self.spinner) 
        if self.filestable.rowCount()>self.capacity:
            self.spinner.setEnabled(False)

    def spinner_selected(self, text):
        if text == "Upload File":
            self.upload_file()
        elif text == "Upload Folder":
            self.upload_folder()
    def remove_plus_symbol(self):
        row_position = self.filestable.rowCount()-1
        if row_position >= 0 :
            self.filestable.removeCellWidget(row_position, 0)
            self.filestable.removeRow(row_position)
    def upload_file(self):
        if self.filestable.rowCount()<=self.capacity:
            file_name, _ = QFileDialog.getOpenFileName(None, "Upload File", filter="Audio files (*.mp3 *.wav);;MP3 files (*.mp3);;WAV files (*.wav);;All files (*.*)")
            if file_name:
                self.add_file_to_table([file_name])

    def upload_folder(self):
        if self.filestable.rowCount()<=self.capacity:
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
                    not_saved_files=f"Selected folder '{os.path.basename(folder_name)}' has non-MP3 files which will not be processed: {', '.join(non_mp3_files)}"
                    QMessageBox.warning(None, "Non Mp3 files", not_saved_files)
                    self.statusbar.showMessage(not_saved_files)
                self.add_file_to_table(file_paths)
    
    def add_file_to_table(self, file_paths):
        existing_files = []
        for row in range(self.filestable.rowCount()):
            cell_widget = self.filestable.cellWidget(row, 0)
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

        for file_path in new_files:
            if self.filestable.rowCount()<self.capacity:
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                row_position = self.filestable.rowCount()
                self.filestable.insertRow(row_position)
                layout = QHBoxLayout()
                layout.setContentsMargins(0,0,0,0)
                label = QLabel(f"{file_name} ({file_size} bytes)")
                font = QFont()
                font.setPointSize(12) 
                label.setFont(font)
                label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                layout.setSpacing(0)
                delete_button = QPushButton("X")
                delete_button.setFixedSize(20, 20)
                delete_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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
                self.filestable.setCellWidget(row_position, 0, widget)
            else:
                QMessageBox.information(self.centralwidget,"Information!", 'uploaded more files than the processing capacity for a time! only few files are uploaded',buttons=QMessageBox.Ok)
                break
        self.add_plus_symbol()
        if self.filestable.rowCount() > 1:
             self.runButton.setEnabled(True)
             self.clearButton.setEnabled(True)
        else:
             self.runButton.setEnabled(False)
             self.clearButton.setEnabled(False)
  
    def delete_file(self, file_name):
        reply = QMessageBox.question(self.centralwidget, 'Delete File', 'Are you sure you want to delete this file?',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            for row in range(self.filestable.rowCount()):
                widget = self.filestable.cellWidget(row, 0)
                layout = widget.layout()
                label = layout.itemAt(0).widget()
                file_label_text = label.text().split(' (')[0]
                if file_label_text == file_name:
                    self.filestable.removeRow(row)
                    break
        if self.filestable.rowCount()==self.capacity:
             self.spinner.setEnabled(True)
    def on_resultsTable_cell_clicked(self, row,column):
        num_rows = self.resultsTable_2.rowCount()
        if row >= num_rows:
            row = num_rows - 1
        self.resultsTable_2.scrollToItem(self.resultsTable_2.item(row, 0))
        self.resultsTable_2.setVisible(True)
        self.tabWidget.setCurrentIndex(1)
        self.resultsTable_2.setFocus()  
        self.resultsTable_2.selectRow(row)
    def on_resultsTable_2_cell_clicked(self, row,column):
        num_rows = self.resultsTable.rowCount()
        if row >= num_rows:
            row = num_rows - 1
        self.resultsTable.scrollToItem(self.resultsTable.item(row, 0))
        self.resultsTable.setVisible(True)
        self.tabWidget.setCurrentIndex(0)
        self.resultsTable.setFocus()  
        self.resultsTable.selectRow(row)
    def show_notification(self,message):
        notification = ToastNotification(message,self)
        notification.show()
    def showUploadDialog(self):
        dialog = UploadDialog(self)
        dialog.exec_()
    def reset_window(self):
        self.filestable.setRowCount(0)
        self.add_plus_symbol()
        self.resultsTable.setRowCount(0)
        self.resultsTable_2.setRowCount(0)
        self.saveButton.setEnabled(False)
        self.clearButton.setEnabled(False)
        self.runButton.setEnabled(False)
        self.stopButton.setEnabled(False)
        self.clearButton_2.setEnabled(False)
        self.spinner.setEnabled(True)
        self.newButton.setChecked(False)
        self.resultsButton.setChecked(False)
        self.filesButton.setChecked(False)
        self.historyButton.setChecked(False)
        self.resetButton.setChecked(False)
        self.helpButton.setChecked(False)
        self.newButton_2.setChecked(False)
        self.resultsButton_2.setChecked(False)
        self.filesButton_2.setChecked(False)
        self.historyButton_2.setChecked(False)
        self.resetButton_2.setChecked(False)
        self.helpButton_2.setChecked(False)
        
class ToastNotification(QWidget):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.8)
        layout = QVBoxLayout()
        self.label = QLabel(message)
        layout.addWidget(self.label)
        font = QtGui.QFont()
        font.setFamily("Arial")
        font.setPointSize(12)
        font.setBold(False)
        font.setItalic(False)
        font.setWeight(40)
        self.label.setFont(font)
        self.setStyleSheet("background-color: black; color: white; padding: 10px; border-radius: 5px;")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setLayout(layout)
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.close)
        self.timer.start(5000)


    def show(self):
        super().show()

class UploadDialog(QDialog):
    def __init__(self,MainWindow):
        self.main_window = MainWindow
        super().__init__()
        self.initUI()
      
    def initUI(self):
        self.setWindowTitle("drag and drop")
        self.setGeometry(100, 100, 400, 300)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.dropLabel = QLabel("Drag and Drop to Upload File\nOR")
        layout.addWidget(self.dropLabel)
        self.browseButton = QPushButton("Browse File")
        self.browseButton.clicked.connect(self.browseFiles)
        layout.addWidget(self.browseButton)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [os.path.basename(u.toLocalFile())  for u in event.mimeData().urls()]
        self.handleFiles(files)

    def browseFiles(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files", "", "Audio Files (*.mp3 *.wav)", options=options)
        if not files:
            folder = QFileDialog.getExistingDirectory(self, "Select Folder", "", options=options)
            if folder:
                self.handleFolder(folder)
        else:
            self.handleFiles(files)

    def handleFiles(self, files):
        for file in files:
            if file.endswith(('.mp3', '.wav')):
                self.main_window.add_file_to_table([file])
            elif file.endswith('/'):  # Check if it's a directory
                self.handleFolder(file)
            else:
                QMessageBox.warning(self, "Invalid File", "Please choose a valid audio file (MP3, WAV, etc.).")


    def handleFolder(self, folder_name):
        if folder_name:
            file_paths = []
            non_mp3_files = []
            for f in os.listdir(folder_name):
                file_path = os.path.join(folder_name, f)
                if os.path.isfile(file_path) and (f.lower().endswith('.mp3') or f.lower().endswith('.wav')):
                    file_paths.append(file_path)
                elif os.path.isfile(file_path):
                    non_mp3_files.append(f)
            if non_mp3_files:
                not_saved_files=f"Selected folder '{os.path.basename(folder_name)}' has non-MP3 files which will not be processed: {', '.join(non_mp3_files)}"
                QMessageBox.warning(None, "Non Mp3 files", not_saved_files)
                self.statusbar.showMessage(not_saved_files)
            self.main_window.add_file_to_table(file_paths)

        
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.raise_()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
