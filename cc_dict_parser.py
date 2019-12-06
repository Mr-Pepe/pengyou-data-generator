import re

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