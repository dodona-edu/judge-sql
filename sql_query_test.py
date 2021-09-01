import unittest
from sql_query import SQLQuery

# @formatter:off
class TestSQLQuery(unittest.TestCase):
    def test_from_raw_input_1(self):
        queries = SQLQuery.from_raw_input(
            """-- First query:
        SELECT * from Users Where ";#" = 1;
        -- 2nd query:
        SELECT 1 # random comment"""
        )

        self.assertEqual(queries[0].formatted, 'SELECT * from Users Where ";#" = 1;')
        self.assertEqual(queries[0].has_ending_semicolon, True)
        self.assertEqual(queries[1].formatted, "SELECT 1")
        self.assertEqual(queries[1].has_ending_semicolon, False)

    def test_from_raw_input_2(self):
        queries = SQLQuery.from_raw_input("\n\r")
        self.assertEqual(len(queries), 0)

    def test_SQLQuery_1(self):
        query = SQLQuery('SELECT * from Users Where ";" = 1 ORdER BY Name ASC;')

        self.assertEqual(
            query.formatted,
            'SELECT * from Users Where ";" = 1 ORdER BY Name ASC;',
        )
        self.assertEqual(query.has_ending_semicolon, True)
        self.assertEqual(query.is_select, True)
        self.assertEqual(query.is_ordered, True)

    def test_SQLQuery_2(self):
        query = SQLQuery(
            '--SELECT\n   INSERT INTO table2 /**/  SELECT * FROM Users Where ";#ORDER BY" = 1;'
        )

        self.assertEqual(
            query.formatted,
            'INSERT INTO table2  SELECT * FROM Users Where ";#ORDER BY" = 1;',
        )
        self.assertEqual(query.has_ending_semicolon, True)
        self.assertEqual(query.is_select, False)
        self.assertEqual(query.is_ordered, False)

    def test_formatted(self):
        query = SQLQuery("\n  SELeCT\n*\tFROm   USERS  \n\r")
        self.assertEqual(query.formatted, "SELeCT\n*\tFROm   USERS")

        query = SQLQuery(
            """
        SELECT *
            from users



            /* test */
        """
        )
        self.assertEqual(
            query.formatted,
            """SELECT *
            from users""",
        )

        query = SQLQuery(
            """--Select all:
        SELECT * FROM Customers;"""
        )
        self.assertEqual(query.formatted, "SELECT * FROM Customers;")

        query = SQLQuery("""SELECT * FROM Customers; --Select all:""")
        self.assertEqual(query.formatted, "SELECT * FROM Customers;")

        query = SQLQuery(
            """# Select all:
        Select * FROM Customers;"""
        )
        self.assertEqual(query.formatted, "Select * FROM Customers;")

        query = SQLQuery("""SELECT * FROM Customers; # Select all:""")
        self.assertEqual(query.formatted, "SELECT * FROM Customers;")

        query = SQLQuery(
            """/* Select all employees whose compensation is
        greater than that of Pataballa. */
        SELECT * FROM Customers; # Select all:"""
        )
        self.assertEqual(query.formatted, "SELECT * FROM Customers;")

        query = SQLQuery(
            """/* Select all employees whose compensation is
        greater than that of Pataballa. */
        SELECT * FROM Customers; # Select all:"""
        )
        self.assertEqual(query.formatted, "SELECT * FROM Customers;")

    def test_is_select(self):
        query = SQLQuery("  SELeCT\n*\tFROm   USERS  \n\r")
        self.assertEqual(query.is_select, True)

        query = SQLQuery("\nSELECT *\n    from\\n       users\n")
        self.assertEqual(query.is_select, True)

        query = SQLQuery(
            """
        INSERT INTO table2
        SELECT * FROM table1
        WHERE condition;
        """
        )
        self.assertEqual(query.is_select, False)

        query = SQLQuery(
            """
        -- Comment
        SELECT * FROM table1
        WHERE condition;
        """
        )
        self.assertEqual(query.is_select, True)

    def test_is_ordered(self):
        query = SQLQuery(
            """SELECT column1, column2, ...
        FROM table_name
        ORDER BY column1, column2, ASC|DESC;
        """
        )
        self.assertEqual(query.is_ordered, True)

        query = SQLQuery(
            """# ORDER BY
        SELECT column1, column2, ...
        FROM table_name
        """
        )
        self.assertEqual(query.is_ordered, False)

        query = SQLQuery("select * from users")
        self.assertEqual(query.is_ordered, False)

        query = SQLQuery('select "ORDER BY" from users')
        self.assertEqual(query.is_ordered, False)

        query = SQLQuery('select "ORDER BY", (SELECT 1 ORDER BY test) from users')
        self.assertEqual(query.is_ordered, False)
# @formatter:on

if __name__ == "__main__":
    unittest.main()
