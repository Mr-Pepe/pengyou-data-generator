from cedict_parser import parse_dictionary
from cjdecomp_parser import parse_decompositions
from stroke_order_parser import parse_stroke_order

cedict_raw_file_path = "./data/cedict.txt"
cjdecomp_raw_file_path = "./data/cjdecomp.txt"
stroke_order_raw_file_path = "./data/stroke_order.json"
database_path = "./output/data.db"

parse_dictionary(cedict_raw_file_path, database_path, max_len_permutations=3)

parse_decompositions(cjdecomp_raw_file_path, database_path)

parse_stroke_order(stroke_order_raw_file_path, database_path)