import pymupdf4llm
import os
from langdetect import detect, LangDetectException

def is_gibberish(text):
    if len(text) < 100:
        return True
    
    letters = sum(c.isalpha() for c in text)
    non_letters = sum(not c.isalpha() for c in text)
    
    if letters / (non_letters + 1) < 0.5:  
        return True
    
    try:
        detected_language = detect(text)
        if detected_language not in ['en']:  
            return True
    except LangDetectException:
        return True  
    
    return False


llama_reader = pymupdf4llm.LlamaMarkdownReader()
dir(llama_reader)

for filename in os.listdir("/home/anil/Studies"):
    file_path = os.path.join("/home/anil/Studies", filename)   
    
    llama_docs = llama_reader.load_data(file_path)
    full_text = ""
    for doc in llama_docs:
        full_text += doc.text
        
    if is_gibberish(full_text):
        print(f"Skipping gibberish file: {filename}")
        continue
        
    with open("/home/anil/LlamaTexts/results/" + filename[:-4] + ".txt", "a", encoding="utf-8") as f:
        f.write(full_text)