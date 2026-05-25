import ExtractDict
import json
import time
from pathlib import Path

PATH = Path(__file__).parent

def extract_dict2(text, key):
    start_index = text.index('"' + key + '"') + len(key) + 3

    while True:
        if text[start_index] == '{':
            break

        start_index += 1
    
    end_index = start_index
    bracket_count = 0
    quotation_count = 0
    while True:
        char = text[end_index]

        if char == '\\':
            end_index += 1
            char = text[end_index]
        elif char == '{':
            bracket_count += 1
        elif char == '}' and quotation_count % 2 == 0:
            bracket_count -= 1
        elif char == '"':
            quotation_count += 1

        if bracket_count < 1:
            break

        end_index += 1

    result = text[start_index:end_index+1]
    return json.loads(result)


with open(PATH/'a.txt', 'r', encoding='utf-8') as f:
    text = f.read()#"assac, asc, \"same\":{\"Penguinホロ歌は癒しの万能薬\":\"cute\"}"

key = "videoDetails"
start_index = text.index(f'"{key}"') + len(key) + 3

stat = time.perf_counter()
for i in range(0, 1000):
    a = ExtractDict.extract_dict(text, key)
end_time = time.perf_counter()
print(end_time-stat)

stat = time.perf_counter()
for i in range(0, 1000):
    b = extract_dict2(text, key)
end_time = time.perf_counter()
print(end_time-stat)


print(a == b)