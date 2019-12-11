import re
import sqlite3
import os

def create_dictionary_database(textfile_path, database_path):    

    if not os.path.isfile(textfile_path):
        raise Exception("Couldn't find {}!".format(textfile_path))

    with open(textfile_path) as f:
        print("Opened cedict text file.")

        update_db = False
        if os.path.isfile(database_path):
            print("Updating database")
            update_db = True

        try:
            conn = sqlite3.connect(database_path)
            print("Successfully connected to database.")

            c = conn.cursor()

            if not update_db:
                c.execute('''CREATE TABLE word (
                            id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            simplified TEXT NOT NULL,
                            traditional TEXT NOT NULL,
                            pinyin TEXT NOT NULL,
                            priority INTEGER NOT NULL)''')

                # Definitions have to be mapped to a headword and a specific pinyin
                c.execute('''CREATE TABLE definition (
                            id INTEGER PRIMARY KEY,
                            word_id INTEGER NOT NULL, 
                            definition TEXT NOT NULL)''')

            for i_line, line in enumerate(f):
                # Check for comment line
                if line[0] != '#':
                    if (i_line % 100) == 0:
                        print(i_line)
                    line = line.rstrip()

                    headwords = re.split(r'\s',line)
                    pinyin = re.search(r'\[([^\]]*)\]' ,line).group(1)
                    definitions = re.split(r'\/',line)
                    
                    if not headwords: raise Exception("No headwords found in line {}".format(i_line+1))
                    if not pinyin: raise Exception("No Pinyin in line {}".format(i_line+1))
                    if not definitions: raise Exception("No definitions in line {}".format(i_line+1))

                    # Check if entry exists already
                    word_id = None
                    if update_db:
                        word_id = c.execute("""SELECT 
                                                    id 
                                                   FROM 
                                                    word
                                                   WHERE 
                                                    simplified = ?
                                                   AND
                                                    pinyin = ?""", 
                                                (headwords[1], pinyin)).fetchall()
                        if word_id:
                            word_id = word_id[0][0]
                    
                    if not word_id:
                        c.execute("""INSERT INTO word (simplified, traditional, pinyin, priority) 
                                     VALUES (?, ?, ?, ?)""",
                                    (headwords[1], headwords[0], pinyin, 0))

                        word_id = c.lastrowid 
                    
                    if update_db:
                        # Delete existing definitions
                        c.execute("""DELETE FROM 
                                     definition
                                    WHERE
                                     word_id = ?""",
                                    (word_id,))

                    # Save Definitions
                    for definition in definitions[1:-1]:
                        c.execute("""INSERT INTO definition (word_id, definition) 
                                     VALUES (?, ?)""",
                                     (word_id, definition))

            conn.commit()
            conn.close()

        except sqlite3.Error as error:
            print("Failed to insert data into sqlite table", error)
        finally:
            if (conn):
                conn.close()
                print("The SQLite connection is closed")

def create_search_index(database_path):

    # TODO: Pinyin with and without tones
    # TODO: Mix of Pinyin and Hanzi

    try:
        conn = sqlite3.connect(database_path)
        print("Successfully connected to database.")

        c = conn.cursor()
        
        c.execute("DROP TABLE IF EXISTS search_index")

        # Permutations linked to dictionary entry
        c.execute('''CREATE TABLE search_index
                    (id INTEGER PRIMARY KEY,
                    word_id INTEGER NOT NULL,
                    permutation TEXT NOT NULL)''')

        entries = c.execute("""SELECT 
                                id, simplified, pinyin
                             FROM
                                word""").fetchall()
        
        for i, entry in enumerate(entries):
            if (i%1000)==0:
                print(i)

            entry_id = entry[0]
            hanzi = entry[1]
            syllables = re.split(r'\s', entry[2])

            max_len_permutations = 3
            
            if len(syllables) <= max_len_permutations:
                if len(hanzi) != len(syllables):
                    permutations = create_permutations(['' for x in syllables], syllables)[1:]
                    permutations.append(hanzi)
                else:
                    permutations = create_permutations(list(hanzi), syllables)
            else:
                if len(hanzi) != len(syllables):
                    # tmp_permutations = create_permutations(['' for x in syllables[:max_len_permutations]], syllables[:max_len_permutations])[1:]

                    permutations = [hanzi, re.sub(' ', '', ''.join(syllables))]

                else:
                    tmp_permutations = create_permutations(hanzi[:max_len_permutations], syllables[:max_len_permutations])
                    permutations = []
                    for permutation in tmp_permutations:
                        permutations.append(permutation + re.sub('\d', '', ''.join(syllables[max_len_permutations:])))
                        permutations.append(permutation + hanzi[max_len_permutations:])


            for permutation in permutations:
                c.execute("""INSERT INTO search_index (word_id, permutation) 
                             VALUES (?, ?)""", 
                             (entry_id, permutation,))

        conn.commit()
        conn.close()

    except sqlite3.Error as error:
        print("Failed to insert data into sqlite table", error)
    finally:
        if (conn):
            conn.close()
            print("The SQLite connection is closed")


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
    textfile_path = 'cedict_ts.u8'
    database_path = 'cedict.db'
    
    # create_dictionary_database(textfile_path, database_path)
    # create_search_index(database_path)
