import re
import sys

from PySide6 import QtCore, QtGui, QtWidgets

from consts import BUTTON_WIDTH, DEFAULT_FONT, ICON_H, ICON_W, XBOX_GREEN, DumpingStatus
from uwp import get_running_uwp_apps


def process_uwpdumper_output(output: str):
    # Remove ASCII color codes
    processed_output = re.sub("\x1b\\[[;\\d]*m", "", output)

    # Remove ASCII special symbols codes
    processed_output = processed_output.replace("\x1b(0m", "").replace("\x1b(B", "")
    processed_output = re.sub("\x1b\(0q*", "", processed_output)

    # Remove prompt message
    processed_output = processed_output.replace("Press any key to continue . . .", "")

    return processed_output


class ImageWidget(QtWidgets.QWidget):
    def __init__(
        self,
        image_path: str,
        width: int,
        height: int,
        bkgrnd_color: QtGui.QColor,
        parent: QtWidgets.QWidget,
    ):
        super(ImageWidget, self).__init__(parent)

        self.img_width = width
        self.img_height = height
        self.bkgrnd_color = bkgrnd_color
        self.picture = QtGui.QPixmap(image_path).scaled(
            self.img_width,
            self.img_height,
            aspectMode=QtCore.Qt.KeepAspectRatio,
            mode=QtCore.Qt.SmoothTransformation,
        )

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.fillRect(
            0,
            0,
            self.img_width,
            self.img_height,
            QtGui.QBrush(self.bkgrnd_color),
        )
        painter.drawPixmap(0, 0, self.picture)


