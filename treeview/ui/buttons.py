import typing as t

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QPushButton

TIGHT_BTN_SIZE = QSize(25, 25)
WIDE_BTN_SIZE = QSize(50, 25)


class BaseButton(QPushButton):

    def __init__(self, text: str, func: t.Callable):
        super().__init__(text)
        self.clicked.connect(func)


class NarrowButton(BaseButton):

    def __init__(self, text: str, func: t.Callable):
        super().__init__(text, func)
        self.setFixedSize(TIGHT_BTN_SIZE)


class WideButton(BaseButton):

    def __init__(self, text: str, func: t.Callable):
        super().__init__(text, func)
        self.setFixedSize(WIDE_BTN_SIZE)
