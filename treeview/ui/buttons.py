from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QPushButton

TIGHT_BTN_SIZE = QSize(25, 25)
WIDE_BTN_SIZE = QSize(50, 25)


class NarrowButton(QPushButton):

    def __init__(self, text: str):
        super().__init__(text)
        self.setFixedSize(TIGHT_BTN_SIZE)


class WideButton(QPushButton):

    def __init__(self, text: str):
        super().__init__(text)
        self.setFixedSize(WIDE_BTN_SIZE)
