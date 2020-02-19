import os
import subprocess
from multiprocessing import Pool
import re
from clang import cindex
from clang.cindex import Index
import cpplint


PICKLE_FILE = "includes.pickle"

def get_all_git_files():
    patterns = ["*.cc", "*.h"]
    all_files = []
    CWD = "/home/chaturvedi/workspace/drake-distro/"
    for pattern in patterns:
        git_output = subprocess.check_output(
            ["git", "ls-files", pattern],
            cwd=CWD).decode("utf-8")
        all_files += [CWD + x for x in git_output.split('\n')]

    return list(filter(lambda x: x != '', all_files))

def process_file(file_name):
    includes = set()
    file_includes = cpplint.ProcessFile(file_name, 0)
    print("Processing File: {}".format(file_name))
    if file_includes:
        includes = includes.union(file_includes)
    return includes

def process_all_files():
    all_git_files = get_all_git_files()
    pool = Pool(8)
    includes_list = pool.map(process_file, all_git_files)
    all_includes = set()
    for include_file in includes_list:
        all_includes = all_includes.union(include_file)
    __import__("pickle").dump(all_includes, open("includes.pickle", "wb"))
    return all_includes

def parse_headers():
    header_list = []
    with open("headers_list.txt", "rb") as fil:
        for line in fil.readlines():
            match_obj = re.match("<(.*)>.*", line.strip())
            if match_obj:
                header_name = match_obj.group(1)
                match_obj_st = \
                        re.match(r"<.*>.*since C\+\+(\d+).*", line.strip())
                standard = match_obj_st.group(1) if match_obj_st else "03"
                header_list.append((header_name, standard))
    return header_list

def get_cpplint_headers():
    with open("cpplint_headers.txt", "rb") as fil:
        headers = [x.strip() for x in fil.readlines()]

    return headers

def main():
    if not os.path.exists(PICKLE_FILE):
        all_includes = process_all_files()
    else:
        all_includes = __import__("pickle").load(open(PICKLE_FILE, "rb"))
    header_std_list = parse_headers()
    headers = [x[0] for x in header_std_list]
    intersection_set = set(headers).intersection(all_includes)

    std_dict = dict()
    for std in ["03", "11", "14", "17", "20"]:
        std_dict[std] = []
    cpplint_headers = get_cpplint_headers()

    for element in intersection_set:
        ind = headers.index(element)
        header_name, std = header_std_list[ind]
        if header_name not in cpplint_headers:
            std_dict[std].append(header_name)
    for k in std_dict:
        std_dict[k] = sorted(std_dict[k])
    __import__('pprint').pprint(std_dict)


if __name__ == '__main__':
    main()
