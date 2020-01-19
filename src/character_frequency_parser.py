# The data comes from https://czielinski.github.io/hanzifreq/hanzifreq/output/frequencies.html
# I took the data from there because I don't want to download the Chinese wikipedia and run the analysis myself


import re
import os
import sqlite3
    
def parse_character_frequency(frequency_file_path, database_path):
    
    if not os.path.isfile(frequency_file_path):
        raise Exception("Couldn't find {}!".format(frequency_file_path))

    with open(frequency_file_path) as f_frequency:
        print("Parsing character frequency data.")
        
        try:
            conn = sqlite3.connect(database_path)

            c = conn.cursor()

            frequencies = dict()

            for i_line, line in enumerate(f_frequency):
                if i_line >= 56 and '<tr><td>' in line:
                    fields = [x for x in re.findall('>([^>]*)<',line) if x]

                    priority = int(fields[0])
                    character = fields[1]
                    frequencies[character] = priority

            entries = c.execute("SELECT * FROM entries").fetchall()

            for entry in entries:
                priority = 0
                simplified = entry[1]
                traditional = entry[2]

                if len(simplified) != len(traditional):
                    raise Exception("Length mismatch between traditional and simplified headword.")

                for i_char in range(len(simplified)):
                    if simplified[i_char] in frequencies:
                        priority += frequencies[simplified[i_char]]
                    elif traditional[i_char] in frequencies:
                        priority += frequencies[traditional[i_char]]
                    else:
                        priority += max(frequencies.values())
                
                
                priority = priority / len(simplified)

                c.execute("UPDATE entries SET priority = (?) WHERE id = (?)", (priority, entry[0]))
                
            conn.commit()
            conn.close()

            print("Successfully parsed character frequencies.")
        except sqlite3.Error as error:
            print("Failed to insert data into sqlite table:", error)
        finally:
            if (conn):
                conn.close()


if __name__ == "__main__":
    frequency_file_path = "./data/character_frequency.html"
    database_path = "./output/data.db"

    parse_character_frequency(frequency_file_path, database_path)