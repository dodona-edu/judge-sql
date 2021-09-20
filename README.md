# SQL judge for [Dodona](https://dodona.ugent.be/)

## Judge features

- Comparison based on solution query
- SQLite database per exercise
- Automatic detection if order needs to be checked
- Support for read and write operations
- Automatic distinction between read and write operations
- Option to execute same queries on multiple databases
- Support for multiple queries in one exercise
- Allow submitted query to return columns in different order than the solution
- Feedback in language of user (Dutch or English)
- Extensive [customization possible in `config.json`](#optional-evaluation-settings-in-configjson)
- Elaborate [feedback](#feedback)

### Feedback

- Syntax errors
- Comparison between row count and column count between solution and submission
- Unnecessary sorts (student query should be sorted when solution query is and vice versa)
- Correct records but wrong order
- Data types
- Number of queries
- Only same type of query as solution is allowed
- Differences between submission and solution table are highlighted
- ...

## Recommended exercise directory structure

> [More info about repository directory structure](https://docs.dodona.be/en/references/repository-directory-structure/#example-of-a-valid-repository-structure)

Add your solution (`solution.sql` file) and database(s) (`.sqlite`) to the **`evaluation`** folder. The `solution.sql`
file can contain multiple queries. You can define a different name for the solution in the `config.json` file. If you
add multiple databases, the queries will be executed on all databases. The names of the databases don't matter. Absolute
necessary files are marked with `▶` in the tree structure below.

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

```json
{
  "type": "exercise",
  "programming_language": "sql",
  "access": "public",
  "evaluation": {
    "handler": "sql",
    "time_limit": 10,
    "memory_limit": 50000000
  },
  "labels": ["sqlite", "database"],
  "author": "Firstname Lastname <firstname_lastname@ugent.be>",
  "contact": "firstname_lastname@ugent.be"
}
```

## Recommended `config.json` (example with default settings)

```json
{
  "description": {
    "names": {
      "nl": "Mijn eerste databank oefening",
      "en": "My first database exercise"
    }
  },
  "type": "exercise",
  "programming_language": "sql",
  "labels": ["sqlite", "database"],
  "evaluation": {
    "handler": "sql"
  }
}
```

## Optional `evaluation` settings in `config.json`

If these settings are not defined, the default value is chosen.

| Evaluation setting                     | Description                                                                                                                 | Possible values     | Default                                             |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ------------------- | --------------------------------------------------- |
| `solution_sql`                         | Relative path to solution SQL file.                                                                                         | path                | `./solution.sql`                                    |
| `database_files`                       | List of database files in custom order. If not provided, the files are loaded alphabetically from `database_dir`.           | list / not provided | not provided                                        |
| `database_dir`                         | Relative path to database directory.                                                                                        | path                | `.`                                                 |
| `max_rows`                             | Maximal number of rows shown.                                                                                               | int                 | 100                                                 |
| `semicolon_warning`                    | Show warning if there isn't a semicolon at the end of each query.                                                           | `true`/`false`      | `true`                                              |
| `strict_identical_order_by`            | If solution (doesn't) contain(s) `ORDER BY`, student queries also (don't) have to contain it.                               | `true`/`false`      | `true`                                              |
| `allow_different_column_order`         | Allow submitted query to return columns in different order than the solution.                                               | `true`/`false`      | `true`                                              |
| `pargma_startup_queries`               | Run the provided PRAGMA queries on all test databases before starting the tests.                                            | string              | `""`                                                |
| `pre_execution_forbidden_symbolregex`  | Disallow the usage of some word groups in queries (check runs before query execution).                                      | list of regex       | `[".*sqlite_(temp_)?(master\|schema).*", "pragma"]` |
| `pre_execution_mandatory_symbolregex`  | Require the usage of some word groups in queries (check runs before query execution).                                       | list of regex       | `[]`                                                |
| `pre_execution_fullregex`              | Require the query to match the provided regex (check runs before query execution).                                          | list of regex       | `[]`                                                |
| `post_execution_forbidden_symbolregex` | Disallow the usage of some word groups in queries (check runs after query execution and only if all other tests succeeded). | list of regex       | `[]`                                                |
| `post_execution_mandatory_symbolregex` | Require the usage of some word groups in queries (check runs after query execution and only if all other tests succeeded).  | list of regex       | `[]`                                                |
| `post_execution_fullregex`             | Require the query to match the provided regex (check runs after query execution and only if all other tests succeeded).     | list of regex       | `[]`                                                |

### Regex match settings

The `pre_execution_forbidden_symbolregex`, `pre_execution_mandatory_symbolregex`, `pre_execution_fullregex`, `post_execution_forbidden_symbolregex`, `post_execution_mandatory_symbolregex` and `post_execution_fullregex` regex lists can be used to set extra checks for the submission query.
The `..._symbolregex` lists are used to check each individual "symbol" (these symbols are detected by sqlparse library, examples are `not like`, `users` and `'String value'`).
All regular expressions are used in a case-insensitive way, and a full match is performed (no `^` and `$` required).

For the example query "SELECT \* FROM users WHERE name = 'test';":
| Field | Value | No error✅ / Error❌ | Reason |
| --------------------------- | ----- | -------------- | ---- |
| `..._forbidden_symbolregex` | ["users"] | ❌ | symbol found |
| `..._mandatory_symbolregex` | ["customers"] | ❌ | symbol not found |
| `..._fullregex` | ["select"] | ❌ | not a full match |
| `..._forbidden_symbolregex` | ["test"] | ✅ | not a full match |
| `..._mandatory_symbolregex` | [".test."] | ✅ | symbol found (`'test'`) |
| `..._fullregex` | ["select .*"] | ✅ | full match |

### Example of modified settings

```json
{
  "evaluation": {
    "solution_sql": "./my_answers.sql",
    "database_dir": "./databases/",
    "max_rows": 80,
    "semicolon_warning": false,
    "strict_identical_order_by": false,
    "allow_different_column_order": false
  }
}
```

or

```json
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
    "post_execution_forbidden_symbolregex": ["dummy", ".*like.*"]
  }
}
```

## Generator scripts

SQLite databases can be made with a Python 3.9 script. Place the script (e.g. `generator.py`) in the `preparation`
folder.

### Generate empty database with Python script

This example creates an empty database in the `evaluation` folder.

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

### Generate database based on changes from previous exercises from scratch

Place the `previous_solution.sql` in the `preparation` folder. Use this script if you want to start with an empty
database and update it with the results previous exercises (only applicable for write queries).

<details>
  <summary>Click <b>here</b> to show to code.</summary>

```python
import os
import sqlite3
from sqlite3 import OperationalError

import pandas as pd


def execute_sql_from_file(filename: str):
    with open(filename, 'r') as file:
        sql_file = file.read()

    sql_commands = sql_file.split(';')

    for command in sql_commands:
        try:
            cursor.execute(command)
        except OperationalError as msg:
            print("Command skipped: ", msg)


db_filename = "../evaluation/your_database.sqlite"

if os.path.exists(db_filename):
    os.remove(db_filename)

connection = sqlite3.connect(db_filename)
cursor = connection.cursor()

execute_sql_from_file("previous_solution.sql")

# Print contents and properties of YOUR_TABLE_NAME
table_name = "YOUR_TABLE_NAME"
print(pd.read_sql(f"SELECT * FROM {table_name};", connection))
print(pd.read_sql(f"PRAGMA TABLE_INFO({table_name});", connection))

connection.commit()
connection.close()
```

</details>

### Generate updated database based with changes from previous exercises

Place the `previous_solution.sql` in the `preparation` folder. Use this script if you want to update an existing
database (only applicable for write queries).

<details>
  <summary>Click <b>here</b> to show to code.</summary>

```python
import os
import sqlite3
from sqlite3 import OperationalError

import pandas as pd


def execute_sql_from_file(filename: str):
    with open(filename, 'r') as file:
        sql_file = file.read()

    sql_commands = sql_file.split(';')

    for command in sql_commands:
        try:
            cursor.execute(command)
        except OperationalError as msg:
            print("Command skipped: ", msg)


original_db = "./my_origi_db.sqlite"
modified_db = "../evaluation/my_new_db.sqlite"

if os.path.exists(modified_db):
    os.remove(modified_db)

# Copy original database
con = sqlite3.connect(original_db)
bck = sqlite3.connect(modified_db)
con.backup(bck)
bck.close()
con.close()

connection = sqlite3.connect(modified_db)
cursor = connection.cursor()

execute_sql_from_file("previous_solution.sql")

# Print contents and properties of YOUR_TABLE_NAME
table_name = "YOUR_TABLE_NAME"
print(pd.read_sql(f"SELECT * FROM {table_name};", connection))
print(pd.read_sql(f"PRAGMA TABLE_INFO({table_name});", connection))

connection.commit()
connection.close()
```

</details>

## Recommended database tools for SQLite

- [DB Browser for SQLite](https://sqlitebrowser.org/dl/) (free and open source)
- [DbVisualizer free version](https://www.dbvis.com/download/)
- PyCharm Professional ([free for students and teachers](https://www.jetbrains.com/community/education/#students))

## How to generate a database diagram with table relationships?

- Database diagram with **DbVisualizer**

> - `Tools` (in menu bar at the top) > `Connection Wizard...`
> - Enter connection alias: e.g. `my_database` > `Next >`
> - Select Database Driver > `SQLite` > `Next >`
> - Path to Database in `Database file name`: e.g. `C:\Users\YOUR_NAME\PycharmProjects\YOUR_PROJECT\YOUR_FOLDER\YOUR_EXERCISE\evaluation\my_database.sqlite` > `Finish`
> - Locate **Tables** in the Databases tab tree > Double click it > `Open Object`
> - **References** > Layout: `Hierarchical`
> - Fourth icon `Export graph to file` > Output format: `PNG` > `Next >`
> - Choose a folder > `Export`
>
> _[More info](http://confluence.dbvis.com/display/UG100/Viewing+Table+Relationships)_

- Database diagram with **PyCharm Professional**

> _[More info](https://www.jetbrains.com/help/pycharm/creating-diagrams.html)_

### Add database schema overview to each exercise

1. Make sure there is a database icon (e.g. [database information icon](https://thenounproject.com/term/database/1211369/)) and
   an [image of database schema](#recommended-database-tools-for-sqlite) in the [`public` folder](https://docs.dodona.be/en/references/repository-directory-structure/) of your repository.
2. Click your repository on https://dodona.ugent.be/en/repositories/.
3. Scroll to the bottom to **Public files**.
4. Copy the links (e.g. https://dodona.ugent.be/nl/repositories/NUMBER/public/YOUR_IMAGE.png)
5. Fill in a template of your choice below and put it in the description of each exercise.

#### Icon which shows database diagram on click

- Markdown (recommended)

```markdown
![Database schema](LINK_TO_DATABASE_ICON){:data-large="LINK_TO_DATABASE_SCHEMA_OVERVIEW"}{:style="float: right"}
```

- HTML

```html
<img
  alt="Database schema"
  src="LINK_TO_DATABASE_ICON"
  data-large="LINK_TO_DATABASE_SCHEMA_OVERVIEW"
  style="float: right"
/>
```

#### Text link which shows database diagram on click

- Markdown (recommended)

```markdown
[Show database schema](LINK_TO_DATABASE_SCHEMA_OVERVIEW){: .dodona-lightbox}{: data-caption="Show database schema"}
```

- HTML

```html
<a
  href="LINK_TO_DATABASE_SCHEMA_OVERVIEW"
  class="dodona-lightbox"
  data-caption="Show database schema"
  >Show database schema</a
>
```

## Testing

The following command can be used to run the tests:

```bash
$ ./run-tests.sh
.............
----------------------------------------------------------------------
Ran 13 tests in 0.069s

OK
```

## Contributors

- **T. Ramlot**
- B. Willems

_Development funded by the [Faculty of Engineering and Architecture](https://www.ugent.be/ea/en)
of [Ghent University](https://www.ugent.be/en)_
