import re
import sys

from PySide6 import QtCore, QtWidgets

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
        self.uwp_processes_dropdown = QtWidgets.QComboBox()
        self.refresh_btn = QtWidgets.QPushButton("Refresh list")
        self.destn_dir_label = QtWidgets.QLabel("Destination directory")
        self.destn_dir = QtWidgets.QLineEdit()
        self.select_destn_btn = QtWidgets.QPushButton("Select")
        self.dump_btn = QtWidgets.QPushButton("Dump")
        self.dumping_dialog = QtWidgets.QDialog(
            f=QtCore.Qt.WindowMaximizeButtonHint | QtCore.Qt.WindowCloseButtonHint
        )

        # Set widgets properties/data
        self.running_uwp_apps = get_running_uwp_apps()
        self.uwp_processes_dropdown.insertItems(
            0, [elt["image_name"] for elt in self.running_uwp_apps]
        )

        self.destn_dir.setReadOnly(True)

        self.refresh_btn.clicked.connect(self.refresh_list)
        self.select_destn_btn.clicked.connect(self.select_destn_folder)
        self.dump_btn.clicked.connect(self.dump_app)

        # Layout
        self.layout = QtWidgets.QGridLayout(self)

        self.layout.addWidget(
            self.uwp_process_label, 0, 0, 1, 2, alignment=QtCore.Qt.AlignTop
        )
        self.layout.addWidget(
            self.uwp_processes_dropdown, 1, 0, alignment=QtCore.Qt.AlignTop
        )
        self.layout.addWidget(self.refresh_btn, 1, 1, alignment=QtCore.Qt.AlignTop)
        self.layout.addWidget(
            self.destn_dir_label, 2, 0, 1, 2, alignment=QtCore.Qt.AlignTop
        )
        self.layout.addWidget(self.destn_dir, 3, 0, alignment=QtCore.Qt.AlignTop)
        self.layout.addWidget(self.select_destn_btn, 3, 1, alignment=QtCore.Qt.AlignTop)

        self.layout.addWidget(self.dump_btn, 4, 0, 1, 2, alignment=QtCore.Qt.AlignTop)
        self.layout.setRowStretch(3, 1)

        # Dumping dialog
        self.uwpdumper_output = QtWidgets.QTextBrowser()

        self.dumping_dialog.setModal(True)

        self.dumping_dialog_layout = QtWidgets.QGridLayout(self.dumping_dialog)

        self.dumping_dialog_layout.addWidget(QtWidgets.QLabel("UWPDumper output:"))
        self.dumping_dialog_layout.addWidget(self.uwpdumper_output)

    @QtCore.Slot()
    def refresh_list(self):
        self.uwp_processes_dropdown.clear()
        self.running_uwp_apps = get_running_uwp_apps()
        self.uwp_processes_dropdown.insertItems(
            0, [elt["image_name"] for elt in self.running_uwp_apps]
        )

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
