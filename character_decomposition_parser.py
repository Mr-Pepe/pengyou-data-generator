import os
import sqlite3
from collections import Counter

def parse_decomposition(decomposition_file_path, database_path):

    if not os.path.isfile(decomposition_file_path):
        raise Exception("Couldn't find {}!".format(decomposition_file_path))


    with open(decomposition_file_path) as f_decomposition:

        try:
            conn = sqlite3.connect(database_path)
            print("Successfully connected to database.")

            c = conn.cursor()

            c.execute("DROP TABLE IF EXISTS decompositions")

            c.execute('''CREATE TABLE decompositions (
                        id INTEGER PRIMARY KEY,
                        character TEXT NOT NULL,
                        decomposition_type TEXT NOT NULL,
                        components TEXT NOT NULL
                        );''')

            for i_line, line in enumerate(f_decomposition):
                character, decomposition = line.strip().split(':')           

                decomposition_type, components = decomposition.split('(')
                components = components.replace(')', '')

                c.execute("""INSERT INTO decompositions (character, decomposition_type, components) 
                                VALUES (?, ?, ?)""",
                                (character, decomposition_type, components))

            conn.commit()
            conn.close()

        except sqlite3.Error as error:
            print("Failed to insert data into sqlite table:", error)
        finally:
            if (conn):
                conn.close()
                print("The SQLite connection is closed")
    



if __name__ == "__main__":
    decomposition_file_path = "cjdecomp.txt"
    database_path = 'cedict.db'

    parse_decomposition(decomposition_file_path, database_path)
