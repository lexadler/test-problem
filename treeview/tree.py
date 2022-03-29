import typing as t
from dataclasses import dataclass


@dataclass
class Node:
    id: int
    parent: int
    name: t.Optional[str] = None

    def __post_init__(self):
        if self.name is None:
            self.name = f'Node{self.id}'
