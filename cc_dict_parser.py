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
                c.execute('''CREATE TABLE headword (
                            id INTEGER PRIMARY KEY AUTOINCREMENT, 
                            simplified TEXT NOT NULL,
                            traditional TEXT NOT NULL,
                            priority INTEGER NOT NULL)''')

                c.execute('''CREATE TABLE pinyin (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            pinyin TEXT NOT NULL)''')
                
                # Pinyin with tones gets mapped to headwords in many-to-many relationship
                c.execute('''CREATE TABLE headword_pinyin (
                            id INTEGER PRIMARY KEY,
                            headword_id INTEGER NOT NULL,
                            pinyin_id TEXT NOT NULL)''')

                # Definitions have to be mapped to a headword and a specific pinyin
                c.execute('''CREATE TABLE definition (
                            id INTEGER PRIMARY KEY,
                            headword_id INTEGER NOT NULL, 
                            pinyin_id INTEGER NOT NULL,
                            definition TEXT NOT NULL)''')

            old_simplified_headword = ''

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

                    # Check if headword exists to have every headword only ones in the database
                    headword_id = None
                    if headwords[1] == old_simplified_headword or update_db:
                        headword_id = c.execute("""SELECT 
                                                    id 
                                                   FROM 
                                                    headword
                                                   WHERE 
                                                    simplified=?""", 
                                                (headwords[1],)).fetchall()
                        if headword_id:
                            headword_id = headword_id[0][0]
                    
                    if not headword_id:
                        c.execute("""INSERT INTO headword ('simplified', 'traditional', 'priority') 
                                        VALUES (?,?, ?)""",
                                    (headwords[1], headwords[0], 0))

                        headword_id = c.lastrowid

                    # Check if pinyin exists
                    pinyin_id = c.execute("""SELECT 
                                              id 
                                             FROM 
                                              pinyin 
                                             WHERE 
                                              pinyin=?""", 
                                             (pinyin,)).fetchall()


                    if pinyin_id:
                        pinyin_existed = True
                        pinyin_id = pinyin_id[0][0]
                    else:
                        pinyin_existed = False
                        c.execute("""INSERT INTO pinyin ('pinyin') 
                                     VALUES (?)""", 
                                     (pinyin,))

                        pinyin_id = c.lastrowid

                    # Connect Pinyin and headword
                    headword_pinyin_existed = False
                    if update_db and pinyin_existed: 
                        if c.execute("""SELECT 
                                        id
                                    FROM 
                                        headword_pinyin
                                    WHERE
                                        headword_id = ?
                                    AND
                                        pinyin_id = ?""",
                                    (headword_id, pinyin_id)):

                            headword_pinyin_existed = True 
                        
                    if not headword_pinyin_existed:    
                        c.execute("""INSERT INTO headword_pinyin ('headword_id', 'pinyin_id') 
                                    VALUES (?,?)""", 
                                    (headword_id, pinyin_id))
                    
                    if update_db:
                        # Delete existing definitions
                        c.execute("""DELETE FROM 
                                    definition
                                    WHERE
                                    headword_id = ? 
                                    AND
                                    pinyin_id = ?""",
                                    (headword_id, pinyin_id))

                    # Save Definitions
                    for definition in definitions[1:-1]:
                        c.execute("""INSERT INTO definition ('headword_id', 'pinyin_id', 'definition') 
                                     VALUES (?,?,?)""",
                                     (headword_id, pinyin_id, definition))

                    old_simplified_headword = headwords[1]

            conn.commit()
            conn.close()

        except sqlite3.Error as error:
            print("Failed to insert data into sqlite table", error)
        finally:
            if (conn):
                conn.close()
                print("The SQLite connection is closed")

def create_search_index(database_path):

    try:
        conn = sqlite3.connect(database_path)
        print("Successfully connected to database.")

        c = conn.cursor()

        # # Permutations of Pinyin with and without tones linked to pinyin with tones
        # c.execute('''CREATE TABLE PERMUTATIONS
        #             ([ID] INTEGER PRIMARY KEY,
        #             [Permutation] text)''')

        # # Mapping between Pinyin with tones and permutations
        # c.execute('''CREATE TABLE PINYIN_PERMUTATIONS
        #             ([ID] INTEGER PRIMARY KEY,
        #             [Pinyin_ID] integer,
        #             [Permutation_ID] integer)''')

        all_pinyin_entries = c.execute('SELECT * FROM PINYIN').fetchall()

        for entry in all_pinyin_entries:
            pinyin_id = entry[0]
            pinyin = entry[1]
            
            # Get headwords that have this pinyin
            headwords = c.execute('SELECT Headword_ID FROM HEADW')

            # Create all permutations of Pinyin with and without tones for the first for characters
            # to be able to combine search with and without tones
            syllables = re.split(r'\s', pinyin)

            if len(syllables) <= 4:
                permutations = create_permutations(syllables)
            else:
                tmp_permutations = create_permutations(syllables[:4])
                permutations = []
                for permutation in tmp_permutations:
                    permutations.append(permutation+re.sub('\d', '', ''.join(syllables[4:])))

            for permutation in permutations:
                c.execute("INSERT INTO PERMUTATIONS ('Permutation') VALUES (?)", 
                    (permutation,))
                permutation_id = c.lastrowid

                c.execute("INSERT INTO PINYIN_PERMUTATIONS ('Pinyin_ID', 'Permutation_ID') VALUES (?,?)", 
                    (pinyin_id, permutation_id))

    except sqlite3.Error as error:
        print("Failed to insert data into sqlite table", error)
    finally:
        if (conn):
            conn.close()
            print("The SQLite connection is closed")


def create_permutations(syllables):
    if len(syllables) == 1:
        if bool(re.search(r'\d', syllables[0])):
            return [syllables[0], re.sub('\d', '', syllables[0])]
        else: 
            return syllables
    else:
        split = int(len(syllables)/2)
        first_half = create_permutations(syllables[:split])
        second_half = create_permutations(syllables[split:])

        output = []

        for first_option in first_half:
            for second_option in second_half:
                output.append(first_option + second_option)

        return output

if __name__ == "__main__":
    textfile_path = 'cedict_ts.u8'
    database_path = 'cedict.db'
    
    create_dictionary_database(textfile_path, database_path)
    # create_search_index(database_path)
