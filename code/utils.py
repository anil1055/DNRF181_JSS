import os
import openpyxl
import pandas as pd  
import transformers
import torch

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    AutoTokenizer,
)

def read_txt_files_as_dict(folder_path):
    file_dict = {}
    
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):  # Only process .txt files
            file_path = os.path.join(folder_path, filename)
            
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            file_dict[filename.replace('.txt', '').lower()] = content

    return file_dict


def read_txt_files_as_dict_random100(folder_path):
    file_dict = {}
    
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):  # Only process .txt files
            file_path = os.path.join(folder_path, filename)
            
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            file_dict[filename.replace('.txt', '')] = content

    return file_dict


def read_txt_file_1_shot(file_path):
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
            
    return content


def model_load(model_name):
    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, 
        torch_dtype="auto", 
        device_map="auto",
    )
    return model, tokenizer

def trim_input_to_max_tokens(input_text, max_tokens=100000, tokenizer = None):
    tokens = tokenizer.encode(input_text)
    if len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]  # Keep only the first max_tokens tokens
        print("Token count exceed!!!")
    
    trimmed_text = tokenizer.decode(tokens)
    
    return trimmed_text


import re
def smart_split(text):
    # Split by commas first
    items = [item.strip() for item in text.split(",")]
    result = []
    
    for item in items:
        item = item.replace("_", " ")
        
        # If it’s all uppercase (with optional hyphen), keep as is
        if re.fullmatch(r'[A-Z0-9\-]+', item):
            result.append(item)
        else:
            # Insert spaces before capital letters that are preceded by lowercase
            # or followed by lowercase letters (PascalCase rule)
            spaced = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', item)
            spaced = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', ' ', spaced)
            result.append(spaced)
    
    return ", ".join(result)


def return_ground_truth():
    gt_dict = {}

    workbook = openpyxl.load_workbook("GT_updated.xlsx")
    sheet = workbook.active
    rows = sheet.iter_rows(values_only=True)

    next(rows)

    for row in rows:
        for paper in row[5].split(','):
            p = paper.strip()
            if p not in gt_dict:
                gt_dict[p] = []
            gt_dict[p].append(row[3].lower().strip())
            
    return gt_dict


def excel_to_list_of_lists(file_path):
    df = pd.read_excel(file_path)
    list_of_lists = df.values.tolist()
    return list_of_lists


def return_taxonomy(file_path="Taxonomy_updated.xlsx"):
    taxonomy_dict = {}
    taxonomy = excel_to_list_of_lists(file_path)
    
    for tax in taxonomy:
        
        if tax[-3] not in taxonomy_dict:
            taxonomy_dict[tax[-3]] = []
            
        taxonomy_dict[tax[-3]].append(f"{str(tax[-2]).lower().strip()} ({str(tax[-1]).capitalize().strip()})")
        
    return taxonomy_dict

def get_common_items(results, k):
    items_list = [set(res.split(',')) for res in results]
    item_counts = {}
    for items in items_list:
        for item in items:
            item = item.strip()
            if item in item_counts:
                item_counts[item] += 1
            else:
                item_counts[item] = 1
    return [item for item, count in item_counts.items() if count >= k]


def filter_result(long_text, keep_list):
    long_text = long_text.replace("\n", ",")
    words = long_text.split(",")

    # Filter words: keep only those that contain any of the keywords
    filtered_words = [
        kw for kw in keep_list
        if any(kw.lower().strip() in word.lower().strip() for word in words)
    ]

    filtered_words = list(dict.fromkeys(filtered_words))  # removes duplicates while preserving order
    # Join back into a string
    filtered_text = ", ".join(filtered_words)
    return filtered_text


def write_list_to_csv(list_of_lists, file_path, headers=['Paper', 'Category', 'Predictors']):
    # Optional: convert non-string items like lists or dicts to strings
    cleaned_data = [
        [str(cell) if isinstance(cell, (list, dict)) else cell for cell in row]
        for row in list_of_lists
    ]

    # Create DataFrame
    df = pd.DataFrame(cleaned_data, columns=headers)

    # Write to Excel
    df.to_csv(file_path, index=False)
