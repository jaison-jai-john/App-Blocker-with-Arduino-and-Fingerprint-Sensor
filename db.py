import mysql.connector

from query import Query


class DB:
    def __init__(self, username, password, database=None, log=False) -> None:
        self.username = username
        self.password = password
        self.database = database
        self.logging = log
        self.conn = mysql.connector.connect(
            user=self.username,
            password=self.password,
            database=self.database if self.database else "",
        )
        self.cursor = self.conn.cursor()

    def log(self, *message) -> None:
        if self.logging:
            print(message)
    
    def use(self, database) -> None:
        # check if database exists
        if not self.__database_exists__(database):
            
            self.log(f"Database {database} does not exist")
            return None

        # use the database
        self.cursor.execute(f"USE {database}")
        self.database = database

    def __databases__(self) -> list:
        # get all databases
        self.cursor.execute("SHOW DATABASES;")
        databases = self.cursor.fetchall()
        self.log(databases)
        return [db[0] for db in databases]

    def __database_exists__(self, database_name: str) -> bool:
        # check if database exists
        databases = self.__databases__()
        self.log(f'{database_name} {'exists' if database_name in databases else 'does not exist'}')
        return database_name in databases

    def create_database(self, database_name: str) -> None:
        # check if database exists
        if self.__database_exists__(database_name):
            self.log(f"Database {database_name} already exists")
            return None

        # create the database
        self.cursor.execute(f"CREATE DATABASE {database_name};")
        # save the changes
        self.log(self.cursor.fetchall())
        self.conn.commit()

    def __table_exists__(self, table_name: str) -> bool:
        # check if table exists
        if table_name in self.__tables__():
            self.log(f"Table {table_name} already exists")
            return True
        return False

    def __tables__(self) -> list:
        # get all tables
        self.cursor.execute("SHOW TABLES;")
        tables = self.cursor.fetchall()
        self.log(tables)
        return [table[0] for table in tables]

    def __scan_tables__(self) -> None:
        # check if database exists
        if not self.database:
            return None
        # scan all tables
        for table in self.__tables__():
            self.__scan_table__(table)

    def __scan_table__(self, table_name: str) -> None:
        # check if database exists
        if not self.database:
            return None
        # get all columns
        self.cursor.execute(f"DESC {table_name};")
        columns = self.cursor.fetchall()
        self.tables[table_name] = {column[0]: column[1] for column in columns}

    def __describe_table__(self, table_name: str) -> dict:
        # check if database exists
        if not self.database:
            return None
        # get all columns
        self.cursor.execute(f"DESC {table_name};")
        columns = self.cursor.fetchall()
        for column in columns:
            self.log(*column)
        return {column[0]: column[1] for column in columns}
    
    def create_table(self, table_name: str, columns: dict, constraints=[]) -> None:
        # check if database exists
        if not self.database:
            self.log("No database selected")
            return None

        # check if table exists
        if self.__table_exists__(table_name):
            self.__describe_table__(table_name)
            return
        # create the table
        self.log(f"Creating table {table_name}")
        query = f"CREATE TABLE {table_name} ("
        for column in columns:
            query += f"{column} {columns[column]["data_type"]} {" ".join(columns[column]["keys"]) if columns[column].get("keys") else ""}, "
        # add constraints of the table
        for constraint in constraints:
            query += f"{constraint}, "
        query = query[:-2] + ");"
        self.log(query)
        self.cursor.execute(query)
        self.log(self.cursor.fetchall())
        # save the changes
        self.conn.commit()
        self.log(f"Table {table_name} created")

    def drop_table(self, table_name: str) -> None:
        # check if database exists
        if not self.database:
            self.log("No database selected")
            return None

        # drop the table
        self.cursor.execute(f"DROP TABLE {table_name};")
        self.log(self.cursor.fetchall())
        # save the changes
        self.conn.commit()
        # scan the tables
        del self.tables[table_name]

    def query(self) -> Query:
        return Query(self, "")