class AppWidget(QtWidgets.QWidget):
    def __init__(self, uwpdumper_path: str):
        super().__init__()

        self.uwpdumper_path = uwpdumper_path

        self.selected_process_data = None
        self.dumping_status = DumpingStatus.NO_DUMPING

        self.setup_main_window()
        self.setup_uwp_selecting_dialog()
        self.setup_dumping_dialog()

        self.setFont(DEFAULT_FONT)
        self.uwp_selecting_dialog.setFont(DEFAULT_FONT)
        self.dumping_dialog.setFont(DEFAULT_FONT)

        for btn in [
            self.select_destn_btn,
            self.select_uwp_btn,
            self.refresh_btn,
            self.select_uwp_in_dialog_btn,
            self.dump_btn,
            self.continue_btn,
        ]:
            btn.setFixedWidth(BUTTON_WIDTH)

    def setup_main_window(self):
        # Widgets definitions
        self.uwp_process_label = QtWidgets.QLabel("UWP process")
        self.selected_uwp_process = QtWidgets.QLineEdit()
        self.select_uwp_btn = QtWidgets.QPushButton("Select")
        self.uwp_selecting_dialog = QtWidgets.QDialog(
            f=QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.WindowCloseButtonHint
        )
        self.select_uwp_in_dialog_btn = QtWidgets.QPushButton("Select")
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.destn_dir_label = QtWidgets.QLabel("Destination directory")
        self.destn_dir = QtWidgets.QLineEdit()
        self.select_destn_btn = QtWidgets.QPushButton("Browse")
        self.registering_checkbox = QtWidgets.QCheckBox(
            "Remove the old installation and register the new one after dumping"
        )
        self.dump_btn = QtWidgets.QPushButton("Dump")
        self.dumping_dialog = QtWidgets.QDialog(
            f=QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.WindowCloseButtonHint
        )
        self.main_msgbox = QtWidgets.QMessageBox(self)

        # Set widgets properties/data
        self.destn_dir.setReadOnly(True)
        self.selected_uwp_process.setReadOnly(True)

        self.select_uwp_btn.clicked.connect(self.open_selecting_uwp_dialog)
        self.select_uwp_in_dialog_btn.clicked.connect(self.select_uwp_process)
        self.refresh_btn.clicked.connect(self.refresh_list)
        self.select_destn_btn.clicked.connect(self.select_destn_folder)
        self.dump_btn.clicked.connect(self.dump_app)

        # Layout
        self.layout = QtWidgets.QGridLayout(self)

        self.layout.addWidget(
            self.uwp_process_label, 0, 0, 1, 2, alignment=QtCore.Qt.AlignTop
        )
        self.layout.addWidget(
            self.selected_uwp_process, 1, 0, alignment=QtCore.Qt.AlignTop
        )
        self.layout.addWidget(self.select_uwp_btn, 1, 1, alignment=QtCore.Qt.AlignTop)
        self.layout.addWidget(
            self.destn_dir_label, 2, 0, 1, 2, alignment=QtCore.Qt.AlignTop
        )
        self.layout.addWidget(self.destn_dir, 3, 0, alignment=QtCore.Qt.AlignTop)
        self.layout.addWidget(self.select_destn_btn, 3, 1, alignment=QtCore.Qt.AlignTop)

        self.layout.addWidget(
            self.registering_checkbox, 4, 0, 1, 2, alignment=QtCore.Qt.AlignTop
        )
        self.layout.addWidget(self.dump_btn, 5, 0, 1, 2, alignment=QtCore.Qt.AlignTop)
        self.layout.setRowStretch(3, 1)

    def setup_uwp_selecting_dialog(self):
        self.uwp_selecting_dialog.resize(800, 600)

        self.uwp_selection_msgbox = QtWidgets.QMessageBox(self.uwp_selecting_dialog)

        self.running_uwp_apps_table = QtWidgets.QTableWidget()
        self.running_uwp_apps_table.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers
        )
        self.running_uwp_apps_table.setSelectionMode(
            QtWidgets.QAbstractItemView.SingleSelection
        )
        self.running_uwp_apps_table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectRows
        )
        self.running_uwp_apps_table.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Fixed
        )

        cols_header = ["PID", "Icon", "Process", "Executable path"]
        self.running_uwp_apps_table.setColumnCount(len(cols_header))
        self.running_uwp_apps_table.setHorizontalHeaderLabels(cols_header)

        # Make the 1st and 2nd columns non-resizable ("PID" and "Icon")
        hz_header = self.running_uwp_apps_table.horizontalHeader()
        hz_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Fixed)
        hz_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Fixed)

        self.update_running_uwp_table()

        self.uwp_selecting_dialog.setModal(True)

        self.uwp_selecting_layout = QtWidgets.QGridLayout(self.uwp_selecting_dialog)

        self.uwp_selecting_layout.addWidget(self.running_uwp_apps_table, 0, 0, 1, 2)
        self.uwp_selecting_layout.addWidget(
            self.refresh_btn, 1, 0, alignment=QtCore.Qt.AlignLeft
        )
        self.uwp_selecting_layout.addWidget(
            self.select_uwp_in_dialog_btn, 1, 1, alignment=QtCore.Qt.AlignRight
        )

    def setup_dumping_dialog(self):
        self.dumping_dialog.resize(800, 600)
        self.uwpdumper_output = QtWidgets.QTextBrowser()
        self.dumping_progressbar = QtWidgets.QProgressBar()
        self.continue_btn = QtWidgets.QPushButton("Continue")
        self.uwp_dumping_msgbox = QtWidgets.QMessageBox(self.dumping_dialog)

        self.dumping_dialog.setModal(True)

        self.dumping_dialog_layout = QtWidgets.QGridLayout(self.dumping_dialog)

        self.dumping_dialog_layout.addWidget(QtWidgets.QLabel("UWPDumper output:"))
        self.dumping_dialog_layout.addWidget(self.uwpdumper_output)
        self.dumping_dialog_layout.addWidget(self.dumping_progressbar)
        self.dumping_dialog_layout.addWidget(self.continue_btn)

    def update_running_uwp_table(self):
        self.running_uwp_apps = get_running_uwp_apps()

        self.running_uwp_apps_table.setRowCount(len(self.running_uwp_apps))
        for i, running_app_data in enumerate(self.running_uwp_apps):
            self.running_uwp_apps_table.setItem(
                i,
                0,
                QtWidgets.QTableWidgetItem(
                    running_app_data["pid"],
                ),
            )

            icon_widget = ImageWidget(
                running_app_data["logo_fullpath"],
                ICON_W,
                ICON_H,
                XBOX_GREEN,
                self.running_uwp_apps_table,
            )
            self.running_uwp_apps_table.setCellWidget(i, 1, icon_widget)

            self.running_uwp_apps_table.setItem(
                i, 2, QtWidgets.QTableWidgetItem(running_app_data["image_name"])
            )
            self.running_uwp_apps_table.setItem(
                i, 3, QtWidgets.QTableWidgetItem(running_app_data["executable_path"])
            )

        self.running_uwp_apps_table.resizeColumnsToContents()
        self.running_uwp_apps_table.setColumnWidth(1, ICON_W)

        self.running_uwp_apps_table.resizeRowsToContents()
        for i in range(self.running_uwp_apps_table.rowCount()):
            current_height = self.running_uwp_apps_table.rowHeight(i)
            if ICON_H > current_height:
                self.running_uwp_apps_table.setRowHeight(i, ICON_H)

    @QtCore.Slot()
    def refresh_list(self):
        self.update_running_uwp_table()

    @QtCore.Slot()
    def open_selecting_uwp_dialog(self):
        self.update_running_uwp_table()
        self.uwp_selecting_dialog.open()

    @QtCore.Slot()
    def select_uwp_process(self):
        selected_rows = list(
            set([elt.row() for elt in self.running_uwp_apps_table.selectedIndexes()])
        )
        msg = None
        if len(selected_rows) == 0:
            msg = "Please select a process"
        elif len(selected_rows) > 1:
            msg = "More than one process selected, this shouldn't be possible"
        else:
            self.selected_process_data = self.running_uwp_apps[selected_rows[0]]
            self.selected_uwp_process.setText(self.selected_process_data["image_name"])
            self.uwp_selecting_dialog.close()

        if msg is not None:
            self.uwp_selection_msgbox.setText(msg)
            self.uwp_selection_msgbox.show()

    @QtCore.Slot()
    def select_destn_folder(self):
        destn_dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            None, "Select a folder:", "C:\\", QtWidgets.QFileDialog.ShowDirsOnly
        )
        if destn_dir_path != "":
            self.destn_dir.setText(destn_dir_path)

    @QtCore.Slot()
    def dump_app(self):
        self.continue_btn.hide()

        msg = None
        if self.selected_process_data is None:
            msg = "Please select a process"
        elif self.destn_dir.text() == "":
            msg = "Please select a destination directory"
        else:
            app_pid = self.selected_process_data["pid"]

            self.uwp_dumper_process = QtCore.QProcess()
            self.uwp_dumper_process.readyReadStandardOutput.connect(
                self.update_uwpdumper_output
            )
            self.uwp_dumper_process.finished.connect(self.handle_uwpdumper_finished)

            self.uwp_dumper_process.start(
                self.uwpdumper_path,
                ["-p", str(app_pid), "-d", self.destn_dir.text().replace("/", "\\")],
            )
            self.dumping_status = DumpingStatus.IN_PROGRESS

            # UWPDumper expects a user input when the dump is done
            self.uwp_dumper_process.write(QtCore.QByteArray(b"\n"))

            self.dumping_dialog.open()
            self.uwpdumper_output.clear()

        if msg is not None:
            self.main_msgbox.setText(msg)
            self.main_msgbox.show()

    @QtCore.Slot()
    def update_uwpdumper_output(self):
        new_output = self.uwp_dumper_process.readAllStandardOutput()
        processed_output = process_uwpdumper_output(new_output.data().decode())

        if "Dump complete" in processed_output:
            self.dumping_status = DumpingStatus.COMPLETE

        current_progress = re.search(r"[0-9]+\/[0-9]+", processed_output)

        if current_progress is not None:
            current_step, max_steps = list(
                map(int, current_progress.group(0).split("/"))
            )
            if current_step == 1:
                self.dumping_progressbar.setMaximum(max_steps)
            elif current_step > 1 and current_step <= max_steps:
                self.dumping_progressbar.setValue(current_step)

        self.uwpdumper_output.append(processed_output)

    @QtCore.Slot()
    def handle_uwpdumper_finished(self):
        if self.dumping_status == DumpingStatus.COMPLETE:
            self.selected_process_data["app_name"]
            self.uwp_dumping_msgbox.setText(
                f"{self.selected_process_data['app_name']} "
                f"successfully dumped to {self.destn_dir.text()}"
            )
            if self.registering_checkbox.isChecked():
                self.continue_btn.show()
        else:
            self.dumping_status = DumpingStatus.ERROR
            self.uwp_dumping_msgbox.setText("Error while dumping")
        self.uwp_dumping_msgbox.show()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = AppWidget(
        uwpdumper_path="C:\\Projects\\_forks\\UWPDumper\\bin\\UWPInjector.exe"
    )
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec_())
