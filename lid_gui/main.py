import time
from layout import Ui_MainWindow
import audio_recorder
import csv,os,sys,xlrd,openpyxl
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSignal,QSize
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton,
    QFileDialog, QAction, QTextEdit, QDialog,QMessageBox , QSizePolicy, QComboBox, QWidget,
    QHBoxLayout, QLabel, QVBoxLayout, QTextBrowser
)
import pandas as pd
from threading import Timer
from PyQt5.QtGui import QFont,QIcon
from PyQt5.QtCore import QObject,QThread,pyqtSlot,QUrl, QDir,Qt, QTimer
from PyQt5.QtCore import pyqtSignal as Signal
import warnings, datetime
warnings.filterwarnings("ignore", category=DeprecationWarning)

class MainWindow(QMainWindow, Ui_MainWindow):
    capacity=3
    notification_signal = Signal(str)
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)
        self.is_running=False
        self.fileName=None
        self.dark_theme = True
        with open("dark_theme.qss", "r") as f:
            self.setStyleSheet(f.read())
        icon_14= QtGui.QIcon()
        icon_14.addPixmap(QtGui.QPixmap(":/Icons/dark.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.modeButton.setIcon(icon_14)
        self.modeButton.setIconSize(QtCore.QSize(60, 30))
        self.add_plus_symbol()
        self.resetButton.clicked.connect(self.reset_window)
        self.uploadButton.clicked.connect(self.showUploadDialog)
        self.recordButton.clicked.connect(self.show_audio_recording_dialog)
        self.runButton.clicked.connect(self.run_button_clicked)
        self.stopButton.clicked.connect(self.stop_button_clicked)
        self.populate_thread = None
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
        self.modeButton.clicked.connect(self.toggleTheme)
        self.helpButton.clicked.connect(self.showHelpDialog)

    def toggleTheme(self):
        self.dark_theme = not self.dark_theme
        self.applyTheme() 
    def applyTheme(self):
        if self.dark_theme:
            icon_14= QtGui.QIcon()
            icon_14.addPixmap(QtGui.QPixmap(":/Icons/dark.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.modeButton.setIcon(icon_14)
            self.modeButton.setIconSize(QtCore.QSize(60, 30))
            with open("dark_theme.qss", "r") as f:
                self.setStyleSheet(f.read())
        else:
            icon_15= QtGui.QIcon()
            icon_15.addPixmap(QtGui.QPixmap(":/Icons/light.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            self.modeButton.setIcon(icon_15)
            self.modeButton.setIconSize(QtCore.QSize(60, 30))
            with open("light_theme.qss", "r") as f:
                self.setStyleSheet(f.read())

    def newWindow(self):
        window = MainWindow()
        self.windows = getattr(self, 'windows', []) + [window]
        window.show()
        window.raise_()        
    def show_audio_recording_dialog(self):
        if self.filestable.rowCount()>self.capacity:
            self.limit_exceeded()
            return None
        else:
            self.notification_signal.emit("Recorder on")
            dialog = audio_recorder.AudioRecorderDialog()
            dialog.raise_()
            dialog.file_saved.connect(self.on_file_saved)
            dialog.exec_()
        return dialog
    def on_file_saved(self, filename):
        self.add_file_to_table([filename])
        self.notification_signal.emit("recording saved")
    def run_button_clicked(self):
        self.is_running=True
        self.runButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.uploadButton.setEnabled(False)
        self.recordButton.setEnabled(False)
        self.clearButton.setEnabled(False)
        self.resultsTable.setRowCount(0)
        self.resultsTable_2.setRowCount(0)
        self.resultsTable.setColumnCount(3)
        self.resultsTable.setHorizontalHeaderLabels(['Filename', 'Language1', 'Confidence1'])
        self.resultsTable_2.setColumnCount(5) 
        self.resultsTable_2.setHorizontalHeaderLabels(['Filename', 'Language1', 'Confidence1', 'Language2', 'Confidence2'])  
        self.populate_thread = PopulateTableThread("LID_RESULT.xls")
        self.populate_thread.update_row.connect(self.update_results_row)
        self.populate_thread.finished.connect(self.on_populate_finished)
        self.populate_thread.start()
        
    def update_results_row(self, row_selected, row_full, index):
        self.resultsTable.insertRow(index)
        for col, value in enumerate(row_selected): 
            self.resultsTable.setItem(index, col, QTableWidgetItem(str(value)))
        self.resultsTable_2.insertRow(index)
        for col, value in enumerate(row_full):  
            self.resultsTable_2.setItem(index, col, QTableWidgetItem(str(value)))
        self.resultsTable.scrollToItem(self.resultsTable.item(index, 0))
        self.resultsTable_2.scrollToItem(self.resultsTable_2.item(index, 0))
    def stop_button_clicked(self):
        self.is_running=False
        if self.populate_thread and self.populate_thread.isRunning():
            self.populate_thread.stop()
            self.populate_thread.wait()
        if self.resultsTable.rowCount()!=0:
            self.saveButton.setEnabled(True)
            self.clearButton_2.setEnabled(True)
        else:
            self.saveButton.setEnabled(False)
            self.clearButton_2.setEnabled(False)
        self.stopButton.setEnabled(False)
        self.runButton.setEnabled(True)

    def on_populate_finished(self):
        self.stopButton.setEnabled(False)
        self.runButton.setEnabled(True)
        self.saveButton.setEnabled(True)
        self.clearButton_2.setEnabled(True)
        self.uploadButton.setEnabled(True)
        self.recordButton.setEnabled(True)
        self.clearButton.setEnabled(True)

        
        
    def clear_button_clicked(self):
        self.saveButton.setEnabled(False)
        self.clearButton_2.setEnabled(False)
        self.runButton.setEnabled(True)
        self.uploadButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.statusbar.showMessage("results have been cleared")
        self.resultsTable.setRowCount(0)
        self.resultsTable_2.setRowCount(0)
        
    def save_button_clicked(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        if self.resultsTable_2.rowCount() > 0:
            self.fileName, _ = QFileDialog.getSaveFileName(None, "Save Results", "", "EXCEL  Files (*.xls);;All Files (*)", options=options)
            if self.fileName:
                try:
                    with open(self.fileName, 'w', newline='') as csvfile:
                        writer = csv.writer(csvfile)
                        headers = [self.resultsTable_2.horizontalHeaderItem(i).text() for i in range(self.resultsTable_2.columnCount())]
                        writer.writerow(headers)  
                        for row in range(self.resultsTable_2.rowCount()):
                            rowdata = []
                            for column in range(self.resultsTable_2.columnCount()):
                                item = self.resultsTable_2.item(row, column)
                                if item is not None:
                                    rowdata.append(item.text())
                                else:
                                    rowdata.append('')
                            writer.writerow(rowdata)
                    self.notification_signal.emit("Data saved successfully")
                    self.statusbar.showMessage("File saved successfully", 2000)
                except Exception as e:
                    QMessageBox.critical(None, "Failed to save file", str(e))
                    self.statusbar.showMessage("Failed to save file", 2000)
        else:
            QMessageBox.critical(None, "Failed to save file", 'No data to save')
            self.statusbar.showMessage("No data to save")

    def clearfiles_clicked(self):  
        self.filestable.setRowCount(0)
        self.notification_signal.emit("selected Files cleared")
        self.add_plus_symbol() 
        self.uploadButton.setEnabled(True)
        self.recordButton.setEnabled(True) 

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
        background-color:rgb(38, 38, 38);
        color: rgb(163, 230, 53);
        selection-color: rgb(170, 85, 255);
        selection-background-color:rgb(38, 38, 38);
        }
        QComboBox QAbstractItemView{
        background-color:rgb(38, 38, 38);
        border: none; /* add this line to remove the border */
        }
        """)
        self.spinner.currentTextChanged.connect(self.spinner_selected)
        self.filestable.setCellWidget(row_position, 0, self.spinner) 
        if self.filestable.rowCount()>(self.capacity):
            self.spinner.currentTextChanged.connect(self.limit_exceeded)
            
    def limit_exceeded(self):
        QMessageBox.information(self, "Limit Exceeded", "You have reached the maximum limit to upload files.")

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
            file_name, _ = QFileDialog.getOpenFileName(None, "Upload File", "",filter="Audio files (*.mp3 *.wav);;MP3 files (*.mp3);;WAV files (*.wav);;All files (*.*)")
            if file_name:
                self.add_file_to_table([file_name])
            else:
                self.spinner.setCurrentIndex(0)

    def upload_folder(self):
        if self.filestable.rowCount()<=self.capacity:
            folder_name = QFileDialog.getExistingDirectory(None, "Upload Folder","")
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
                    not_saved_files=f"Selected folder '{os.path.basename(folder_name)}' has non-MP3 files which will not be processed"
                    self.statusbar.showMessage(not_saved_files)
                self.add_file_to_table(file_paths)
            else:
                self.spinner.setCurrentIndex(0)
    
    def add_file_to_table(self, file_paths):
        if not isinstance(file_paths, list):
            file_paths = [file_paths]
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
            if self.filestable.rowCount() < self.capacity:
                print(file_path)
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path) / 1024  # Convert to KB
                upload_date = datetime.date.today().strftime("%Y-%m-%d")
                row_position = self.filestable.rowCount()
                self.filestable.insertRow(row_position)
                self.filestable.setItem(row_position, 0, QTableWidgetItem(file_name))
                self.filestable.setItem(row_position, 1, QTableWidgetItem(f"{file_size:.2f} KB"))
                layout = QHBoxLayout()
                layout.setContentsMargins(0, 0, 0, 0)
                date_label = QLabel(upload_date)
                font = QFont()
                font.setPointSize(12)
                date_label.setFont(font)
                delete_button = QPushButton("X")
                delete_button.setFixedSize(20, 20)
                delete_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                delete_button.setStyleSheet("""QPushButton{color:black;background-color:rgb(255, 115, 97);}
                                           QPushButton:hover{color:red;background-color:white;border:2px solid red;}
                                           QPushButton:focus{color:white;background-color:red;}""")
                delete_button.setFocusPolicy(QtCore.Qt.ClickFocus)
                delete_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
                delete_button.clicked.connect(lambda checked, file_name=file_name: self.delete_file(row_position))
                layout.addWidget(date_label)
                layout.addWidget(delete_button)
                widget = QWidget()
                widget.setStyleSheet("QWidget { background-color: transparent; color:rgb(163, 230, 53);}")
                widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                widget.setLayout(layout)
                self.filestable.setCellWidget(row_position, 2, widget)
            else:
                QMessageBox.information(self.centralwidget, "Information!", 'Uploaded more files than the processing capacity for a time! only few files are uploaded', buttons=QMessageBox.Ok)
                break
        self.add_plus_symbol()
        if self.filestable.rowCount() > 1:
            self.runButton.setEnabled(True)
            self.clearButton.setEnabled(True)
        else:
            self.runButton.setEnabled(False)
            self.clearButton.setEnabled(False)
  
    def delete_file(self, row_position):
        self.reply = QMessageBox.question(self.centralwidget, 'Delete File', 'Are you sure you want to delete this file?',
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if self.reply == QMessageBox.Yes:
            self.filestable.removeRow(row_position)
        if self.filestable.rowCount()==self.capacity:
            self.spinner.setEnabled(True)
            self.spinner.setCurrentIndex(0)
            self.spinner.currentTextChanged.disconnect(self.limit_exceeded)
            self.spinner.currentTextChanged.connect(self.spinner_selected)
            self.uploadButton.setEnabled(True)
            self.recordButton.setEnabled(True)
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
        if self.filestable.rowCount()>self.capacity:
            self.limit_exceeded()
        else:
            dialog = UploadDialog(self)
            dialog.exec_()
    
    def showHelpDialog(self):
        help_dialog = HelpDialog(self)
        help_dialog.exec_()

    def reset_window(self):
        self.reset=True
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
        self.recordButton.setEnabled(True)
        self.uploadButton.setEnabled(True)
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
        self.setStyleSheet("background-color:black; color: white; padding: 10px; border-radius: 5px;")
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
        self.setWindowTitle("Upload")
        self.setGeometry(400, 200, 400, 300)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setStyleSheet("""
        QWidget {
            background-color:white;
            font-family: Arial;
            font-size: 12px;
        }
        """)

        # Create the drop/upload layout
        drop_widget = QWidget()
        drop_widget.setStyleSheet("""
        QWidget {
            background-color: #e6f0ff;
            border-radius: 15px;
            border: 2px dashed rgb(14, 165, 233);
        }
        """)
        self.drop_layout = QVBoxLayout()
        self.drop_layout.setSpacing(0)
        drop_widget.setLayout(self.drop_layout)
        icon = QIcon(":/Icons/drag.png")
        pixmap= icon.pixmap(QSize(100, 100))
        self.icon_label = QLabel()
        self.icon_label.setPixmap(pixmap)
        self.icon_label.setAlignment(QtCore.Qt.AlignCenter|QtCore.Qt.AlignBottom)
        self.drop_layout.addWidget(self.icon_label)
        self.icon_label.setStyleSheet("""
        QLabel{
        border:none;
        padding-top:30px;
        padding-bottom:0px;
        margin-bottom:0px;
        }
        """)
        self.dropLabel = QLabel("Drag and Drop your files\nOR")
        self.dropLabel.setAlignment(Qt.AlignCenter)
        self.dropLabel.setStyleSheet("""
        QLabel {
            font-size: 16px;
            color: rgb(14, 165, 233);
            border: none;
            padding-top:0px;
            padding-bottom:20px;
            margin-top:0px;
        }
        """)
        self.drop_layout.addWidget(self.dropLabel)

        # Add the drop/upload layout to the main layout
        layout.addWidget(drop_widget)

        # Create the browse button
        self.browseButton = QPushButton("Browse File")
        self.browseButton.clicked.connect(self.browseFiles)
        self.browseButton.setStyleSheet("""
        QPushButton {
            height:30px;
            width:100px;
            text-decoration:underline;
            background-color:white;
            color: rgb(7, 89, 133);
            padding:2px;
            border-radius: 10px;
            font-size:16px;
        }
        """)
        layout.addWidget(self.browseButton)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()
        
        
    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls()]
        print(paths)
        self.handleFiles(paths)
        self.close()
        self.main_window.raise_()
        

    def browseFiles(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(None, "Select Files", "", "Audio Files (*.mp3 *.wav);;MP3 files (*.mp3);;WAV files (*.wav)", options=options)
        if files:
            self.handleFiles(files)
        self.close()
        
    def handleFiles(self, paths):
        if not paths:
            return
        
        if os.path.isdir(paths[0]):
            self.handleFolder(paths[0])
        else:
            for file_path in paths:
                if file_path.lower().endswith(('.mp3', '.wav')):
                    print(file_path)
                    self.main_window.add_file_to_table([file_path])

    def handleFolder(self, folder_path):
        if folder_path:
            file_paths = []
            non_audio_files = []
            for f in os.listdir(folder_path):
                file_path = os.path.join(folder_path, f)
                if os.path.isfile(file_path):
                    if file_path.lower().endswith(('.mp3', '.wav')):
                        file_paths.append(file_path)
                    else:
                        non_audio_files.append(f)
            if non_audio_files:
                not_saved_files = f"Selected folder '{os.path.basename(folder_path)}' has non-audio files which will not be processed"
                self.main_window.notification_signal.emit(not_saved_files)
            self.main_window.add_file_to_table(file_paths)
        else:
            print('Folder not found')

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Help")
        self.setGeometry(100, 100, 800, 600)
        layout = QVBoxLayout()
        self.setLayout(layout)

        help_text = """
        <h2><u>Getting Started</u></h2>
        <p>This application is designed to identify the language spoken in audio files.
        You can upload files and folders by clicking the "Upload" button.
        Supported file formats: MP3, WAV
        The uploades files get processed when the "Run" button is clicked.
        The results of the processed files gets updated at the "Results" table.</p>

        <h2><u>Uploading Files and Folders</u></h2>
        <p>Click the "Upload" button to drag and drop files or folders to upload.
        You can upload multiple files and folders at once.
        You can also upload files by using the "Select Upload" button in the selected files table.
        Selected files will be displayed in the "Selected Files" section.
        The files get uploaded only if the number of files uploaded are within the capacity.</p>

        <h2><u>Recording Live Voice</u></h2>
        <p>Click the "Record" button to start recording your live voice.
        The recorded audio will be saved as an mp3 file and uploaded to the "Selected Files" section.
        You can then run the language identification process on the recorded file.
        The "Record" button will be enabled only if the number of files uploaded are within the capacity.</p>

        <h2><u>Running the Language Identification</u></h2>
        <p>Click the "Run" button to start the language identification process.
        The application will process each file individually and display the results in the "Results" section.
        The results will include the file name, identified language, and confidence level.</p>

        <h2><u>Results</u></h2>
        <p>The "Results" section displays the language identification results for each file.
        To get a more detailed view of results switch to "Details" section.
        You can save the results by clicking the "Save" button.</p>

        <h2><u>Saving Results</u></h2>
        <p>Click the "Save" button to save the language identification results to file.
        You can choose the file name and location.
        The file gets saved in an xls file format.</p>

        <h2><u>Tips and Troubleshooting</u></h2>
        <p>Make sure to upload files in the supported formats (MP3, WAV).
        If you encounter any errors during the language identification process, check the file format and try again.
        Make sure the number of the files are within the capacity before uploading a new file.
        If you encounter while uploading the files, check if the capacity of number of files.
        If the capacity of number of files exceeded try uploading files in a new window by clicking "New Window" button
        (or) try after removing some files from the selected files.</p>

        <h2><u>About</u></h2>
        <p>This application uses advanced machine learning algorithms to identify languages spoken in audio files.
        The application is designed to be user-friendly and easy to use.
        We hope you find this application helpful!</p>
        """
        self.text_browser = QTextBrowser()
        self.text_browser.setText(help_text) 
        self.text_browser.setStyleSheet("""
            QTextBrowser{
            background-color:black;
            color:white;
            padding:20px;
            margin:10px;
            border:1px solid white;
            }
            """)
        layout.addWidget(self.text_browser)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.close)
        layout.addWidget(ok_button) 
            
import time
import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal

class PopulateTableThread(QThread):
    finished = pyqtSignal()
    update_row = pyqtSignal(pd.Series, pd.Series, int)
    error_occurred = pyqtSignal(str)

    def __init__(self, file_path, row_delay=1):
        super().__init__()
        self.file_path = file_path
        self.is_running = True
        self.row_delay = row_delay  

    def run(self):
        time.sleep(3)   
        if self.is_running:
            try:
                df = pd.read_excel(self.file_path)
                required_columns = ['Filename', 'Language1', 'Confidence1']
                df_selected = df[required_columns]
                for index in range(len(df)):
                    if not self.is_running:
                        break
                    row_selected = df_selected.iloc[index]  
                    row_full = df.iloc[index]  
                    self.update_row.emit(row_selected, row_full, index)
                    time.sleep(self.row_delay)
                    
            except Exception as e:
                error_msg = f"Error reading file: {str(e)}"
                print(error_msg)
                self.error_occurred.emit(error_msg)
        self.finished.emit()

    def stop(self):
        self.is_running = False
        
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.raise_()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()

