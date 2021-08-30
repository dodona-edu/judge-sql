# SQL judge for [Dodona](dodona.ugent.be)

## Judge features

* Comparison based on solution query
* SQLite database per exercise
* Automatic detection if order needs to be checked
* Support for read and write operations
* Automatic distinction between read and write operations

## Recommended exercise directory structure

> [More info about repository directory structure](https://docs.dodona.be/en/references/repository-directory-structure/#example-of-a-valid-repository-structure)

Add your solution (`solution.sql` file) and database(s) (`.sqlite`) to the `evaluation` folder. The `solution.sql` file can contain multiple queries. You can define a different name for the solution in the `config.json` file. If you add multiple databases, the queries will be executed on all databases. The names of the databases don't matter.

````
+-- README.md                            # Optional: Describes the repository
+-- 📂public                            # Optional: Contains files that belong to the course or series
|   +-- database_diagram.png             # Optional: An database diagram image to reuse throughout the course
+-- dirconfig.json                       # Shared config for all exercises in subdirs
+-- 📂sql-exercises                     # We could group exercises in a folder
|   +-- 📂first_select_query            # Folder name for the exercise
|   |   +-- config.json                  # configuration of the exercise
|   |   +-- 📂evaluation                # -- 🔽️ ADD YOUR DATABASE AND SOLUTION HERE 🔽 --
|   |   |   +-- 📂databases             #
|   |   |   |   +-- my_database.sqlite   # ▶ The database file
|   |   |   +-- solution.sql             # ▶ The SQL model solution file
|   |   +-- 📂solution                  # Optional: This will be visible in Dodona
|   |   |   +-- solution.sql             # Optional: the SQL model solution file
|   |   +-- 📂description               #
|   |       +-- description.nl.md        # The description in Dutch
|   |       +-- description.en.md        # Optional: The description in English
|   |       +-- 📂media                 # Optional folder
|   |       |   +-- some_image.png       # Optional: An image used in the description
|   |       +-- 📂boilerplate           # Optional folder
|   |           +-- boilerplate          # Optional: loaded automatically in submission text area
|   :
:
````

## Recommended `dirconfig.json`

> [More info about exercise directory structure](https://docs.dodona.be/en/references/exercise-directory-structure/)

````json
{
  "type": "exercise",
  "programming_language": "sql",
  "access": "private",
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

* **Optional setting in `config.json`**

| Evaluation setting  | Description                                                    | Possible values | Default          |
| ------------------- | -------------------------------------------------------------- | --------------- | ---------------- |
| `solution_sql`      | Relative path to solution SQL file                             | path            | `./solution.sql` |
| `database_dir`      | Relative path to database directory                            | path            | `./databases`    |
| `max_rows`          | Maximal number of rows shown                                   | int             | 100              |
| `semicolon_warning` | Show warning if there isn't a semicolon at the end of each query | `true`/`false`  | `true`           |

### Example of modified settings

````json
{
  "evaluation": {
    "solution_sql": "./mijn_oplossing.sql",
    "database_dir": ".",
    "max_rows": 100,
    "semicolon_warning": false
  }
}
````

## Testing

The following command can be used to run the doctests:

```bash
$ ./run-doctest.sh
...
3 items passed all tests:
   2 tests in sql_judge.detect_is_ordered
   3 tests in sql_judge.detect_is_select
   2 tests in sql_judge.query_cleanup
7 tests in 5 items.
7 passed and 0 failed.
Test passed.
```
