import typing as t

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
        cache_buttons = (
            NarrowButton('+', self.add_child_node),
            NarrowButton('-', self.remove_node),
            NarrowButton('a', self.edit_node)
        )
        ops_buttons = (
            WideButton('Apply', self.apply_changes),
            WideButton('Reset', self.reset_all)
        )
        for b in cache_buttons:
            btn_layout.addWidget(b)
        btn_layout.addSpacing(10)
        for b in ops_buttons:
            btn_layout.addWidget(b)
        self.layout.addLayout(btn_layout, 1, 0)

    def _input_value_modal(self) -> t.Tuple[str, bool]:
        value, ok = QInputDialog.getText(
            self, 'Set value', 'Enter node value:'
        )
        return value, ok

    def _stillborns_message(
        self,
        message: str,
        stillborns: t.List[str]
    ) -> None:
        stillborns_ = '\n'.join(stillborns)
        text = f'{message}:\n\n{stillborns_}'
        QMessageBox.warning(
            self,
            'Warning message',
            text
        )

    def node_to_cache(self) -> None:
        selected_item = self.db_tree.get_selected_node()
        if selected_item is None:
            return
        node = self.db.get_node(selected_item.id)
        if node is None:
            raise IndexError(
                f'Node with id {selected_item.id} not found in db'
            )
        stillborns = self.cache_tree.import_node(node)
        if stillborns:
            self._stillborns_message(
                'Following unsaved nodes were deleted\n'
                "as it's orphaned descendants turned out\n"
                'to be marked for deletion',
                stillborns
            )

    def add_child_node(self) -> None:
        selected_item = self.cache_tree.get_selected_node()
        if selected_item is None:
            return
        if selected_item.deleted:
            QMessageBox.warning(
                self,
                'Forbidden operation',
                ('Cache node is deleted\n'
                 'or marked for deletion.\n'
                 'Can not add child.')
            )
            return
        value, ok = self._input_value_modal()
        if ok:
            self.cache_tree.add_child_node(selected_item, value)
            self.cache_tree.expandAll()

    def remove_node(self) -> None:
        selected_item = self.cache_tree.get_selected_node()
        if selected_item is None or selected_item.deleted:
            return
        if selected_item.in_database():
            if self.db_deletion_mbox.enabled():
                if self.db_deletion_mbox.exec() != QMessageBox.Yes:
                    return
        else:
            if self.cache_deletion_mbox.enabled():
                if self.cache_deletion_mbox.exec() != QMessageBox.Yes:
                    return
        stillborns = self.cache_tree.delete_node(selected_item)
        if stillborns:
            self._stillborns_message(
                'Following unsaved nodes were be deleted\n'
                "as it's descendants were marked for deletion",
                stillborns
            )

    def edit_node(self) -> None:
        selected_item = self.cache_tree.get_selected_node()
        if selected_item is None:
            return
        if selected_item.deleted:
            QMessageBox.warning(
                self,
                'Forbidden operation',
                ('Cache node is deleted\n'
                 'or marked for deletion.\n'
                 'Can not set new value.')
            )
            return
        value, ok = self._input_value_modal()
        if ok and value:
            selected_item.set_data(value)

    def apply_changes(self) -> None:
        deleted_ids = self.db_tree.delete_subtrees(
            self.cache_tree.deleted_subtree_roots
        )
        self.db.soft_delete(*deleted_ids)
        saved_cache = self.cache_tree.save_cache_and_export_changes(deleted_ids)
        self.db.update_table(saved_cache.updates)
        self.db_tree.update_view(saved_cache.updates)
        if saved_cache.stillborns:
            self._stillborns_message(
                'Following unsaved nodes were deleted\n'
                "as it's orphaned descendants turned out\n"
                'to be deleted',
                saved_cache.stillborns
            )

    def reset_all(self) -> None:
        if self.reset_mbox.enabled():
            if self.reset_mbox.exec() != QMessageBox.Yes:
                return
        self.cache_tree.reset_view()
        self.db_tree.reset_view()
        self.db_tree.load_data(DEFAULT_TREE)
        self.db.reset_table()
