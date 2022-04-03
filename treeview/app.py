import sys
import typing as t
from collections import deque

from PyQt5.Qt import QStandardItem
from PyQt5.Qt import QStandardItemModel
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtWidgets import QWidget

from treeview.db import DBConfig
from treeview.db import DBNodeModel
from treeview.db import TreeDBClient

FNT = QFont('Open Sans', 12)
STRIKED_FNT = QFont('Open Sans', 12)
COLOR = QColor(0, 0, 0)
EDITED_COLOR = QColor(255, 0, 0)
TIGHT_BTN_SIZE = QSize(25, 25)
WIDE_BTN_SIZE = QSize(50, 25)

STRIKED_FNT.setStrikeOut(True)


class NarrowButton(QPushButton):

    def __init__(self, text: str):
        super().__init__(text)
        self.setFixedSize(TIGHT_BTN_SIZE)


class WideButton(QPushButton):

    def __init__(self, text: str):
        super().__init__(text)
        self.setFixedSize(WIDE_BTN_SIZE)


class NodeItem(QStandardItem):

    def __init__(
        self,
        node_id: t.Optional[int] = None,
        parent_id: t.Optional[int] = None,
        data: t.Optional[str] = None,
    ):
        super().__init__()
        self.id = node_id
        self.parent_id = parent_id
        self.data = data or None
        self.deleted = False
        self.modified = False
        self._backup: t.Optional[str] = None
        self.setEditable(False)
        self.setForeground(COLOR)
        self.setFont(FNT)
        self.setText(self.data or '(no value)')

    def set_data(self, data: str) -> None:
        self.setText(data)
        if self.id is not None:
            self._backup = self.data
            self.modified = True
            self.setForeground(EDITED_COLOR)
        self.data = data

    def mark_for_delete(self) -> None:
        if self.deleted:
            return
        if self.modified:
            self.data, self._backup = self._backup, None
            self.setText(self.data)
            self.setForeground(COLOR)
        self.deleted = True
        self.setFont(STRIKED_FNT)

    @classmethod
    def from_db_model(cls, node: DBNodeModel) -> 'NodeItem':
        return cls(
            node.id,
            node.parent_id,
            node.node_data
        )


class BaseTreeView(QTreeView):

    _header = 'Base Tree'

    def __init__(self):
        super().__init__()
        self._nodes_map = {}
        self._model = QStandardItemModel()
        self._root = self._model.invisibleRootItem()
        self.setModel(self._model)
        self._model.setHorizontalHeaderItem(
            0, QStandardItem(self._header)
        )

    def _remove_from_map(self, ids: t.Set[int]) -> None:
        for k in ids:
            self._nodes_map.pop(k, None)

    def get_selected_node(self) -> t.Optional[NodeItem]:
        index = next(iter(self.selectedIndexes()), None)
        if index is not None:
            return self._model.itemFromIndex(index)


class DBTreeView(BaseTreeView):

    _header = 'DB Tree'

    def load_data(self, data: t.List[DBNodeModel]) -> None:
        nodes = deque(data)
        while nodes:
            node = nodes.popleft()
            if node.parent_id is None:
                parent = self._root
            else:
                parent = self._nodes_map.get(node.parent_id)
                if parent is None:
                    nodes.append(node)
                    continue
            item = NodeItem.from_db_model(node)
            parent.appendRow(item)
            self._nodes_map[item.id] = item
        self.expandAll()

    def get_node(self, node_id: int) -> NodeItem:
        node = self._nodes_map.get(node_id)
        if node is None:
            raise IndexError(
                f'Node with id {node_id} not found in db'
            )
        else:
            return node

    def mark_subtree_for_delete(self, root_node_id: int) -> t.Set[int]:

        deleted_descendants = set()

        def _delete_descendants(item: NodeItem):
            if item.hasChildren():
                for i in range(item.rowCount()):
                    child = item.child(i, 0)
                    deleted_descendants.add(child.id)
                    if child.deleted:
                        continue
                    child.mark_for_delete()
                    _delete_descendants(child)

        subtree_root = self.get_node(root_node_id)
        subtree_root.mark_for_delete()
        _delete_descendants(subtree_root)

        return deleted_descendants

    def update_value(self, node_id: int, data: str) -> None:
        node = self.get_node(node_id)
        node.set_data(data)


