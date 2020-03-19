import os
import sqlite3


def parse_opencc(opencc_tradsimpl_characters_file_path, opencc_tradsimpl_phrases_file_path, database_path):
    if not os.path.isfile(opencc_tradsimpl_characters_file_path):
        raise Exception("Couldn't find {}!".format(opencc_tradsimpl_characters_file_path))

    if not os.path.isfile(opencc_tradsimpl_phrases_file_path):
        raise Exception("Couldn't find {}!".format(opencc_tradsimpl_phrases_file_path))

    with open(opencc_tradsimpl_characters_file_path) as f_opencc_characters:
        with open(opencc_tradsimpl_phrases_file_path) as f_opencc_phrases:
            print("Parsing opencc data.")

            try:
                conn = sqlite3.connect(database_path)

                c = conn.cursor()

                c.execute("DROP TABLE IF EXISTS trad_to_simpl_characters")
                c.execute("DROP TABLE IF EXISTS trad_to_simpl_phrases")
                c.execute("VACUUM")

                c.execute('''CREATE TABLE trad_to_simpl_characters (
                            id INTEGER PRIMARY KEY,
                            traditional TEXT NOT NULL,
                            simplified TEXT NOT NULL
                            );''')

                c.execute('''CREATE TABLE trad_to_simpl_phrases (
                            id INTEGER PRIMARY KEY,
                            traditional TEXT NOT NULL,
                            simplified TEXT NOT NULL
                            );''')

                for i_line, line in enumerate(f_opencc_characters):
                    traditional, simplified = line.strip().split('\t')

                    if len(simplified) > 1:
                        simplified = simplified.replace(' ', ',')

                    c.execute("""INSERT INTO trad_to_simpl_characters (traditional, simplified)
                                    VALUES (?, ?)""",
                              (traditional, simplified))

                for i_line, line in enumerate(f_opencc_phrases):
                    traditional, simplified = line.strip().split('\t')

                    c.execute("""INSERT INTO trad_to_simpl_phrases (traditional, simplified)
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
    opencc_tradsimpl_characters_file_path = "../data/opencc_tradsimpl_characters.txt"
    opencc_tradsimpl_phrases_file_path = "../data/opencc_tradsimpl_phrases.txt"
    database_path = "../output/data.db"

    parse_opencc(opencc_tradsimpl_characters_file_path, opencc_tradsimpl_phrases_file_path, database_path)
