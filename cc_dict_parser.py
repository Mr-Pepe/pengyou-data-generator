import re
import sqlite3

data = dict()

id = 1

with open('cedict_ts.u8') as f:
    i_line = 0
    for line in f:
        i_line += 1
        if line[0] != '#':
            line = line.rstrip()

            headwords = re.split(r'\s',line)
            if headwords:
                data[id] = dict()
                data[id]['simplified'] = headwords[1]
                data[id]['traditional'] = headwords[0]
            else:
                raise Exception("No headwords found in line {}".format(i_line))

            pinyin = re.search(r'\[(.*)\]' ,line).group(1)
            if pinyin:
                data[id]['pinyin'] = pinyin
            else:
                raise Exception("No Pinyin in line {}".format(i_line))

            definition = re.split(r'\/',line)
            if definition:
                data[id]['definition'] = definition[1:-1]
            else:
                raise Exception("No definition in line {}".format(i_line))
            
            id += 1

print("Found {} entries".format(id-1))

try:
    
    conn = sqlite3.connect('cedict.db')
    print("Successfully connected to database.")

    c = conn.cursor()

    c.execute('''CREATE TABLE ENTRIES 
                 ([ID] INTEGER PRIMARY KEY, 
                 [Traditional] text,
                 [Simplified] text,
                 [Pinyin] text)''')

    c.execute('''CREATE TABLE DEFINITIONS
                 ([ID] INTEGER PRIMARY KEY,
                 [Entry_ID] integer, 
                 [Definition] text)''')

    i_definition = 1

    for id in data:
        entries_query = """INSERT INTO `ENTRIES`
                           ('ID', 'Traditional', 'Simplified', 'Pinyin')
                           VALUES (?, ?, ?, ?);"""
        
        entries_query_data = (id, data[id]['simplified'], data[id]['traditional'], data[id]['pinyin'])

        count = c.execute(entries_query, entries_query_data)

        for definition in data[id]['definition']:
            definition_query = """INSERT INTO `DEFINITIONS`
                                  ('ID', 'Entry_ID', 'Definition') 
                                  VALUES (?, ?, ?);"""
            
            definition_query_data = (i_definition, id, definition)
            
            count = c.execute(definition_query, definition_query_data)

            i_definition += 1


    conn.commit()
    c.close()

except sqlite3.Error as error:
    print("Failed to insert data into sqlite table", error)
finally:
    if (conn):
        conn.close()
        print("The SQLite connection is closed")
