import os
import sqlite3


def parse_opencc(opencc_file_path, database_path):
    if not os.path.isfile(opencc_file_path):
        raise Exception("Couldn't find {}!".format(opencc_file_path))

    with open(opencc_file_path) as f_opencc:
        print("Parsing opencc data.")

        try:
            conn = sqlite3.connect(database_path)

            c = conn.cursor()

            c.execute("DROP TABLE IF EXISTS traditional2simplified")
            c.execute("VACUUM")

            c.execute('''CREATE TABLE traditional2simplified (
                        id INTEGER PRIMARY KEY,
                        traditional TEXT NOT NULL,
                        simplified TEXT NOT NULL
                        );''')

            for i_line, line in enumerate(f_opencc):
                traditional, simplified = line.strip().split('\t')

                if len(simplified) > 1:
                    simplified = simplified.replace(' ', ',')

                c.execute("""INSERT INTO traditional2simplified (traditional, simplified)
                                VALUES (?, ?)""",
                          (traditional, simplified))

            conn.commit()
            conn.close()

            print("Succesfully parsed opencc data.")

        except sqlite3.Error as error:
            print("Failed to insert data into sqlite table:", error)
        finally:
            if (conn):
                conn.close()


if __name__ == "__main__":
    opencc_file_path = "../data/opencc.txt"
    database_path = "../output/data.db"

    parse_opencc(opencc_file_path, database_path)
