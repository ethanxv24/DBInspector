
# DBInspector

[中文文档](README_zh.md)

DBInspector is a versatile database inspection tool that supports multiple types of databases, including both relational and non-relational databases. It provides a unified interface to inspect, query, and manage different databases efficiently.
A command line script for database health checks.

## Features

- **Multi-Database Support**: Works with various relational databases (e.g., MySQL, PostgreSQL, SQLite) and non-relational databases (e.g., MongoDB, Redis).
- **Unified Interface**: Provides a consistent interface for interacting with different types of databases.
- **Query Execution**: Execute queries and commands across different databases.
- **Schema Inspection**: Inspect database schemas, tables, collections, and indexes.
- **Extensible**: Easily extendable to support additional databases.

## Installation

To install DBInspector, use the following command:

```bash
pip install dbinspector# DBInspector


./dist/main --config=./config/default_config.toml --check-config=./config/postgres_check_item.json --report-format=html --output-report-dir=./report
./dist/main --config=/Users/astro/PycharmProjects/DBInspector/db_inspector/config/default_config.toml --report-format=html --output-report-dir=/Users/astro/PycharmProjects/DBInspector/dist/report


pyinstaller --onefile --add-data "db_inspector/checks:db_inspector/checks" --add-data "db_inspector/config:db_inspector/config" --add-data "db_inspector/connectors:db_inspector/connectors" --add-data "db_inspector/pipelines:db_inspector/pipelines" --add-data "db_inspector/reports:db_inspector/reports" --add-data "db_inspector/utils:db_inspector/utils" --hidden-import=db_inspector.main db_inspector/main.py
