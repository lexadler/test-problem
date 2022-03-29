import typing as t
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from string import Template

from .tree import Node

TEMPLATE_DB_URL = Template(
    'postgresql://$user:$password@$host:$port/$db'
)
DBModelBase = declarative_base()


class DBConfig(t.NamedTuple):
    username: str
    password: str
    host: str
    port: int
    db_name: str


class NodeModel(DBModelBase):
    __tablename__ = 'nodes'

    id = sa.Column(sa.Integer, primary_key=True)
    parent_id = sa.Column(sa.Integer, nullable=True)
    name = sa.Column(sa.String, nullable=True)
    deleted = sa.Column(sa.Boolean, default=False, nullable=False)


class TreeDBClient:

    def __init__(self, conf: DBConfig):
        self.url = TEMPLATE_DB_URL.substitute(
            user=conf.username,
            password=conf.password,
            host=conf.host,
            port=conf.port,
            db=conf.db_name
        )
        self.engine = sa.create_engine(self.url)
        self.session = sessionmaker(bind=self.engine)

    @staticmethod
    def _rows_to_dicts(
        rows: t.List[sa.engine.row.Row]
    ) -> t.List[t.Dict[str, t.Any]]:
        return list(map(lambda row: row._asdict(), rows))

    def _ensure_table(self) -> None:
        DBModelBase.metadata.create_all(self.engine)

    @property
    def _default_tree(self) -> t.List[NodeModel]:
        return [
            NodeModel(id=1, parent_id=None, name='Node1'),
            NodeModel(id=2, parent_id=1, name='Node2'),
            NodeModel(id=3, parent_id=1, name='Node3'),
            NodeModel(id=4, parent_id=3, name='Node4'),
            NodeModel(id=5, parent_id=1, name='Node5'),
            NodeModel(id=6, parent_id=5, name='Node6'),
            NodeModel(id=7, parent_id=4, name='Node7'),
            NodeModel(id=8, parent_id=4, name='Node8'),
        ]

    def reset_nodes(self) -> None:
        self._ensure_table()
        stmt = sa.text(f'TRUNCATE TABLE {NodeModel.__tablename__}')
        with self.session() as s:
            s.execute(stmt)
            s.commit()
            s.bulk_save_objects(self._default_tree)
            s.commit()

    def get_nodes(self) -> t.List[t.Dict[str, t.Any]]:
        with self.session() as s:
            rows = s.query(
                NodeModel.id,
                NodeModel.parent_id,
                NodeModel.name
            ).filter(
                NodeModel.deleted.is_not(True)
            ).all()
        return self._rows_to_dicts(rows)

    def soft_delete(self, *node_ids: int) -> int:
        with self.session() as s:
            deleted_count = s.query(NodeModel).filter(
                NodeModel.id.in_(node_ids)
            ).update(
                {'deleted': True},
                synchronize_session='fetch'
            )
            s.commit()
        return deleted_count

    def add_nodes(self, nodes: t.List[Node]) -> None:
        nodes = list(map(
            lambda n: NodeModel(
                id=n.id,
                parent_id=n.parent,
                name=n.name
            ), nodes
        ))
        with self.session() as s:
            s.bulk_save_objects(nodes)
            s.commit()
