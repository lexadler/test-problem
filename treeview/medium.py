import typing as t


class NodeUpdates(t.TypedDict):
    id: int
    parent_id: t.Optional[int]
    node_data: t.Optional[str] = None
    deleted: bool = False


class ExportedCache(t.NamedTuple):
    updates: t.List[NodeUpdates]
    marked_for_delete: t.Set[int]
