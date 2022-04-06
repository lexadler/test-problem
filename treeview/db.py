import typing as t
from string import Template

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .medium import NodeUpdates

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


class DBNodeModel(DBModelBase):
    __tablename__ = 'nodes'

    id = sa.Column(sa.Integer, primary_key=True)  # NOQA: A003
    parent_id = sa.Column(sa.Integer, nullable=True)
    node_data = sa.Column(sa.String, nullable=True)
    deleted = sa.Column(sa.Boolean, default=False, nullable=False)


DEFAULT_TREE = [
    DBNodeModel(id=1, parent_id=None, node_data='Node1'),
    DBNodeModel(id=2, parent_id=1, node_data='Node2'),
    DBNodeModel(id=3, parent_id=1, node_data='Node3'),
    DBNodeModel(id=4, parent_id=3, node_data='Node4'),
    DBNodeModel(id=5, parent_id=1, node_data='Node5'),
    DBNodeModel(id=6, parent_id=5, node_data='Node6'),
    DBNodeModel(id=7, parent_id=4, node_data='Node7'),
    DBNodeModel(id=8, parent_id=4, node_data='Node8'),
]


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

    def _ensure_table(self) -> None:
        DBModelBase.metadata.create_all(self.engine)

    def reset_table(self) -> None:
        self._ensure_table()
        stmt = sa.text(f'TRUNCATE TABLE {DBNodeModel.__tablename__}')
        with self.session() as s:
            s.execute(stmt)
            s.commit()
            s.bulk_save_objects(DEFAULT_TREE)
            s.commit()

    def export_nodes(self) -> t.List[DBNodeModel]:
        with self.session() as s:
            nodes = s.query(DBNodeModel).filter(
                DBNodeModel.deleted.is_not(True)
            ).all()
        return nodes

    def get_node(self, node_id: int) -> t.Optional[DBNodeModel]:
        with self.session() as s:
            node = s.query(DBNodeModel).get(node_id)
        return node

    def update_table(self, updates: t.List[NodeUpdates]):
        """Performs bulk upsert of new and updated nodes to database
        """
        if not updates:
            return
        insert_stmt = insert(DBNodeModel).values(updates)
        update_stmt = insert_stmt.on_conflict_do_update(
            index_elements=[DBNodeModel.id],
            set_={
                'node_data': insert_stmt.excluded.node_data,
            }
        )
        with self.session() as s:
            s.execute(update_stmt)
            s.commit()

    def soft_delete(self, *node_ids: int) -> int:
        if not node_ids:
            return 0
        with self.session() as s:
            deleted_count = s.query(DBNodeModel).filter(
                DBNodeModel.id.in_(node_ids)
            ).update(
                {'deleted': True},
                synchronize_session='fetch'
            )
            s.commit()
        return deleted_count
