import re
import sys

from PySide6 import QtCore, QtWidgets, QtGui

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


class MyWidget(QtWidgets.QWidget):
    def __init__(self, uwpdumper_path: str):
        super().__init__()

        self.uwpdumper_path = uwpdumper_path

        # Widgets definitions
        self.uwp_process_label = QtWidgets.QLabel("UWP process")
        self.uwp_process = QtWidgets.QLineEdit()
        self.select_uwp_btn = QtWidgets.QPushButton("Select")
        self.uwp_selecting_dialog = QtWidgets.QDialog(
            f=QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.WindowCloseButtonHint
        )
        self.uwp_processes_dropdown = QtWidgets.QComboBox()
        self.refresh_btn = QtWidgets.QPushButton("Refresh list")
        self.destn_dir_label = QtWidgets.QLabel("Destination directory")
        self.destn_dir = QtWidgets.QLineEdit()
        self.select_destn_btn = QtWidgets.QPushButton("Browse")
        self.dump_btn = QtWidgets.QPushButton("Dump")
        self.dumping_dialog = QtWidgets.QDialog(
            f=QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.WindowCloseButtonHint
        )

        # Set widgets properties/data
        self.destn_dir.setReadOnly(True)

        self.select_uwp_btn.clicked.connect(self.select_uwp_process)
        self.refresh_btn.clicked.connect(self.refresh_list)
        self.select_destn_btn.clicked.connect(self.select_destn_folder)
        self.dump_btn.clicked.connect(self.dump_app)

        # Layout
        self.layout = QtWidgets.QGridLayout(self)

        self.layout.addWidget(
            self.uwp_process_label, 0, 0, 1, 2, alignment=QtCore.Qt.AlignTop
        )
        self.layout.addWidget(self.uwp_process, 1, 0, alignment=QtCore.Qt.AlignTop)
        self.layout.addWidget(self.select_uwp_btn, 1, 1, alignment=QtCore.Qt.AlignTop)
        self.layout.addWidget(
            self.destn_dir_label, 2, 0, 1, 2, alignment=QtCore.Qt.AlignTop
        )
        self.layout.addWidget(self.destn_dir, 3, 0, alignment=QtCore.Qt.AlignTop)
        self.layout.addWidget(self.select_destn_btn, 3, 1, alignment=QtCore.Qt.AlignTop)

        self.layout.addWidget(self.dump_btn, 4, 0, 1, 2, alignment=QtCore.Qt.AlignTop)
        self.layout.setRowStretch(3, 1)

        # Selecting UWP process dialog
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
        cols_header = ["PID", "Icon", "Process", "Executable path"]
        self.running_uwp_apps_table.setColumnCount(len(cols_header))
        self.running_uwp_apps_table.setHorizontalHeaderLabels(cols_header)

        self.update_running_uwp_table()

        self.running_uwp_apps_table.resizeRowsToContents()
        self.running_uwp_apps_table.resizeColumnsToContents()

        self.uwp_selecting_dialog.setModal(True)

        self.uwp_selecting_layout = QtWidgets.QGridLayout(self.uwp_selecting_dialog)

        self.uwp_selecting_layout.addWidget(self.running_uwp_apps_table)
        self.uwp_selecting_layout.addWidget(self.refresh_btn)

        # Dumping dialog
        self.uwpdumper_output = QtWidgets.QTextBrowser()

        self.dumping_dialog.setModal(True)

        self.dumping_dialog_layout = QtWidgets.QGridLayout(self.dumping_dialog)

        self.dumping_dialog_layout.addWidget(QtWidgets.QLabel("UWPDumper output:"))
        self.dumping_dialog_layout.addWidget(self.uwpdumper_output)

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

            pixmap = QtGui.QPixmap(running_app_data["logo_fullpath"])
            icon_item = QtWidgets.QTableWidgetItem()
            icon_item.setIcon(QtGui.QIcon(pixmap))
            self.running_uwp_apps_table.setItem(i, 1, icon_item)

            self.running_uwp_apps_table.setItem(
                i, 2, QtWidgets.QTableWidgetItem(running_app_data["image_name"])
            )
            self.running_uwp_apps_table.setItem(
                i, 3, QtWidgets.QTableWidgetItem(running_app_data["executable_path"])
            )

    @QtCore.Slot()
    def refresh_list(self):
        self.uwp_processes_dropdown.clear()
        self.update_running_uwp_table()

    @QtCore.Slot()
    def select_uwp_process(self):
        self.uwp_selecting_dialog.show()

    @QtCore.Slot()
    def select_destn_folder(self):
        destn_dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            None, "Select a folder:", "C:\\", QtWidgets.QFileDialog.ShowDirsOnly
        )
        self.destn_dir.setText(destn_dir_path)

    @QtCore.Slot()
    def dump_app(self):
        app_pid = self.running_uwp_apps[self.uwp_processes_dropdown.currentIndex()][
            "pid"
        ]

        self.uwp_dumper_process = QtCore.QProcess()
        self.uwp_dumper_process.readyReadStandardOutput.connect(
            self.update_uwpdumper_output
        )

        self.uwp_dumper_process.start(
            self.uwpdumper_path,
            ["-p", str(app_pid), "-d", self.destn_dir.text().replace("/", "\\")],
        )

        # UWPDumper expects a user input when the dump is done
        self.uwp_dumper_process.write(QtCore.QByteArray(b"\n"))

        self.dumping_dialog.show()
        self.uwpdumper_output.clear()

    @QtCore.Slot()
    def update_uwpdumper_output(self):
        new_output = self.uwp_dumper_process.readAllStandardOutput()
        processed_output = process_uwpdumper_output(new_output.data().decode())
        self.uwpdumper_output.append(processed_output)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MyWidget(
        uwpdumper_path="C:\\Games\\_Tools\\UWPDumper-x64\\UWPInjector.exe"
    )
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec_())
