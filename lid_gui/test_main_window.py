pytest_plugins = ["pytestqt"]
import pytest,time
from PyQt5.QtWidgets import QApplication,QMessageBox,QPushButton
from main import MainWindow
from unittest.mock import patch


@pytest.fixture
def app(qtbot):
    return QApplication.instance() or QApplication([])

@pytest.fixture
def main_window(app):
    return MainWindow()

def test_newWindow(main_window, qtbot):
    main_window.newWindow()
    assert len(main_window.windows) == 1

'''def test_show_audio_recording_dialog(main_window, qtbot):
    main_window.show_audio_recording_dialog()
    assert main_window.statusbar.currentMessage() == " " '''
def test_upload_file(main_window, qtbot):
    x= main_window.filestable.rowCount()
    main_window.upload_file()
    assert main_window.filestable.rowCount() > x

def test_upload_folder(main_window, qtbot):
    x= main_window.filestable.rowCount()
    main_window.upload_file()
    assert main_window.filestable.rowCount() > x

def test_delete_file(main_window, qtbot):
    main_window.upload_folder()
    x = main_window.filestable.rowCount()
    if x == 1:
        return
    for row in range(x):
        widget = main_window.filestable.indexWidget(main_window.filestable.model().index(row, 0))
        if widget:
            delete_button = None
            for child in widget.children():
                if isinstance(child, QPushButton) and child.text() == 'Delete':
                    delete_button = child
                    break
            if delete_button:
                with patch('PyQt5.QtWidgets.QMessageBox.question', return_value=QMessageBox.Yes):
                    initial_row_count = main_window.filestable.rowCount()
                    qtbot.mouseClick(delete_button, QtCore.Qt.LeftButton)
                    assert main_window.filestable.rowCount() == initial_row_count - 1

                with patch('PyQt5.QtWidgets.QMessageBox.question', return_value=QMessageBox.No):
                    initial_row_count = main_window.filestable.rowCount()
                    qtbot.mouseClick(delete_button, QtCore.Qt.LeftButton)
                    assert main_window.filestable.rowCount() == initial_row_count

def test_add_plus_symbol(main_window, qtbot):
    x=main_window.filestable.rowCount()
    main_window.add_plus_symbol()
    assert main_window.filestable.rowCount() > x

def test_remove_plus_symbol(main_window, qtbot):
    x=main_window.filestable.rowCount()
    main_window.remove_plus_symbol()
    assert main_window.filestable.rowCount() == x-1
def test_clearfiles_clicked(main_window, qtbot):
    x= main_window.filestable.rowCount()
    main_window.upload_file()
    main_window.clearfiles_clicked()
    assert main_window.filestable.rowCount() == 1

def test_run_button_clicked(main_window, qtbot):
    main_window.upload_file()
    main_window.run_button_clicked()
    time.sleep(5)
    assert main_window.is_running==True
    assert main_window.populate_thread.isRunning() == True
    
    

def test_stop_button_clicked(main_window, qtbot):
    main_window.upload_file()
    main_window.run_button_clicked()
    assert main_window.is_running==True
    assert main_window.populate_thread.isRunning() == True
    time.sleep(6)
    main_window.stop_button_clicked()
    assert main_window.is_running==False
    assert main_window.populate_thread.isRunning() == False
    if main_window.resultsTable.rowCount()==0:
        assert main_window.saveButton.isEnabled() == False
        assert main_window.clearButton_2.isEnabled() == False
    else:
        assert main_window.saveButton.isEnabled() == True
        assert main_window.clearButton_2.isEnabled() == True
    
    assert main_window.runButton.isEnabled() == True
    assert main_window.stopButton.isEnabled() == False
  

def test_clear_button_clicked(main_window, qtbot):
    main_window.upload_file()
    main_window.run_button_clicked()
    time.sleep(10)
    x=main_window.resultsTable.rowCount()
    print(x)
    main_window.clearButton_2.clicked.emit()
    assert main_window.saveButton.isEnabled() == False
    assert main_window.clearButton.isEnabled() == False
    assert main_window.runButton.isEnabled() == True
    assert main_window.stopButton.isEnabled() == False
    assert main_window.resultsTable.rowCount() == 0
    assert main_window.resultsTable_2.rowCount() == 0

def test_save_button_clicked(main_window, qtbot):
    main_window.upload_file()
    main_window.run_button_clicked()
    time.sleep(6)
    main_window.stop_button_clicked()
    main_window.save_button_clicked()
    if main_window.fileName:
        assert os.path.exists(fileName)==True
    else:
        if main_window.resultsTable.rowCount()== 0:
            assert main_window.statusbar.currentMessage()== "No data to save"
        else:
            assert main_window.statusbar.currentMessage()== "No data to save"
        
def test_on_tabWidgetle_cell_clicked(main_window, qtbot):
    main_window.on_resultsTable_cell_clicked(0, 0)
    assert main_window.tabWidget.currentIndex() == 1

def test_on_resultsTable_2_cell_clicked(main_window, qtbot):
    main_window.on_resultsTable_2_cell_clicked(0, 0)
    assert main_window.tabWidget.currentIndex() == 0

def test_resetButton(main_window,qtbot):
    main_window.upload_file()
    main_window.run_button_clicked()
    time.sleep(10)
    main_window.stop_button_clicked()
    main_window.reset_window()
    assert main_window.saveButton.isEnabled() == False
    assert main_window.recordButton.isEnabled() == True
    assert main_window.clearButton_2.isEnabled() == False
    assert main_window.stopButton.isEnabled() == False
    assert main_window.runButton.isEnabled() == False
    assert main_window.uploadButton.isEnabled() == True
    assert main_window.resultsTable.rowCount() == 0
    assert main_window.resultsTable_2.rowCount() == 0
    assert main_window.filestable.rowCount() == 1

