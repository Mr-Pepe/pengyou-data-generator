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
                    raw_definitions = re.search(r'\/(.*)\/',line).group(1).replace("CL:", "measure word: ")

                    # Wrap Chinese words in § for linking, because that is not used otherwise
                    # That saves the pain of handling surrogate pairs during definition parsing in Kotlin
                    definitions = ""
                    mode = 0 # Mode: 0 = not entered Chinese string, 1 = entered Chinese string
                    for i_char in range(len(raw_definitions)):
                        
                        if mode == 0:
                            if ((raw_definitions[i_char] >= u'\u4e00' and raw_definitions[i_char] <= u'\u9fff') or 
                                (raw_definitions[i_char] >= u'\u3000' and raw_definitions[i_char] <= u'\u303f')):

                                # Backtrack to find the beginning of the expression
                                for i_char_back in range(len(definitions)-1, -1, -1):
                                    if definitions[i_char_back] == ' ':
                                        definitions = definitions[:i_char_back+1] + '§' + definitions[i_char_back+1:]
                                        break
                                    elif definitions[i_char_back] == ',':
                                        definitions = definitions[:i_char_back+1] + ' §' + definitions[i_char_back+1:]
                                        break

                                mode = 1
                        else:
                            if raw_definitions[i_char] == '[' or raw_definitions[i_char] == ' ' or raw_definitions[i_char] == ',':
                                mode = 0
                                definitions += "§"

                        definitions += raw_definitions[i_char]
                    
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
                        pinyin = entry['pinyin'].strip()

                        if ' ' in pinyin:
                            raise Exception("Pinyin from Unihan has more than one pinyin syllable")
                        else:
                            pinyin = pinyin_marks_to_numbers(pinyin)

                        c.execute("""INSERT INTO entries (simplified, traditional, pinyin, priority, word_length, definitions, hsk, pinyin_length) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                (character, character, pinyin, 0, 1, entry['definition'], 7, len(pinyin)))
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
                    origin_headwords = definitions.split('erhua variant of ')[1].split('§')[1].split('|')

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

def pinyin_marks_to_numbers(syllable):

    tone = 5
    output = []

    characters = ['a', 'e', 'i', 'o', 'u', 'ü', 
                  'A', 'E', 'I', 'O', 'U', 'Ü']

    marks = [('ā', 'á', 'ǎ', 'à', 'a'),
            ('ē', 'é', 'ě', 'è', 'e'),
            ('ī', 'í', 'ǐ', 'ì', 'i'),
            ('ō', 'ó', 'ǒ', 'ò', 'o'),
            ('ū', 'ú', 'ǔ', 'ù', 'u'),
            ('ǖ', 'ǘ', 'ǚ', 'ǜ', 'ü'),

            ('Ā', 'Á', 'Ǎ', 'À', 'A'),
            ('Ē', 'É', 'Ě', 'È', 'E'),
            ('Ī', 'Í', 'Ĭ', 'Ì', 'I'),
            ('Ō', 'Ó', 'Ǒ', 'Ò', 'O'),
            ('Ū', 'Ú', 'Ǔ', 'Ù', 'U'),
            ('Ǖ', 'Ǘ', 'Ǚ', 'Ǜ', 'Ü')]

    for character in syllable: 
        indices = [-1 for mark in marks]

        for i_mark, mark in enumerate(marks):
            if character in mark:
                indices[i_mark] = mark.index(character)

        if sum(indices) != -len(indices):
            for i_index, index in enumerate(indices):
                if index != -1:
                    output.append(characters[i_index])
                    tone = index+1
        else:
            output.append(character)

    output.append(str(tone))
    output = ''.join(output).strip()

    return output

if __name__ == "__main__":
    cedict_raw_file_path = "./data/cedict.txt"
    database_path = "./output/data.db"
    unihan_path = "./data/unihan.txt"
    
    parse_dictionary(cedict_raw_file_path, unihan_path, database_path)
