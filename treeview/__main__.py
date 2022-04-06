from treeview.cli import cli


def main(name: str = None):
    cli(obj={},
        help_option_names=['-h', '--help'],
        auto_envvar_prefix='DB_TREE_VIEW',
        prog_name=name)


if __name__ == '__main__':
    main('python -m ' + __package__)
