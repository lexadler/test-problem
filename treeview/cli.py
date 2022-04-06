import sys

import click
from PyQt5.QtWidgets import QApplication

from .app import TreeDBViewApp
from .db import DBConfig


@click.command()
@click.option('--host', type=click.STRING,
              default='127.0.0.1', help='Postgres server host')
@click.option('--port', type=click.INT,
              default=5432, help='Postgres server port')
@click.option('--username', type=click.STRING,
              default='postgres', help='Postgres user')
@click.option('--password', type=click.STRING,
              default='sql', help='Postgres password')
@click.option('--database', type=click.STRING,
              default='treedb', help='Postgres DB name')
@click.pass_context
def cli(
    ctx: click.Context,
    host: str,
    port: int,
    username: str,
    password: str,
    database: str,
):
    conf = DBConfig(
        username=username,
        password=password,
        host=host,
        port=port,
        db_name=database
    )
    app = QApplication(sys.argv)
    main_window = TreeDBViewApp(conf)
    main_window.show()
    sys.exit(app.exec_())
