# SQL judge for [Dodona](https://dodona.ugent.be/)

## Judge features

* Comparison based on solution query
* SQLite database per exercise
* Automatic detection if order needs to be checked
* Support for read and (TODO) write operations
* Automatic distinction between read and write operations
* Option to execute same queries on multiple databases
* Support for multiple queries in one exercise
* Allow submitted query to return columns in different order than the solution
* Feedback in language of user (Dutch or English)
* Extensive [customization possible in `config.json`](#optional-evaluation-settings-in-configjson)
* Elaborate [feedback](#feedback)

### Feedback

* Syntax errors
* Comparison between row count and column count between solution and submission
* Data types
* Number of queries
* Only same type of query as solution is allowed
* Differences between submission and solution table are highlighted
* ...

## Recommended exercise directory structure

> [More info about repository directory structure](https://docs.dodona.be/en/references/repository-directory-structure/#example-of-a-valid-repository-structure)

Add your solution (`solution.sql` file) and database(s) (`.sqlite`) to the **`evaluation`** folder. The `solution.sql` file can contain multiple queries. You can define a different name for the solution in the `config.json` file. If you add multiple databases, the queries will be executed on all databases. The names of the databases don't matter. Absolute necessary files are marked with `▶` in the tree structure below.

```text
+-- README.md                            # Optional: Describes the repository
+-- 📂public                            # Optional: Contains files that belong to the course or series
|   +-- database_diagram.png             # Optional: An database diagram image to reuse throughout the course
+-- dirconfig.json                       # Shared config for all exercises in subdirs
+-- 📂sql-exercises                     # We could group exercises in a folder
|   +-- 📂first_select_query            # Folder name for the exercise
|   |   +-- config.json                  # ▶ Configuration of the exercise
|   |   +-- 📂evaluation                # -- 🔽️ ADD YOUR DATABASE AND SOLUTION HERE 🔽 --
|   |   |   +-- my_database.sqlite       # ▶ The database file
|   |   |   +-- solution.sql             # ▶ The SQL model solution file
|   |   +-- 📂solution                  # Optional: This will be visible in Dodona
|   |   |   +-- solution.sql             # Optional: The SQL model solution file
|   |   +-- 📂preparation               # Optional folder
|   |   |   +-- generator.py             # Optional: Script to generate database
|   |   +-- 📂description               #
|   |       +-- description.nl.md        # ▶ The description in Dutch
|   |       +-- description.en.md        # Optional: The description in English
|   |       +-- 📂media                 # Optional folder
|   |       |   +-- some_image.png       # Optional: An image used in the description
|   |       +-- 📂boilerplate           # Optional folder
|   |           +-- boilerplate          # Optional: loaded automatically in submission text area
|   :
:
```

## Recommended `dirconfig.json`

> [More info about exercise directory structure](https://docs.dodona.be/en/references/exercise-directory-structure/)

````json
{
  "type": "exercise",
  "programming_language": "sql",
  "access": "public",
  "evaluation": {
    "handler": "sql",
    "time_limit": 10,
    "memory_limit": 50000000
  },
  "labels": [
    "sqlite",
    "database"
  ],
  "author": "Firstname Lastname <firstname_lastname@ugent.be>",
  "contact": "firstname_lastname@ugent.be"
}
````

## Recommended `config.json` (example with default settings)

````json
{
  "description": {
    "names": {
      "nl": "Mijn eerste databank oefening",
      "en": "My first database exercise"
    }
  },
  "type": "exercise",
  "programming_language": "sql",
  "labels": [
    "sqlite",
    "database"
  ],
  "evaluation": {
    "handler": "sql"
  }
}
````

## Optional `evaluation` settings in `config.json`

If these settings are not defined, the default value is chosen.

| Evaluation setting             | Description                                                                                                       | Possible values     | Default          |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------------- | ------------------- | ---------------- |
| `solution_sql`                 | Relative path to solution SQL file.                                                                               | path                | `./solution.sql` |
| `database_files`               | List of database files in custom order. If not provided, the files are loaded alphabetically from `database_dir`. | list / not provided | not provided     |
| `database_dir`                 | Relative path to database directory.                                                                              | path                | `.`              |
| `max_rows`                     | Maximal number of rows shown.                                                                                     | int                 | 100              |
| `semicolon_warning`            | Show warning if there isn't a semicolon at the end of each query.                                                 | `true`/`false`      | `true`           |
| `strict_identical_order_by`    | If solution (doesn't) contain(s) `ORDER BY`, student queries also (don't) have to contain it.                     | `true`/`false`      | `true`           |
| `allow_different_column_order` | Allow submitted query to return columns in different order than the solution.                                     | `true`/`false`      | `true`           |
| `forbidden_pre_execution`      | Disallow the usage of some words in queries (check runs before query execution).                                  | list of regex       | `[".*sqlite_(temp_)?(master\|schema).*", "pragma"]` |
| `forbidden_post_execution`     | Disallow the usage of some words in queries (check runs after query execution and only if all other tests succeeded). | list of regex       | `[]`             |

### Example of modified settings

````json
{
  "evaluation": {
    "solution_sql": "./my_answers.sql",
    "database_dir": "./databases/",
    "max_rows": 80,
    "semicolon_warning": false,
    "strict_identical_order_by": false,
    "allow_different_column_order": false,

  }
}
````

or

````json
{
  "evaluation": {
    "solution_sql": "./mijn_oplossing.sql",
    "database_files": [
      "./databases/database2.sqlite",
      "./databases/database1.sqlite"
    ],
    "max_rows": 80,
    "semicolon_warning": false,
    "strict_identical_order_by": false,
    "allow_different_column_order": false,
    "forbidden_pre_execution": [
      "dummy",
      "like"
    ]
  }
}
````

## Generate database with Python script

SQLite databases can be made with a Python script. Place the script (e.g. `generator.py`) in the `preparation` folder. This example creates an empty database in the `evaluation` folder.

```python
# import the sqlite3 module from the Python Standard Library
import sqlite3

# create the database file and create a cursor object
connection = sqlite3.connect("../evaluation/empty.sqlite")
cursor = connection.cursor()

# define and execute an SQL command to create an empty database
sql_command_create_dummy_table = """CREATE TABLE dummy_table(dummy_field int);"""
sql_command_remove_dummy_tabel = """DROP TABLE dummy_table;"""
cursor.execute(sql_command_create_dummy_table)
cursor.execute(sql_command_remove_dummy_tabel)

# commit changes and close the connection to the database file
connection.commit()
connection.close()
```

## Recommended database tools for SQLite

* [DB Browser for SQLite](https://sqlitebrowser.org/dl/) (free and open source)  
* [DbVisualizer free version](https://www.dbvis.com/download/)

> **How to generate diagram with table relationships?**
> * Open **DbVisualizer**
> * `Tools` (in menu bar at the top) > `Connection Wizard...`
> * Enter connection alias: e.g. `my_database` > `Next >`
> * Select Database Driver > `SQLite` > `Next >`
> * Path to Database in `Database file name`: e.g. `C:\Users\YOUR_NAME\PycharmProjects\YOUR_PROJECT\YOUR_FOLDER\YOUR_EXERCISE\evaluation\my_database.sqlite` > `Finish`
> * Locate **Tables** in the Databases tab tree > Double click it > `Open Object`
> * **References** > Layout: `Hierarchical`
> * Fourth icon `Export graph to file` > Output format: `PNG` > `Next >`
> * Choose a folder > `Export` 

## Testing

The following command can be used to run the tests:

```bash
$ ./run-tests.sh
.........
----------------------------------------------------------------------
Ran 9 tests in 0.029s

OK
```
