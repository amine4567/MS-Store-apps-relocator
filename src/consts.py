from enum import Enum

from PySide6 import QtGui

ICON_W = 50
ICON_H = 50

XBOX_GREEN = QtGui.QColor(16, 124, 16)


class DumpingStatus(Enum):
    NO_DUMPING = -1
    COMPLETE = 0
    IN_PROGRESS = 1
    ERROR = 2