class CachedTreeView(BaseTreeView):

    _header = 'Cached Tree'

    def __init__(self):
        super().__init__()
        self.marked_for_delete: t.Set[int] = set()

    @staticmethod
    def _add_imported_child(parent: QStandardItem, item: NodeItem) -> None:
        if parent.hasChildren():
            for i in range(parent.rowCount()):
                child = parent.child(i, 0)
                if child.id is None or child.id > item.id:
                    parent.insertRow(i, item)
                    return
        parent.appendRow(item)

    def _reparent_orphaned(self, item: NodeItem) -> None:
        for i in range(self._root.rowCount()-1, -1, -1):
            top_item = self._root.child(i, 0)
            if top_item.id < item.id:
                break
            elif top_item.parent_id == item.id:
                self._root.takeRow(i)
                self._add_imported_child(item, top_item)

    def import_node(self, node: DBNodeModel) -> None:
        if node.id in self._nodes_map:
            return
        if node.parent_id is None:
            parent = self._root
        else:
            parent = self._nodes_map.get(node.parent_id)
            if parent is None:
                parent = self._root
        item = NodeItem.from_db_model(node)
        self._add_imported_child(parent, item)
        self._nodes_map[item.id] = item
        self._reparent_orphaned(item)
        self.expandAll()

    def delete_node(self, item: NodeItem) -> bool:
        update_descendants = False
        if item.id in self._nodes_map:
            item.mark_for_delete()
            if item.hasChildren():
                item.removeRows(0, item.rowCount())
            del self._nodes_map[item.id]
            self.marked_for_delete.add(item.id)
            update_descendants = True
        else:
            item.parent().removeRow(item.row())
        return update_descendants

    def update_deleted_descendants(self, descendants_ids: t.Set[int]) -> None:
        for i in range(self._root.rowCount()-1, -1, -1):
            top_item = self._root.child(i, 0)
            if top_item.id in descendants_ids:
                self._root.removeRow(i)
        self.marked_for_delete.update(descendants_ids)
        self._remove_from_map(descendants_ids)


class TreeDBViewApp(QMainWindow):

    def __init__(self, conf: DBConfig):
        super().__init__()
        self.db = TreeDBClient(conf)
        self.db.reset_nodes()
        data = self.db.export_nodes()
        self._index = len(data)
        self.setWindowTitle('TreeDB')
        self.resize(500, 500)
        central_wdg = QWidget()
        self.setCentralWidget(central_wdg)
        layout = QGridLayout(central_wdg)
        self.cache_tree = CachedTreeView()
        self.db_tree = DBTreeView()
        self.db_tree.load_data(data)
        layout.addWidget(self.cache_tree, 0, 0)
        get_node_btn = WideButton('<<<')
        get_node_btn.clicked.connect(self.node_to_cache)
        layout.addWidget(get_node_btn, 0, 1)
        layout.addWidget(self.db_tree, 0, 2)
        cache_btn_layout = QHBoxLayout()
        add_node_btn = NarrowButton('+')
        add_node_btn.clicked.connect(self.add_child_node)
        cache_btn_layout.addWidget(add_node_btn)
        delete_node_btn = NarrowButton('-')
        delete_node_btn.clicked.connect(self.remove_node)
        cache_btn_layout.addWidget(delete_node_btn)
        edit_node_btn = NarrowButton('a')
        edit_node_btn.clicked.connect(self.edit_node)
        cache_btn_layout.addWidget(edit_node_btn)
        cache_btn_layout.addSpacing(10)
        cache_btn_layout.addWidget(WideButton('Apply'))
        cache_btn_layout.addWidget(WideButton('Reset'))
        layout.addLayout(cache_btn_layout, 1, 0)

    def node_to_cache(self) -> None:
        selected_item = self.db_tree.get_selected_node()
        if selected_item is None:
            return
        if selected_item.deleted:
            QMessageBox.warning(
                self,
                'Forbidden operation',
                ('DB tree node is marked for delete.\n'
                    'Can not import to cache.')
            )
            return
        node = self.db.get_node(selected_item.id)
        if node is None:
            raise IndexError(
                f'Node with id {selected_item.id} not found in db'
            )
        self.cache_tree.import_node(node)

    def add_child_node(self) -> None:
        selected_item = self.cache_tree.get_selected_node()
        if selected_item is None:
            return
        if selected_item.deleted:
            QMessageBox.warning(
                self,
                'Forbidden operation',
                'Cached node is marked for delete.\nCan not add child.'
            )
            return
        value, ok = QInputDialog.getText(
            self, 'Set value', 'Enter node value:'
        )
        if ok:
            item = NodeItem(
                node_id=None,
                parent_id=selected_item.id,
                data=value
            )
            selected_item.appendRow(item)
            self.cache_tree.expandAll()

    def remove_node(self) -> None:
        selected_item = self.cache_tree.get_selected_node()
        if selected_item is None:
            return
        update_descendants = self.cache_tree.delete_node(selected_item)
        if update_descendants:
            descendants = self.db_tree.mark_subtree_for_delete(
                selected_item.id
            )
            self.cache_tree.update_deleted_descendants(descendants)

    def edit_node(self) -> None:
        selected_item = self.cache_tree.get_selected_node()
        if selected_item is None:
            return
        if selected_item.deleted:
            QMessageBox.warning(
                self,
                'Forbidden operation',
                'Cached node is marked for delete.\nCan not edit value.'
            )
            return
        value, ok = QInputDialog.getText(
            self, 'Set value', 'Enter node value:'
        )
        if ok and value:
            selected_item.set_data(value)
            if selected_item.id is not None:
                self.db_tree.update_value(selected_item.id, value)


if __name__ == '__main__':
    sys.path.append('..')
    conf = DBConfig(
        username='postgres',
        password='sql',
        host='127.0.0.1',
        port=5432,
        db_name='treedb'
    )
    app = QApplication(sys.argv)
    tree_view_app = TreeDBViewApp(conf)
    tree_view_app.show()
    sys.exit(app.exec_())
