import json
import os
import sqlite3


def parse_stroke_order(textfile_path, database_path):

    if not os.path.isfile(textfile_path):
        raise Exception("Couldn't find {}!".format(textfile_path))

    with open(textfile_path) as f:
        print("Opened stroke order text file.")

        data = json.load(f)

        try:
            conn = sqlite3.connect(database_path)

            c = conn.cursor()

            c.execute("DROP TABLE IF EXISTS stroke_orders")
            c.execute("VACUUM")

            c.execute('''CREATE TABLE stroke_orders (
                        id INTEGER PRIMARY KEY,
                        character TEXT NOT NULL,
                        json TEXT NOT NULL
                        );''')

            for character in data:
                c.execute("""INSERT INTO stroke_orders (character, json) 
                                VALUES (?, ?)""",
                                (character, str(data[character])))

            conn.commit()
            conn.close()

            print("Successfully parsed stroke orders.")

        except sqlite3.Error as error:
            print("Failed to insert data into sqlite table:", error)
        finally:
            if (conn):
                conn.close()


if __name__ == "__main__":
    stroke_order_raw_file_path = "../data/stroke_order.json"
    database_path = "../output/data.db"

    parse_stroke_order(stroke_order_raw_file_path, database_path)
