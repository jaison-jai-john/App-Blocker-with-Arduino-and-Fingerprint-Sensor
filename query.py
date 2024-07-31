from sql_metadata import parser


class Query:
    def __init__(self, db, query: str) -> None:
        self.db = db
        self.query = query
        self.read = True
        self.cursor = self.db.cursor

    def execute(self):
        print(self.query)
        # execute the query
        self.cursor.execute(self.query + ";")
        # commit the changes
        if not self.read:
            self.db.conn.commit()
            return []

        # convert results
        columns = [column[0] for column in self.cursor.description]
        results = self.cursor.fetchall()
        results = [Record(**dict(zip(columns, result))) for result in results]
        print(results)
        # return the results
        return results

    def select(self, fields=None):
        if not fields:
            fields = ["*"]
        # add the select clause
        self.query += f"SELECT {', '.join(fields)}"
        return self

    def from_table(self, table: str):
        # add the from clause
        self.query += f" FROM {table}"
        return self

    def insert(self, table_name, **fields):
        # add the insert clause
        self.query += f"INSERT INTO {table_name}"
        # add the fields
        self.query += f"({', '.join(fields.keys())})"
        self.read = False
        return self

    def values(self, values_list):
        # add the values clause
        self.query += f" VALUES "
        for values in values_list:
            # add the values, add strings with quotes if the value is a string else add the value
            self.query += f"({', '.join([f"'{value}'" if isinstance(value, str) else str(value) for value in values])}), "
        # remove the last ','
        self.query = self.query[:-2]
        self.read = False
        return self

    def update(self, table: str, **fields):
        # add the update clause
        self.query += f"UPDATE {table} SET "
        # add the fields
        for field, value in fields.items():
            self.query += f"{field} = {value}, "
        # remove the last ','
        self.query = self.query[:-2]
        self.read = False
        return self

    def delete(self, table: str):
        # add the delete clause
        self.query += f"DELETE FROM {table}"
        self.read = False
        return self

    def __where__(self):
        # check if where clause exists
        if "WHERE" not in self.query:
            self.query += " WHERE "

    def equals(self, **fields):
        # add the where clause
        self.__where__()
        # add the fields
        for field, value in fields.items():
            self.query += f"{field} = {f'"{value}"' if isinstance(value,str) else f'({value.__str__()})' if isinstance(value,self.__class__) else value} AND "
        # remove the last 'AND'
        self.query = self.query[:-4]
        return self

    def greater(self, **fields):
        # add the where clause
        self.__where__()
        # add the fields
        for field, value in fields.items():
            self.query += f"{field} > {value} AND "
        # remove the last 'AND'
        self.query = self.query[:-4]
        return self

    def lesser(self, **fields):
        # add the where clause
        self.__where__()
        # add the fields
        for field, value in fields.items():
            self.query += f"{field} < {value} AND "
        # remove the last 'AND'
        self.query = self.query[:-4]
        return self

    def like(self, **fields):
        # add the where clause
        self.__where__()
        # add the fields
        for field, value in fields.items():
            self.query += f"{field} LIKE '{value}' AND "
        # remove the last 'AND'
        self.query = self.query[:-4]
        return self

    def limit(self, limit: int):
        # add the limit clause
        self.query += f" LIMIT {limit}"
        return self

    def order(self, field: str, asc=True):
        # add the order clause
        self.query += f" ORDER BY {field} {'ASC' if asc else 'DESC'}"
        return self

    def group(self, field: str):
        # add the group clause
        self.query += f" GROUP BY {field}"
        return self

    def having(self, field: str, condition: str, value: int):
        # add the having clause
        self.query += f" HAVING {field} {condition} {value}"
        return self

    def join(self, table: str, field: str, join: str):
        # add the join clause
        # multiple fields and joins
        if isinstance(field, list):
            self.query += f" JOIN {table} ON {' AND '.join([f'{f} = {j}' for f, j in zip(field, join)])}"
        else:
            self.query += f" JOIN {table} ON {field} = {join}"
        return self

    def inner_join(self, table: str, field: str, join: str):
        # add the inner join clause
        self.query += f" INNER JOIN {table} ON {field} = {join}"
        return self

    def left_join(self, table: str, field: str, join: str):
        # add the left join clause
        self.query += f" LEFT JOIN {table} ON {field} = {join}"
        return self

    def right_join(self, table: str, field: str, join: str):
        # add the right join clause
        self.query += f" RIGHT JOIN {table} ON {field} = {join}"
        return self

    def full_join(self, table: str, field: str, join: str):
        # add the full join clause
        self.query += f" FULL JOIN {table} ON {field} = {join}"
        return self

    def union(self, query: str):
        # add the union clause
        self.query += f" UNION {query}"
        return self

    def union_all(self, query: str):
        # add the union all clause
        self.query += f" UNION ALL {query}"
        return self
    def __str__(self):
        return self.query


class Record:
    def __init__(self, **values):
        for key, value in values.items():
            self.__setattr__(key, value)
