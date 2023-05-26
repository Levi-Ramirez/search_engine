

import json

def calculate_TF_IDF():
    print('sup')


def read_large_line(file):
    chunk_size = 4096  # python line buffer size
    line = ''

    while True:
        chunk = file.readline(chunk_size)
        line += chunk

        if len(chunk) < chunk_size or '\n' in chunk:
            break

    return json.loads(line)





if __name__ == '__main__':
    calculate_TF_IDF()