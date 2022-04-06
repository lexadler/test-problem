import typing as t


class NodeUpdates(t.TypedDict):
    id: int  # NOQA: A003
    parent_id: t.Optional[int]
    node_data: t.Optional[str]


class ExportedCache(t.NamedTuple):
    updates: t.List[NodeUpdates]
    marked_for_delete: t.Set[int]
