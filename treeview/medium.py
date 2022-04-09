import typing as t


class NodeUpdates(t.TypedDict):
    id: int  # NOQA: A003
    parent_id: t.Optional[int]
    ancestry: t.Optional[str]
    value: t.Optional[str]


class ExportedCache(t.NamedTuple):
    updates: t.List[NodeUpdates]
    deleted_subtree_roots: t.Set[int]
