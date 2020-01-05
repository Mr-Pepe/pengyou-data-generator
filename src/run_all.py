from cedict_parser import parse_dictionary
from cjdecomp_parser import parse_decompositions
from stroke_order_parser import parse_stroke_order
from permutations import generate_permutations
from hsk_word_list_parser import parse_hsk

cedict_raw_file_path = "./data/cedict.txt"
cjdecomp_raw_file_path = "./data/cjdecomp.txt"
stroke_order_raw_file_path = "./data/stroke_order.json"
hsk_lists_base_path = "./data/HSK/HSK{}.txt"
database_path = "./output/data.db"

parse_dictionary(cedict_raw_file_path, database_path)

parse_hsk(hsk_lists_base_path, database_path)

generate_permutations(database_path, max_len_permutations=3)

parse_decompositions(cjdecomp_raw_file_path, database_path)

parse_stroke_order(stroke_order_raw_file_path, database_path)