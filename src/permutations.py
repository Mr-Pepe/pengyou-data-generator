import sqlite3
import re


def generate_permutations(database_path, max_len_permutations):

    try:
        conn = sqlite3.connect(database_path)

        c = conn.cursor()

        c.execute("DROP INDEX IF EXISTS search_index")
        c.execute("DROP TABLE IF EXISTS permutations")
        c.execute("VACUUM")
        
        # Permutations of Hanzi and Pinyin with and without tones for searching
        c.execute('''CREATE TABLE permutations (
                    id INTEGER PRIMARY KEY,
                    entry_id INTEGER NOT NULL, 
                    permutation TEXT NOT NULL)''')

        entries = c.execute("SELECT * FROM entries").fetchall()

        print("Generating permutations.")

        for entry in entries:
            
            entry_id = entry[0]
            hanzi = entry[1]
            syllables = re.split(r'\s', entry[3].lower())

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
                    permutations.append(permutation + re.sub(r'\d', '', ''.join(syllables[max_len_permutations:])))
                    permutations.append(permutation + hanzi[max_len_permutations:])
                
                if hanzi not in permutations:
                    permutations.append(hanzi)


            for permutation in permutations:
                c.execute("""INSERT INTO permutations (entry_id, permutation) 
                            VALUES (?, ?)""", 
                            (entry_id, permutation))


        print("Creating search index for permutations.")
        c.execute("CREATE INDEX search_index ON permutations (permutation)")

        conn.commit()
        conn.close()

        print("Successfully generated permutations.")

    except sqlite3.Error as error:
        print("Failed to insert data into sqlite table:", error)
    finally:
        if (conn):
            conn.close()


def create_permutations(hanzi, syllables):
    if len(syllables) == 1:
        syllable = syllables[0]

        output = [hanzi[0], syllable]

        if bool(re.search(r'\d', syllable)):
            syllable_without_digits = re.sub(r'\d', '', syllable)
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
    database_path = "./output/data.db"

    generate_permutations(database_path, 3)