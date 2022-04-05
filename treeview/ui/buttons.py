import typing as t

from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QPushButton


class BaseButton(QPushButton):
    _size = QSize(10, 10)

    def __init__(self, text: str, func: t.Callable):
        super().__init__(text)
        self.setFixedSize(self._size)
        self.clicked.connect(func)


class NarrowButton(BaseButton):
    _size = QSize(25, 25)


class WideButton(BaseButton):
    _size = QSize(50, 25)
