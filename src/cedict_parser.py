import re
import sqlite3
import os

def parse_dictionary(textfile_path, database_path):    

    if not os.path.isfile(textfile_path):
        raise Exception("Couldn't find {}!".format(textfile_path))
    
    with open(textfile_path) as f:
        print("Parsing CEDICT.")

        try:
            conn = sqlite3.connect(database_path)

            c = conn.cursor()

            c.execute("DROP TABLE IF EXISTS entries")

            c.execute('''CREATE TABLE entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        simplified TEXT NOT NULL,
                        traditional TEXT NOT NULL,
                        pinyin TEXT NOT NULL,
                        definitions TEXT NOT NULL,
                        priority INTEGER NOT NULL,
                        hsk INTEGER NOT NULL,
                        word_length INTEGER NOT NULL)''')

            n_lines = sum([1 for line in f if line[0] != '#'])
            f.seek(0)

            for i_line, line in enumerate(f):
                # Check for comment line
                if line[0] != '#':
                    if ((i_line+1) % 1000) == 0:
                        print("Entry {}/{}".format(i_line+1, n_lines), end='\r')
                        
                    line = line.rstrip()

                    headwords = re.split(r'\s',line)
                    pinyin = re.search(r'\[([^\]]*)\]' ,line).group(1)
                    definitions = re.search(r'\/(.*)\/',line).group(1)
                    
                    if not headwords: raise Exception("No headwords found in line {}".format(i_line+1))
                    if not pinyin: raise Exception("No Pinyin in line {}".format(i_line+1))
                    if not definitions: raise Exception("No definitions in line {}".format(i_line+1))

                    c.execute("""INSERT INTO entries (simplified, traditional, pinyin, priority, word_length, definitions, hsk) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                (headwords[1], headwords[0], pinyin, 0, len(headwords[0]), definitions, 7))

            print("")

            conn.commit()
            conn.close()

            print("Successfully parsed CEDICT.")

        except sqlite3.Error as error:
            print("Failed to insert data into sqlite table:", error)
        finally:
            if (conn):
                conn.close()


if __name__ == "__main__":
    cedict_raw_file_path = "./data/cedict.txt"
    database_path = "./output/data.db"
    
    parse_dictionary(cedict_raw_file_path, database_path)
