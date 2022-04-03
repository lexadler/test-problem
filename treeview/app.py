import sys
import typing as t
from collections import deque

from PyQt5.Qt import QStandardItem
from PyQt5.Qt import QStandardItemModel
from PyQt5.QtGui import QColor
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtWidgets import QWidget

from treeview.db import DBConfig
from treeview.db import DBNodeModel
from treeview.db import TreeDBClient

FNT = QFont('Open Sans', 12)
COLOR = QColor(0, 0, 0)


class NodeItem(QStandardItem):

    def __init__(
        self,
        node_id: int,
        parent_id: t.Optional[int],
        data: t.Optional[str] = None
    ):
        super().__init__()
        self.id = node_id
        self.parent_id = parent_id
        self.data = data or f'Node{self.id}'
        self.setEditable(False)
        self.setForeground(COLOR)
        self.setFont(FNT)
        self.setText(self.data)

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


class CachedTreeView(BaseTreeView):

    _header = 'Cached Tree'

    @staticmethod
    def _add_child(parent: QStandardItem, child: NodeItem) -> None:
        if parent.hasChildren():
            for i in range(parent.rowCount()):
                if parent.child(i, 0).id > child.id:
                    parent.insertRow(i, child)
                    return
        parent.appendRow(child)

    def _reparent_orphaned(self, item: NodeItem) -> None:
        for i in range(self._root.rowCount()-1, -1, -1):
            top_item = self._root.child(i, 0)
            if top_item.id < item.id:
                break
            elif top_item.parent_id == item.id:
                self._root.takeRow(top_item.row())
                self._add_child(item, top_item)

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
        self._add_child(parent, item)
        self._nodes_map[item.id] = item
        self._reparent_orphaned(item)
        self.expandAll()


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
        layout = QHBoxLayout(central_wdg)
        self.cache_tree = CachedTreeView()
        self.db_tree = DBTreeView()
        self.db_tree.load_data(data)
        layout.addWidget(self.cache_tree)
        get_node_btn = QPushButton('<<<')
        get_node_btn.clicked.connect(self.node_to_cache)
        layout.addWidget(get_node_btn)
        layout.addWidget(self.db_tree)

    def node_to_cache(self) -> None:
        selected_item = self.db_tree.get_selected_node()
        if selected_item is not None:
            node = self.db.get_node(selected_item.id)
            if node is None:
                raise IndexError(
                    f'Node with id {selected_item.id} not found in db'
                )
            self.cache_tree.import_node(node)


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
