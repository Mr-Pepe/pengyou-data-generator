import sqlite3
import os

def parse_hsk(base_path, database_path):

    for i_hsk in range(1, 7):
        path = base_path.format(i_hsk)
        if not os.path.isfile(path):
            raise Exception("Couldn't find {}!".format(path))

    try:
        conn = sqlite3.connect(database_path)

        c = conn.cursor()
        mismatches = []

        for i_hsk in range(1, 7):
            path = base_path.format(i_hsk)
            print("Analyzing word list for HSK {}".format(i_hsk))

            with open(path) as f:
                n_lines = sum([1 for line in f if line[0] != '#'])
                f.seek(0)

                for i_line, line in enumerate(f):
                    if ((i_line+1) % 10) == 0:
                        print("Entry {}/{}".format(i_line+1, n_lines), end='\r')

                    fields = line.split('\t')
                    simplified = fields[0]
                    traditional = fields[1]
                    pinyin = fields[2]
                    definitions = fields[4]

                    entries_match_simplified = c.execute("SELECT * FROM entries WHERE simplified = (?)", (simplified,)).fetchall()

                    if not entries_match_simplified:
                        # A few words from the HSK lists are not included in the CEDICT and are added to the database here
                        print("HSK: {} Couldn't find {} in CEDICT. It is being added.".format(i_hsk, simplified))
                        
                        modified_pinyin = ''

                        for p in pinyin:
                            modified_pinyin += p
                            if p in ['1', '2', '3', '4', '5']:
                                modified_pinyin += ' '
                        
                        modified_pinyin = modified_pinyin.replace('  ', ' ').strip()
                        
                        c.execute("""INSERT INTO entries (simplified, traditional, pinyin, priority, word_length, definitions, hsk, pinyin_length) 
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                (simplified, traditional, modified_pinyin, 0, len(simplified), definitions.replace('/', ' or ').replace('; ', '/').strip(), i_hsk, len(modified_pinyin)))
                    
                    else:
                        # Delete variant entries
                        if len(entries_match_simplified) > 1:
                            tmpEntries = []

                            for entry in entries_match_simplified:
                                if 'variant of' not in entry[4]:
                                    tmpEntries.append(entry)
                            
                            entries_match_simplified = tmpEntries

                        if len(entries_match_simplified) == 1:
                            # There is an exact match
                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entries_match_simplified[0][0]))

                        else:
                            # There are several matches for the simplified headword
                            
                            


                            # See if there is an exact match for both simplified and traditional headword
                            entries_match_both = c.execute("SELECT * FROM entries WHERE simplified = (?) AND traditional = (?)", (simplified, traditional)).fetchall()
                            
                            # Hack :(
                            if simplified == '台':
                                for entry in entries_match_simplified:
                                    if entry[2] == '臺' and entry[3] == 'tai2':
                                        c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                            elif len(entries_match_both) == 1:
                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entries_match_simplified[0][0]))

                            elif len(entries_match_both) == 0:
                                # The HSK list uses a traditional headword that is not in CEDICT
                                
                                # Manual hacks :(
                                if simplified == '联系':
                                    for entry in entries_match_simplified:
                                        if entry[2] == '聯繫':
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                elif simplified == '重复':
                                    for entry in entries_match_simplified:
                                        if entry[2] == '重複':
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                elif simplified == '台风':
                                    for entry in entries_match_simplified:
                                        if entry[2] == '颱風':
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                else: 
                                    print("Exception found -> search for this error message.")


                            elif len(entries_match_both) > 1:
                                # There are multiple matches for both simplified and traditional
                                # See if there is a pinyin match
                                n_matches_both = sum([1 for entry in entries_match_both if entry[3].replace(' ', '') == pinyin.replace(' ', '')])

                                if n_matches_both == 1:
                                    for entry in entries_match_both:
                                        if entry[3].replace(' ', '') == pinyin.replace(' ', ''):
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))

                                else:
                                    # Manual hacks :(
                                    if simplified == '要':
                                        for entry in entries_match_both:
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '吧':
                                        for entry in entries_match_both:
                                            if entry[3] == 'ba1' or entry[3] == 'ba5':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '还':
                                        for entry in entries_match_both:
                                            if entry[3] == 'hai2' or entry[3] == 'huan2':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '给':
                                        for entry in entries_match_both:
                                            if entry[3] == 'gei3':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '得':
                                        for entry in entries_match_both:
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '着':
                                        for entry in entries_match_both:
                                            if entry[3] == 'zhe5' or entry[3] == 'zhao2' or entry[3] == 'zhuo2':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '别':
                                        for entry in entries_match_both:
                                            if entry[3] == 'bie2':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '长':
                                        for entry in entries_match_both:
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '女':
                                        for entry in entries_match_both:
                                            if entry[3] == 'nu:3':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '白':
                                        for entry in entries_match_both:
                                            if entry[3] == 'bai2':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '累':
                                        for entry in entries_match_both:
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '啊':
                                        for entry in entries_match_both:
                                            if entry[3] == 'a5':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '把':
                                        for entry in entries_match_both:
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '为':
                                        for entry in entries_match_both:
                                            if entry[2] == '為':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '更':
                                        for entry in entries_match_both:
                                            if entry[3] == 'geng4':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '地':
                                        for entry in entries_match_both:
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '种':
                                        for entry in entries_match_both:
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '难':
                                        for entry in entries_match_both:
                                            if entry[3] == 'nan2':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '分':
                                        for entry in entries_match_both:
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '教':
                                        for entry in entries_match_both:
                                            if entry[3] == 'jiao1' or entry[3] == 'jiao4':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '差':
                                        for entry in entries_match_both:
                                            if entry[3] == 'cha4' or entry[3] == 'cha1':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '角':
                                        for entry in entries_match_both:
                                            if entry[3] == 'jiao3':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '当':
                                        for entry in entries_match_both:
                                            if entry[3] == 'dang1':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '行':
                                        for entry in entries_match_both:
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '与':
                                        for entry in entries_match_both:
                                            if entry[3] == 'yu3':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '弄':
                                        for entry in entries_match_both:
                                            if entry[3] == 'nong4':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '场':
                                        for entry in entries_match_both:
                                            if entry[3] == 'chang3':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '倒':
                                        for entry in entries_match_both:
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '重':
                                        for entry in entries_match_both:
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '转':
                                        for entry in entries_match_both:
                                            if entry[3] == 'zhuan3' or entry[3] == 'zhuan4':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '假':
                                        for entry in entries_match_both:
                                            if entry[3] == 'jia3' or entry[3] == 'jia4':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '空':
                                        for entry in entries_match_both:
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '赚':
                                        for entry in entries_match_both:
                                            if entry[3] == 'zhuan4':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '趟':
                                        for entry in entries_match_both:
                                            if entry[3] == 'tang4':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '省':
                                        for entry in entries_match_both:
                                            if entry[3] == 'sheng3':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '汗':
                                        for entry in entries_match_both:
                                            if entry[3] == 'han4':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '嗯':
                                        for entry in entries_match_both:
                                            if entry[3] == 'en5':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '正':
                                        for entry in entries_match_both:
                                            if entry[3] == 'zheng4':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '片':
                                        for entry in entries_match_both:
                                            if entry[3] == 'pian4':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '吓':
                                        for entry in entries_match_both:
                                            if entry[3] == 'xia4':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '数':
                                        for entry in entries_match_both:
                                            if entry[3] == 'shu4' or entry[3] == 'shu3':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '臭':
                                        for entry in entries_match_both:
                                            if entry[3] == 'chou4':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '朝':
                                        for entry in entries_match_both:
                                            if entry[3] == 'chao2':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '便':
                                        for entry in entries_match_both:
                                            if entry[3] == 'bian4':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '抢':
                                        for entry in entries_match_both:
                                            if entry[3] == 'qiang3':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '圈':
                                        for entry in entries_match_both:
                                            if entry[3] == 'quan1':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '背':
                                        for entry in entries_match_both:
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '吐':
                                        for entry in entries_match_both:
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '切':
                                        for entry in entries_match_both:
                                            if entry[3] == 'qie1':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '称':
                                        for entry in entries_match_both:
                                            if entry[3] == 'cheng1':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '晕':
                                        for entry in entries_match_both:
                                            if entry[3] == 'yun1':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '挡':
                                        for entry in entries_match_both:
                                            if entry[3] == 'dang3':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '划':
                                        for entry in entries_match_both:
                                            if entry[3] == 'hua4':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '唉':
                                        for entry in entries_match_both:
                                            if entry[3] == 'ai1':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '挣':
                                        for entry in entries_match_both:
                                            if entry[3] == 'zheng4':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '薄':
                                        for entry in entries_match_both:
                                            if entry[3] == 'bao2':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '涨':
                                        for entry in entries_match_both:
                                            if entry[3] == 'zhang3':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '哦':
                                        for entry in entries_match_both:
                                            if entry[3] == 'o5': 
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '啦':
                                        for entry in entries_match_both:
                                            if entry[3] == 'la5':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '喂':
                                        for entry in entries_match_both:
                                            if entry[3] == 'wei2':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '哇':
                                        for entry in entries_match_both:
                                            if entry[3] == 'wa1':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '恶心':
                                        for entry in entries_match_both:    
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '折':
                                        for entry in entries_match_both:
                                            if entry[3] == 'zhe2':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '卷':
                                        for entry in entries_match_both:
                                            if entry[3] == 'juan4':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '扎':
                                        for entry in entries_match_both:
                                            if entry[3] == 'zha1':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '晃':
                                        for entry in entries_match_both:
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '篇':
                                        for entry in entries_match_both:
                                            if entry[3] == 'pian1':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '翘':
                                        for entry in entries_match_both:
                                            if entry[3] == 'qiao4':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '幢':
                                        for entry in entries_match_both:
                                            if entry[3] == 'zhuang4':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '拽':
                                        for entry in entries_match_both:
                                            if entry[3] == 'zhuai1':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '咋':
                                        for entry in entries_match_both:
                                            if entry[3] == 'za3':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '铺':
                                        for entry in entries_match_both:
                                            if entry[3] == 'pu1':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '挨':
                                        for entry in entries_match_both:
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '哄':
                                        for entry in entries_match_both:
                                            if entry[3] == 'hong3':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '横':
                                        for entry in entries_match_both:
                                            if entry[3] == 'heng2':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '拧':
                                        for entry in entries_match_both:
                                            if entry[3] == 'ning2':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '淋':
                                        for entry in entries_match_both:
                                            if entry[3] == 'lin2':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '扒':
                                        for entry in entries_match_both:
                                            if entry[3] == 'ba1':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '削':
                                        for entry in entries_match_both:
                                            if entry[3] == 'xiao1':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '扛':
                                        for entry in entries_match_both:
                                            if entry[3] == 'kang2':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '劈':
                                        for entry in entries_match_both:
                                            if entry[3] == 'pi1':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '搂':
                                        for entry in entries_match_both:
                                            c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '攒':
                                        for entry in entries_match_both:
                                            if entry[3] == 'zan3':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '撇':
                                        for entry in entries_match_both:
                                            if entry[3] == 'pie3':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '盛':
                                        for entry in entries_match_both:
                                            if entry[3] == 'cheng2':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '搁':
                                        for entry in entries_match_both:
                                            if entry[3] == 'ge1':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '分量':
                                        for entry in entries_match_both:
                                            if entry[3] == 'fen4 liang5':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))
                                    elif simplified == '扁':
                                        for entry in entries_match_both:
                                            if entry[3] == 'bian3':
                                                c.execute("UPDATE entries SET hsk = (?) WHERE id = (?) ", (i_hsk, entry[0]))


                                    
                                    else:
                                        print("Found an exception that has to be treated. Search for this error message.")
                                    

                print("")
                        
        conn.commit()
        conn.close()

        print("Successfully parsed HSK word lists.")


    except sqlite3.Error as error:
        print("Failed to insert data into sqlite table:", error)
    finally:
        if (conn):
            conn.close()


if __name__ == "__main__":
    base_path = "./data/HSK/HSK{}.txt"
    database_path = "./output/data.db"

    parse_hsk(base_path, database_path)