pytest_plugins = ["pytestqt"]
import pytest,time
from PyQt5.QtWidgets import QApplication
from main import MainWindow


@pytest.fixture
def app(qtbot):
    return QApplication.instance() or QApplication([])

@pytest.fixture
def main_window(app):
    return MainWindow()

def test_newWindow(main_window, qtbot):
    main_window.newWindow()
    assert len(main_window.windows) == 1

def test_show_audio_recording_dialog(main_window, qtbot):
    x=main_window.filestable.rowCount()
    main_window.show_audio_recording_dialog()
    assert main_window.filestable.rowCount()== (x+1)

def test_populate_table(main_window, qtbot):
    main_window.populate_table()
    assert main_window.resultTable.rowCount() != 0
    assert main_window.resultTable2.rowCount() != 0

def test_run_button_clicked(main_window, qtbot):
    main_window.run_button_clicked()
    assert main_window.saveButton.isEnabled() == False
    assert main_window.recordButton.isEnabled() == False
    assert main_window.clearButton.isEnabled() == False
    assert main_window.stopButton.isEnabled() == True
    assert main_window.runButton.isEnabled() == False
    time.sleep(10)
    assert main_window.resultsTable.rowCount() !=0
    assert main_window.resultsTable_2.rowCount() !=0

def test_stop_button_clicked(main_window, qtbot):
    x=main_window.resultsTable.rowCount() !=0
    main_window.stop_button_clicked()
    assert main_window.resultsTable.rowCount() ==x
    assert main_window.runButton.isEnabled() == True
    assert main_window.stopButton.isEnabled() == False
    assert main_window.recordButton.isEnabled() == True
    if main_window.resultsTable.rowCount()!=0:
        assert main_window.clearButton.isEnabled() == True
        assert main_window.saveButton.isEnabled() == True
    else:
        assert main_window.clearButton.isEnabled() == False
        assert main_window.saveButton.isEnabled() == False

def test_clear_button_clicked(main_window, qtbot):
    main_window.clear_button_clicked()
    assert main_window.resultsTable.rowCount() ==0
    assert main_window.resultsTable_2.rowCount() ==0
    assert main_window.saveButton.isEnabled() == False
    assert main_window.clearButton.isEnabled() == False
    assert main_window.runButton.isEnabled() == True
    assert main_window.stopButton.isEnabled() == False
    
def test_save_button_clicked(main_window, qtbot):
    main_window.save_button_clicked()
    if main_window.resultsTable.rowCount() == 0:
        assert main_window.statusbar.currentMessage() == "no data to save"
    else:
        assert main_window.statusbar.currentMessage() == "File saved successfully"

def test_clearfiles_clicked(main_window, qtbot):
    main_window.clearfiles_clicked()
    assert main_window.filestable.rowCount() == 1

def test_add_plus_symbol(main_window, qtbot):
    x=main_window.filestable.rowCount()
    main_window.add_plus_symbol()
    assert main_window.filestable.rowCount() > x

def test_remove_plus_symbol(main_window, qtbot):
    x=main_window.filestable.rowCount()
    main_window.remove_plus_symbol()
    assert main_window.filestable.rowCount() == x-1

def test_upload_file(main_window, qtbot):
    main_window.upload_file()
    assert main_window.filestable.rowCount() == 2

def test_upload_folder(main_window, qtbot):
    main_window.upload_folder()
    assert main_window.filestable.rowCount() >=2



def test_delete_file(main_window, qtbot):
    if main_window.filestable.rowCount()==1:
        pass
    else:
        x=main_window.filestable.rowCount()
        main_window.delete_file("file_name")
        assert main_window.filestable.rowCount()< x

def test_on_resultTable_cell_clicked(main_window, qtbot):
    main_window.on_resultsTable_cell_clicked(0, 0)
    assert main_window.tabWidget.currentIndex() == 1

def test_on_resultTable2_cell_clicked(main_window, qtbot):
    main_window.on_resultsTable_2_cell_clicked(0, 0)
    assert main_window.tabWidget.currentIndex() == 0

def test_show_notification(main_window, qtbot):
    main_window.show_notification("message")
