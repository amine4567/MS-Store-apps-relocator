import sys
from PySide6 import QtCore, QtWidgets

from uwp import get_running_uwp_apps


class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Widgets definitions
        self.uwp_process_label = QtWidgets.QLabel("UWP process")
        self.uwp_processes_dropdown = QtWidgets.QComboBox()
        self.refresh_btn = QtWidgets.QPushButton("Refresh list")
        self.destn_dir_label = QtWidgets.QLabel("Destination directory")
        self.destn_dir = QtWidgets.QLineEdit()
        self.select_destn_btn = QtWidgets.QPushButton("Select")

        # Set widgets properties/data
        running_uwp_apps = get_running_uwp_apps()
        self.uwp_processes_dropdown.insertItems(
            0, [elt["image_name"] for elt in running_uwp_apps]
        )

        self.destn_dir.setReadOnly(True)

        self.refresh_btn.clicked.connect(self.refresh_list)
        self.select_destn_btn.clicked.connect(self.select_destn_folder)

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

        self.layout.setRowStretch(3, 1)

    @QtCore.Slot()
    def refresh_list(self):
        self.uwp_processes_dropdown.clear()
        running_uwp_apps = get_running_uwp_apps()
        self.uwp_processes_dropdown.insertItems(
            0, [elt["image_name"] for elt in running_uwp_apps]
        )

    @QtCore.Slot()
    def select_destn_folder(self):
        destn_dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            None, "Select a folder:", "C:\\", QtWidgets.QFileDialog.ShowDirsOnly
        )
        self.destn_dir.setText(destn_dir_path)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec_())
