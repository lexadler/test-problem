# DB Tree View

Test application to update database table storing tree data structure.

## Requirements:

1. Python3.8 and Docker CE must be installed on the host.

## Creating test environment:

1. Create virtual environment in the project folder: `python3.8 -m venv venv`
2. Activate virtual environment: `source venv/bin/activate`
3. Install package: `pip install .`
4. Run `sudo docker-compose up -d` from the project folder to create an instance of PostreSQL with the test database.

You can access database in PostgreSQL instance at localhost:5432.

## Usage:

Run `treeview` within an activated virtual environment to start an application for testing purposes. <br>
An application instance will connect to the database in test container by default. <br>
Options to explicitly set connection and database settings with CLI can be checked by running `treeview --help`.

## Removing test environment:

1. Deactivate virtual environment: `deactivate`
2. Remove virtual environment in the project folder: `rm -rf venv`
3. Run `sudo docker-compose down` from the project folder to remove an instance of PostreSQL.
