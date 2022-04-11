import typing as t


class NodeUpdates(t.TypedDict):
    id: int  # NOQA: A003
    parent_id: t.Optional[int]
    value: t.Optional[str]


class ExportedCache(t.NamedTuple):
    updates: t.List[NodeUpdates]
    stillborns: t.List[str]
