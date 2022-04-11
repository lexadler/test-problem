import typing as t

from PyQt5.Qt import QStandardItem
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QFont

from treeview.db import DBNodeModel
from treeview.medium import NodeUpdates

DEFAULT_FNT = QFont('Open Sans', 12)
STRIKED_FNT = QFont('Open Sans', 12)
STRIKED_FNT.setStrikeOut(True)
UNSAVED_COLOR = QColor(169, 169, 169)
DEFAULT_COLOR = QColor(0, 0, 0)
EDITED_COLOR = QColor(255, 0, 0)


class BaseNodeItem(QStandardItem):

    _null_text = '(no value)'

    def __init__(
        self,
        node_id: t.Optional[int],
        data: t.Optional[str] = None,
    ):
        super().__init__()
        self.id = node_id
        self.setEditable(False)
        self.setForeground(DEFAULT_COLOR)
        self.setFont(DEFAULT_FNT)
        self._set_text(data)

    def _set_text(self, data: t.Optional[str]):
        self.setText(data or self._null_text)

    def __repr__(self) -> str:
        return f'Node(id: {self.id}, data: {self.text()})'

    def in_database(self) -> bool:
        return self.id is not None

    def set_data(self, data: t.Optional[str]) -> None:
        raise NotImplementedError


class DBViewNodeItem(BaseNodeItem):

    def __init__(
        self,
        node_id: int,
        data: t.Optional[str] = None,
    ):
        super().__init__(node_id, data)
        self.deleted = False

    def set_data(self, data: t.Optional[str]) -> None:
        self._set_text(data)

    def set_deleted(self) -> None:
        self.setFont(STRIKED_FNT)
        self.deleted = True

    @classmethod
    def from_dict(cls, node: NodeUpdates) -> 'DBViewNodeItem':
        return cls(
            node['id'],
            node['value'],
        )

    @classmethod
    def from_db_model(cls, node: DBNodeModel) -> 'CacheViewNodeItem':
        return cls(
            node.id,
            node.value,
        )


class CacheViewNodeItem(BaseNodeItem):

    def __init__(
        self,
        node_id: t.Optional[int] = None,
        parent_id: t.Optional[int] = None,
        data: t.Optional[str] = None,
        deleted: bool = False
    ):
        super().__init__(node_id, data)
        self.parent_id = parent_id
        self.data = data
        self.deleted = deleted
        self.modified = False
        self._backup_data: t.Optional[str] = None
        if self.deleted:
            self.setFont(STRIKED_FNT)

    def set_unsaved(self) -> None:
        self.setForeground(UNSAVED_COLOR)

    def set_saved(self) -> None:
        self.setForeground(DEFAULT_COLOR)

    def set_modified(self) -> None:
        self.modified = True
        self.setForeground(EDITED_COLOR)

    def set_unmodifed(self) -> None:
        self.modified = False
        self.setForeground(DEFAULT_COLOR)

    def set_data(self, data: t.Optional[str]) -> None:
        if self.in_database():
            self._backup_data = self.data
            self.set_modified()
        self._set_text(data)
        self.data = data

    def mark_for_delete(self) -> None:
        if self.deleted:
            return
        if self.modified:
            self._set_text(self._backup_data)
            self.data = self._backup_data
            self.set_unmodifed()
        self.deleted = True
        self.setFont(STRIKED_FNT)

    def to_dict(self) -> NodeUpdates:
        if (not self.id or self.id != 1 and not self.parent_id):
            raise NotImplementedError('Node has wrong id values')
        return NodeUpdates(
            id=self.id,
            parent_id=self.parent_id,
            value=self.data,
        )

    @classmethod
    def from_db_model(cls, node: DBNodeModel) -> 'CacheViewNodeItem':
        return cls(
            node.id,
            node.parent_id,
            node.value,
            node.deleted
        )
