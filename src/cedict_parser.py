import re
import sqlite3
import os

def parse_dictionary(cedict_path, unihan_path, database_path):    

    entries = []
    characters = set()

    if not os.path.isfile(cedict_path):
        raise Exception("Couldn't find {}!".format(cedict_path))

    if not os.path.isfile(unihan_path):
        raise Exception("Couldn't find {}!".format(unihan_path))

    unihan = dict()
    print("Parsing Unihan.")
    with open(unihan_path) as f_unihan:
        for i_line, line in enumerate(f_unihan):
            # Check for comment line
            if line != '\n' and line[0] != '#':
                u_code, id, content = line.split("\t")
                u_code = u_code[2:]

                if u_code not in unihan:
                    unihan[u_code] = {'pinyin': '', 'definition': ''}

                if id == 'kMandarin':
                    unihan[u_code]['pinyin'] = content
                if id == 'kDefinition':
                    unihan[u_code]['definition'] = content.strip().replace(', ', '/').replace('; ', '/')
    
    print("Found {} entries in Unihan.".format(len(unihan)))

    with open(cedict_path) as f_cedict:
        print("Parsing CEDICT.")

        try:
            conn = sqlite3.connect(database_path)

            c = conn.cursor()

            c.execute("DROP TABLE IF EXISTS entries")
            c.execute("VACUUM")

            c.execute('''CREATE TABLE entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        simplified TEXT NOT NULL,
                        traditional TEXT NOT NULL,
                        pinyin TEXT NOT NULL,
                        definitions TEXT NOT NULL,
                        priority FLOAT NOT NULL,
                        hsk INTEGER NOT NULL,
                        word_length INTEGER NOT NULL,
                        pinyin_length INTEGER NOT NULL)''')

            n_lines = sum([1 for line in f_cedict if line[0] != '#'])
            f_cedict.seek(0)

            for i_line, line in enumerate(f_cedict):
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

                    entries.append(headwords[0])
                    entries.append(headwords[1])

                    for character in headwords[0]:
                        characters.add(character)

                    for character in headwords[1]:
                        characters.add(character)

                    if len(definitions.split('/')) == 1 and "old variant of" in definitions:
                        continue
                        
                    if len(definitions.split('/')) == 1 and "archaic variant of" in definitions:
                        continue

                    c.execute("""INSERT INTO entries (simplified, traditional, pinyin, priority, word_length, definitions, hsk, pinyin_length) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                (headwords[1], headwords[0], pinyin, 0, len(headwords[0]), definitions, 7, len(pinyin)))

            print("")

            print("Checking that every character has a definition.")
            chars_not_found = []

            # Make sure that there is a definition for every character 
            # Add Unihan definition if necessary
            for character in characters:
                
                # Checking here is faster than doing a lookup in the database
                if character not in entries:
                    if str(hex(ord(character)))[-4:].upper() in unihan:
                        print("Adding {} from Unihan".format(character))
                        entry = unihan[str(hex(ord(character)))[-4:].upper()]
                        c.execute("""INSERT INTO entries (simplified, traditional, pinyin, priority, word_length, definitions, hsk, pinyin_length) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                (character, character, entry['pinyin'], 0, 1, entry['definition'], 7, len(entry['pinyin'])))
                    else:
                        chars_not_found.append(character)
            
            print("The following characters have no definition in CEDICT or Unihan: {}".format(", ".join(chars_not_found)))

            # Augment erhua version definitions
            entries = c.execute("SELECT * FROM entries WHERE definitions LIKE '%erhua variant of%'").fetchall()

            for entry in entries:
                definitions = entry[4]
                pinyin = entry[3]
                if len(definitions.split('/')) == 1:

                    # Get the entry this entry is derived from
                    origin_headwords = definitions.split('erhua variant of ')[1].split('[')[0].split('|')

                    if len(origin_headwords) == 1:
                        origin = c.execute("SELECT * FROM entries WHERE simplified = (?) AND traditional = (?)", (origin_headwords[0], origin_headwords[0])).fetchall()

                        if not origin:
                            print("Error 1")
                        elif len(origin) > 1:
                            found = 0
                            for tmpEntry in origin:
                                if tmpEntry[3] in pinyin:
                                    c.execute("UPDATE entries SET definitions = (?) WHERE id = (?) ", (tmpEntry[4] + '/' + definitions, entry[0]))
                                    found += 1
                            
                            if found != 1:
                                print("Error 2")
                        else:
                            c.execute("UPDATE entries SET definitions = (?) WHERE id = (?) ", (origin[0][4] + '/' + definitions, entry[0]))
                    
                    elif len(origin_headwords) == 2:
                        origin = c.execute("SELECT * FROM entries WHERE traditional = (?) AND simplified = (?)", (origin_headwords[0], origin_headwords[1])).fetchall()

                        if not origin:
                            print("Error 3")
                        elif len(origin) > 1:
                            found = 0
                            for tmpEntry in origin:
                                if tmpEntry[3] in pinyin:
                                    c.execute("UPDATE entries SET definitions = (?) WHERE id = (?) ", (tmpEntry[4] + '/' + definitions, entry[0]))
                                    found += 1
                            
                            if found != 1:
                                print("Error 4")
                        else:
                            c.execute("UPDATE entries SET definitions = (?) WHERE id = (?) ", (origin[0][4] + '/' + definitions, entry[0]))
                    else:
                        print("Error 5")

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
    unihan_path = "./data/unihan.txt"
    
    parse_dictionary(cedict_raw_file_path, unihan_path, database_path)
