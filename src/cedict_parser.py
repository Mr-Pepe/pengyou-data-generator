import re
import sqlite3
import os

def parse_dictionary(textfile_path, database_path, max_len_permutations = 3):    

    if not os.path.isfile(textfile_path):
        raise Exception("Couldn't find {}!".format(textfile_path))
    
    with open(textfile_path) as f:
        print("Opened cedict text file.")

        try:
            conn = sqlite3.connect(database_path)
            print("Successfully connected to database.")

            c = conn.cursor()

            c.execute("DROP TABLE IF EXISTS entries")
            c.execute("DROP TABLE IF EXISTS permutations")

            c.execute('''CREATE TABLE entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        simplified TEXT NOT NULL,
                        traditional TEXT NOT NULL,
                        pinyin TEXT NOT NULL,
                        definitions TEXT NOT NULL,
                        priority INTEGER NOT NULL,
                        word_length INTEGER NOT NULL)''')
            
            # Permutations of Hanzi and Pinyin with and without tones for searching
            c.execute('''CREATE TABLE permutations (
                        id INTEGER PRIMARY KEY,
                        entry_id INTEGER NOT NULL, 
                        permutation TEXT NOT NULL)''')

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

                    # Check if entry exists already
                    c.execute("""INSERT INTO entries (simplified, traditional, pinyin, priority, word_length, definitions) 
                                    VALUES (?, ?, ?, ?, ?, ?)""",
                                (headwords[1], headwords[0], pinyin, 0, len(headwords[0]), definitions))

                    entry_id = c.lastrowid

                    # Generate permutations
                    syllables = re.split(r'\s', pinyin)
                    hanzi = headwords[1]

                    if len(syllables) <= max_len_permutations:
                        if len(hanzi) != len(syllables):
                            permutations = create_permutations(['' for x in syllables], syllables)[1:]
                            permutations.append(hanzi)
                        else:
                            permutations = create_permutations(list(hanzi), syllables)
                    else:
                        if len(hanzi) != len(syllables):
                            tmp_permutations = create_permutations(['' for x in syllables[:max_len_permutations]], syllables[:max_len_permutations])[1:]
                        else:
                            tmp_permutations = create_permutations(hanzi[:max_len_permutations], syllables[:max_len_permutations])

                        permutations = []
                        for permutation in tmp_permutations:
                            permutations.append(permutation + re.sub('\d', '', ''.join(syllables[max_len_permutations:])))
                            permutations.append(permutation + hanzi[max_len_permutations:])
                        
                        if hanzi not in permutations:
                            permutations.append(hanzi)


                    for permutation in permutations:
                        c.execute("""INSERT INTO permutations (entry_id, permutation) 
                                    VALUES (?, ?)""", 
                                    (entry_id, permutation))

            print("")

            print("Creating search index for permutations")
            c.execute("CREATE INDEX search_index ON permutations (permutation)")

            conn.commit()
            conn.close()

            print("Successfully parsed cedict.")

        except sqlite3.Error as error:
            print("Failed to insert data into sqlite table:", error)
        finally:
            if (conn):
                conn.close()
                print("The SQLite connection is closed.")


def create_permutations(hanzi, syllables):
    if len(syllables) == 1:
        syllable = syllables[0]

        output = [hanzi[0], syllable]

        if bool(re.search(r'\d', syllable)):
            syllable_without_digits = re.sub('\d', '', syllable)
            output.append(syllable_without_digits)

        if syllable == 'r5':
            output.append('er5')
            output.append('er')
        
        
        return list(set(output))
    else:
        split = int(len(syllables)/2)
        first_half = create_permutations(hanzi[:split], syllables[:split])
        second_half = create_permutations(hanzi[split:], syllables[split:])

        output = []

        for first_option in first_half:
            for second_option in second_half:
                output.append(first_option + second_option)

        return output


if __name__ == "__main__":
    cedict_raw_file_path = "./data/cedict.txt"
    database_path = "./output/data.db"
    
    parse_dictionary(cedict_raw_file_path, database_path)
