from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QMessageBox


class BaseQuestionMBox(QMessageBox):
    _title = ''
    _text = 'Are you sure?'

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setWindowTitle(self._title)
        self.setText(self._text)
        self.setIcon(QMessageBox.Icon.Question)
        self.setStandardButtons(self.Yes | self.No)
        self.setDefaultButton(self.No)
        cb = QCheckBox("Don't show this again", self)
        self.setCheckBox(cb)

    def enabled(self) -> bool:
        return not self.checkBox().isChecked()


class DBNodeDeletionMBox(BaseQuestionMBox):
    _title = 'Mark node for deletion'
    _text = (
        "Selected node and all it's descendants\n"
        'in database will be marked for deletion.\n'
        'Unsaved descendants will be removed in a moment.\n'
        'Database changes will be applied upon\n'
        "clicking 'Apply' button.\n\n"
        'Are you sure to delete this node?\n'
    )


class UnsavedNodeDeletionMBox(BaseQuestionMBox):
    _title = 'Delete node'
    _text = (
        "Selected node and all it's descendants\n"
        'will be removed in a moment.\n\n'
        'Are you sure to delete this node?\n'
    )
