import os
import sqlite3
from collections import Counter

def parse_decompositions(decomposition_file_path, database_path):

    if not os.path.isfile(decomposition_file_path):
        raise Exception("Couldn't find {}!".format(decomposition_file_path))

    with open(decomposition_file_path) as f_decomposition:
        print("Parsing character decompositions.")

        try:
            conn = sqlite3.connect(database_path)

            c = conn.cursor()

            c.execute("DROP TABLE IF EXISTS decompositions")
            c.execute("VACUUM")

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

            print("Succesfully parsed decomposition data.")

        except sqlite3.Error as error:
            print("Failed to insert data into sqlite table:", error)
        finally:
            if (conn):
                conn.close()
    

if __name__ == "__main__":
    cjdecomp_raw_file_path = "../data/cjdecomp.txt"
    database_path = "../output/data.db"

    parse_decompositions(cjdecomp_raw_file_path, database_path)
