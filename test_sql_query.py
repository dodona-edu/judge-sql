import unittest
from sql_query import SQLQuery


class TestSQLQuery(unittest.TestCase):
    def test_from_raw_input_1(self):
        queries = SQLQuery.from_raw_input(
            """
            -- First query:
            SELECT * FROM USERS WHERE ";#" = 1;
            -- 2nd query:
            SELECT 1 # random comment
        """
        )

        self.assertEqual(
            queries[0].canonical, 'SELECT *\nFROM USERS\nWHERE ";#" = 1'
        )
        self.assertEqual(queries[0].has_ending_semicolon(), True)
        self.assertEqual(queries[1].canonical, "SELECT 1")
        self.assertEqual(queries[1].has_ending_semicolon(), False)

    def test_from_raw_input_2(self):
        queries = SQLQuery.from_raw_input("\n\r")
        self.assertEqual(len(queries), 0)

    def test_SQLQuery_1(self):
        query = SQLQuery('SELECT * FROM USERS WHERE ";" = 1 ORDER BY NAME ASC;')

        self.assertEqual(
            query.canonical,
            'SELECT *\nFROM USERS\nWHERE ";" = 1\nORDER BY NAME ASC',
        )
        self.assertEqual(query.has_ending_semicolon(), True)
        self.assertEqual(query.is_select(), True)
        self.assertEqual(query.is_ordered(), True)

    def test_SQLQuery_2(self):
        query = SQLQuery(
            '--SELECT\n   INSERT INTO TABLE2 /**/  SELECT * FROM Users WHERE ";#ORDER BY" = 1;'
        )

        self.assertEqual(
            query.canonical,
            'INSERT INTO TABLE2\nSELECT *\nFROM USERS\nWHERE ";#ORDER BY" = 1',
        )
        self.assertEqual(query.has_ending_semicolon(), True)
        self.assertEqual(query.is_select(), False)
        self.assertEqual(query.is_ordered(), False)

    def test_canonical(self):
        query = SQLQuery("\n  SELECT\n*\tFROM   USERS  \n\r")
        self.assertEqual(query.canonical, "SELECT *\nFROM USERS")

        query = SQLQuery(
            """
        SELECT *
            FROM USERS
        """
        )
        self.assertEqual(query.canonical, "SELECT *\nFROM USERS")

        query = SQLQuery(
            """
        --SELECT ALL:
        SELECT * FROM CUSTOMERS;
        """
        )
        self.assertEqual(query.canonical, "SELECT *\nFROM CUSTOMERS")

        query = SQLQuery(
            """
        SELECT * FROM CUSTOMERS; --SELECT ALL:"""
        )
        self.assertEqual(query.canonical, "SELECT *\nFROM CUSTOMERS")

        query = SQLQuery(
            """
        # Select all:
        SELECT * FROM CUSTOMERS;"""
        )
        self.assertEqual(query.canonical, "SELECT *\nFROM CUSTOMERS")

        query = SQLQuery(
            """
        SELECT * FROM CUSTOMERS; # Select all:"""
        )
        self.assertEqual(query.canonical, "SELECT *\nFROM CUSTOMERS")

        query = SQLQuery(
            """
        /* Select all employees whose compensation is
        greater than that of Pataballa. */
        SELECT * FROM CUSTOMERS; # Select all:"""
        )
        self.assertEqual(query.canonical, "SELECT *\nFROM CUSTOMERS")

        query = SQLQuery(
            """
        /* Select all employees whose compensation is
        greater than that of Pataballa. */
        SELECT * FROM CUSTOMERS; # Select all:"""
        )
        self.assertEqual(query.canonical, "SELECT *\nFROM CUSTOMERS")

    def test_is_select(self):
        query = SQLQuery("  SELECT\n*\tFROM   USERS  \n\r")
        self.assertEqual(query.is_select(), True)

        query = SQLQuery("\nSELECT *\n    from\\n       users\n")
        self.assertEqual(query.is_select(), True)

        query = SQLQuery(
            """
        INSERT INTO TABLE2
        SELECT * FROM TABLE1
        WHERE CONDITION;
        """
        )
        self.assertEqual(query.is_select(), False)

        query = SQLQuery(
            """
        -- Comment
        SELECT * FROM TABLE1
        WHERE CONDITION;
        """
        )
        self.assertEqual(query.is_select(), True)

    def test_is_ordered(self):
        query = SQLQuery(
            """
        SELECT COLUMN1, COLUMN2, ...
        FROM TABLE_NAME
        ORDER BY column1, column2, ASC|DESC;
        """
        )
        self.assertEqual(query.is_ordered(), True)

        query = SQLQuery(
            """
        # ORDER BY
        SELECT COLUMN1, COLUMN2, ...
        FROM TABLE_NAME
        """
        )
        self.assertEqual(query.is_ordered(), False)

        query = SQLQuery("SELECT * FROM USERS")
        self.assertEqual(query.is_ordered(), False)

        query = SQLQuery('SELECT "ORDER BY" FROM USERS')
        self.assertEqual(query.is_ordered(), False)

        query = SQLQuery('SELECT "ORDER BY", (SELECT 1 ORDER BY TEST) FROM USERS')
        self.assertEqual(query.is_ordered(), False)
