from cython import int
import json


def extract_dict(text: str, key: str) -> dict:
    start_index: int = text.index(f'"{key}"') + len(key) + 3

    while 1:
        if text[start_index] == '{':
            break

        start_index += 1
    
    end_index: int = start_index
    bracket_count: int = 0
    quotation_count: int = 0
    letter: str

    while 1:
        letter = text[end_index]

        if letter == '\\':
            end_index += 1
            letter = text[end_index]
        elif letter == '{':
            bracket_count += 1
        elif letter == '}' and quotation_count % 2 == 0:
            bracket_count -= 1
        elif letter == '"':
            quotation_count += 1

        if bracket_count < 1:
            break

        end_index += 1

    result: str = text[start_index:end_index+1]

    return json.loads(result)