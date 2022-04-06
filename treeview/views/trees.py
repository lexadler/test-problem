import typing as t
from collections import deque

from PyQt5.Qt import QStandardItem
from PyQt5.Qt import QStandardItemModel
from PyQt5.QtWidgets import QTreeView

from treeview.db import DBNodeModel
from treeview.medium import ExportedCache
from treeview.medium import NodeUpdates
from .items import BaseNodeItem
from .items import CacheViewNodeItem
from .items import DBViewNodeItem


class BaseTreeView(QTreeView):

    _header = 'Base Tree'

    def __init__(self):
        super().__init__()
        self._nodes_map = {}
        self._init_model()

    def _init_model(self):
        self._model = QStandardItemModel()
        self._root = self._model.invisibleRootItem()
        self.setModel(self._model)
        self._model.setHorizontalHeaderItem(
            0, QStandardItem(self._header)
        )

    def _remove_from_map(self, ids: t.Set[int]) -> None:
        for k in ids:
            self._nodes_map.pop(k, None)

    def _remove_item_row(self, item: BaseNodeItem):
        parent = item.parent()
        if parent is None:
            self._root.removeRow(item.row())
        else:
            parent.removeRow(item.row())

    def get_selected_node(self) -> t.Optional[BaseNodeItem]:
        index = next(iter(self.selectedIndexes()), None)
        if index is not None:
            return self._model.itemFromIndex(index)

    def reset_view(self):
        self._nodes_map = {}
        self._init_model()


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
            item = DBViewNodeItem.from_db_model(node)
            parent.appendRow(item)
            self._nodes_map[item.id] = item
        self.expandAll()

    def get_node(self, node_id: int) -> DBViewNodeItem:
        node = self._nodes_map.get(node_id)
        if node is None:
            raise IndexError(
                f'Node with id {node_id} not found in db'
            )
        else:
            return node

    def _import_node(self, node: NodeUpdates) -> None:
        node_id = node['id']
        if node_id in self._nodes_map:
            raise IndexError(
                f'Node with id {node_id} is already in view'
            )
        item = DBViewNodeItem.from_dict(node)
        parent = self.get_node(node['parent_id'])
        parent.appendRow(item)
        self._nodes_map[item.id] = item

    def mark_subtree_for_delete(self, root_node_id: int) -> t.Set[int]:

        deleted_descendants = set()

        def _delete_descendants(item: DBViewNodeItem):
            if item.hasChildren():
                for row in range(item.rowCount()):
                    child = item.child(row, 0)
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
        item = self.get_node(node_id)
        item.set_data(data)

    def update_view(self, saved_cache: ExportedCache) -> None:
        for node_id in sorted(saved_cache.marked_for_delete, reverse=True):
            item = self.get_node(node_id)
            self._remove_item_row(item)
        self._remove_from_map(saved_cache.marked_for_delete)
        for node in saved_cache.updates:
            item = self._nodes_map.get(node['id'])
            if item is not None:
                item.set_unmodifed()
            else:
                self._import_node(node)
        self.expandAll()


class CachedTreeView(BaseTreeView):

    _header = 'Cached Tree'

    def __init__(self, index: int = 1):
        super().__init__()
        self._index = self._init_index = index
        self._marked_for_delete: t.Set[int] = set()

    @staticmethod
    def _add_imported_child(
        parent: QStandardItem,
        item: CacheViewNodeItem
    ) -> None:
        if parent.hasChildren():
            for row in range(parent.rowCount()):
                child = parent.child(row, 0)
                if child.id is None or child.id > item.id:
                    parent.insertRow(row, item)
                    return
        parent.appendRow(item)

    def _reparent_orphaned(self, item: CacheViewNodeItem) -> None:
        for row in range(self._root.rowCount() - 1, -1, -1):
            top_item = self._root.child(row, 0)
            if top_item.id < item.id:
                break
            elif top_item.parent_id == item.id:
                self._root.takeRow(row)
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
        item = CacheViewNodeItem.from_db_model(node)
        self._add_imported_child(parent, item)
        self._nodes_map[item.id] = item
        self._reparent_orphaned(item)
        self.expandAll()

    def add_child_node(self, parent: CacheViewNodeItem, data: str) -> None:
        item = CacheViewNodeItem(
            node_id=None,
            parent_id=parent.id,
            data=data or None
        )
        item.set_unsaved()
        parent.appendRow(item)

    def delete_node(
        self,
        item: CacheViewNodeItem,
        descendants_ids: t.Optional[t.Set[int]] = None
    ):
        if item.in_database():
            self._nodes_map.pop(item.id, None)
            self._marked_for_delete.add(item.id)
            if descendants_ids:
                self._update_deleted_descendants(descendants_ids)
        self._remove_item_row(item)

    def _update_deleted_descendants(self, descendants_ids: t.Set[int]) -> None:
        for row in range(self._root.rowCount() - 1, -1, -1):
            top_item = self._root.child(row, 0)
            if top_item.id in descendants_ids:
                self._root.removeRow(row)
        self._marked_for_delete.update(descendants_ids)
        self._remove_from_map(descendants_ids)

    def save_cache_and_export_changes(self) -> ExportedCache:
        updates = []

        def _export_subtree(item: QStandardItem):
            if item is not self._root:
                if item.in_database():
                    if item.modified:
                        item.set_unmodifed()
                        updates.append(item.to_dict())
                else:
                    self._index += 1
                    item.id = self._index
                    item.parent_id = item.parent().id
                    updates.append(item.to_dict())
                    self._nodes_map[item.id] = item
                    item.set_saved()
            for row in range(item.rowCount()):
                _export_subtree(item.child(row, 0))

        _export_subtree(self._root)
        result = ExportedCache(
            updates=updates,
            marked_for_delete=self._marked_for_delete,
        )
        self._marked_for_delete = set()
        return result

    def reset_view(self):
        super().reset_view()
        self._index = self._init_index
        self._marked_for_delete = set()
