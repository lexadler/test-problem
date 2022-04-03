import typing as t
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from string import Template

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

    id = sa.Column(sa.Integer, primary_key=True)
    parent_id = sa.Column(sa.Integer, nullable=True)
    node_data = sa.Column(sa.String, nullable=True)
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
    def _default_tree(self) -> t.List[DBNodeModel]:
        return [
            DBNodeModel(id=1, parent_id=None, node_data='Node1'),
            DBNodeModel(id=2, parent_id=1, node_data='Node2'),
            DBNodeModel(id=3, parent_id=1, node_data='Node3'),
            DBNodeModel(id=4, parent_id=3, node_data='Node4'),
            DBNodeModel(id=5, parent_id=1, node_data='Node5'),
            DBNodeModel(id=6, parent_id=5, node_data='Node6'),
            DBNodeModel(id=7, parent_id=4, node_data='Node7'),
            DBNodeModel(id=8, parent_id=4, node_data='Node8'),
        ]

    def reset_nodes(self) -> None:
        self._ensure_table()
        stmt = sa.text(f'TRUNCATE TABLE {DBNodeModel.__tablename__}')
        with self.session() as s:
            s.execute(stmt)
            s.commit()
            s.bulk_save_objects(self._default_tree)
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

    def soft_delete(self, *node_ids: int) -> int:
        with self.session() as s:
            deleted_count = s.query(DBNodeModel).filter(
                DBNodeModel.id.in_(node_ids)
            ).update(
                {'deleted': True},
                synchronize_session='fetch'
            )
            s.commit()
        return deleted_count

    # def add_nodes(self, nodes: t.List[Node]) -> None:
    #     nodes = list(map(
    #         lambda n: DBNodeModel(
    #             id=n.id,
    #             parent_id=n.parent,
    #             name=n.name
    #         ), nodes
    #     ))
    #     with self.session() as s:
    #         s.bulk_save_objects(nodes)
    #         s.commit()
