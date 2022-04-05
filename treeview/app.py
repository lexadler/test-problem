import sys

from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QWidget

from treeview.db import DBConfig
from treeview.db import DEFAULT_TREE
from treeview.db import TreeDBClient
from treeview.ui.buttons import NarrowButton
from treeview.ui.buttons import WideButton
from treeview.ui.modal import DBNodeDeletionMBox
from treeview.ui.modal import ResetAllMBox
from treeview.ui.modal import UnsavedNodeDeletionMBox
from treeview.views.trees import CachedTreeView
from treeview.views.trees import DBTreeView


class TreeDBViewApp(QMainWindow):

    def __init__(self, conf: DBConfig):
        super().__init__()
        self.setWindowTitle('TreeDB')
        self.resize(500, 500)
        central_wdg = QWidget()
        self.setCentralWidget(central_wdg)
        self.layout = QGridLayout(central_wdg)
        self.db_deletion_mbox = DBNodeDeletionMBox(self)
        self.cache_deletion_mbox = UnsavedNodeDeletionMBox(self)
        self.reset_mbox = ResetAllMBox(self)
        self.db = TreeDBClient(conf)
        self.db.reset_table()

        self.cache_tree = CachedTreeView(index=len(DEFAULT_TREE))
        self.db_tree = DBTreeView()
        self.db_tree.load_data(DEFAULT_TREE)

        self.layout.addWidget(self.cache_tree, 0, 0)
        get_node_btn = WideButton('<<<', self.node_to_cache)
        self.layout.addWidget(get_node_btn, 0, 1)
        self.layout.addWidget(self.db_tree, 0, 2)
        self._construct_lower_layout()

    def _construct_lower_layout(self):
        btn_layout = QHBoxLayout()
        cache_buttons = [
            NarrowButton('+', self.add_child_node),
            NarrowButton('-', self.remove_node),
            NarrowButton('a', self.edit_node)
        ]
        ops_buttons = [
            WideButton('Apply', self.apply_changes),
            WideButton('Reset', self.reset_all)
        ]
        for b in cache_buttons:
            btn_layout.addWidget(b)
        btn_layout.addSpacing(10)
        for b in ops_buttons:
            btn_layout.addWidget(b)
        self.layout.addLayout(btn_layout, 1, 0)

    def _input_value_modal(self):
        value, ok = QInputDialog.getText(
            self, 'Set value', 'Enter node value:'
        )
        return value, ok

    def node_to_cache(self) -> None:
        selected_item = self.db_tree.get_selected_node()
        if selected_item is None:
            return
        if selected_item.deleted:
            QMessageBox.warning(
                self,
                'Forbidden operation',
                ('DB tree node is marked for deletion.\n'
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
        value, ok = self._input_value_modal()
        if ok:
            self.cache_tree.add_child_node(selected_item, value)
            self.cache_tree.expandAll()

    def remove_node(self) -> None:
        selected_item = self.cache_tree.get_selected_node()
        if selected_item is None:
            return
        descendants = None
        if selected_item.in_database():
            if self.db_deletion_mbox.enabled():
                if self.db_deletion_mbox.exec() != QMessageBox.Yes:
                    return
            descendants = self.db_tree.mark_subtree_for_delete(
                selected_item.id
            )
        else:
            if self.cache_deletion_mbox.enabled():
                if self.cache_deletion_mbox.exec() != QMessageBox.Yes:
                    return
        self.cache_tree.delete_node(selected_item, descendants)

    def edit_node(self) -> None:
        selected_item = self.cache_tree.get_selected_node()
        if selected_item is None:
            return
        value, ok = self._input_value_modal()
        if ok and value:
            selected_item.set_data(value)
            if selected_item.id is not None:
                self.db_tree.update_value(selected_item.id, value)

    def apply_changes(self) -> None:
        saved_cache = self.cache_tree.save_cache_and_export_changes()
        self.db.update_table(saved_cache.updates)
        self.db.soft_delete(*saved_cache.marked_for_delete)
        self.db_tree.update_view(saved_cache)

    def reset_all(self) -> None:
        if self.reset_mbox.enabled():
            if self.reset_mbox.exec() != QMessageBox.Yes:
                return
        self.cache_tree.reset_view()
        self.db_tree.reset_view()
        self.db_tree.load_data(DEFAULT_TREE)
        self.db.reset_table()


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
