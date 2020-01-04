from cedict_parser import parse_dictionary
from cjdecomp_parser import parse_decompositions

cedict_raw_file_path = "./data/cedict.txt"
cjdecomp_raw_file_path = "./data/cjdecomp.txt"
database_path = "./output/data.db"

parse_dictionary(cedict_raw_file_path, database_path, max_len_permutations=3)

parse_decompositions(cjdecomp_raw_file_path, database_path)
