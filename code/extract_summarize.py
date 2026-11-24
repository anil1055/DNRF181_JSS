import prompts
from prompts import Summarize
import utils
import os
from tqdm import tqdm
from huggingface_hub import login
login(token = "user_token")
    
import transformers
import torch

from transformers import (
    AutoConfig,
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    AutoTokenizer,
    TrainingArguments,
)

text_types_addr = {
    'FP': '/home/anil/LlamaTexts/results', 
    'SF': '/home/anil/LlamaTexts/sections',
    'FS': '/home/anil/LlamaTexts/summary'
    }

prompts_type = Summarize.PROMPT
    

def model_load(model_name):
    # Load model and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, 
        torch_dtype=torch.float16, 
        device_map="auto"
    )
    
    print(model.config.max_position_embeddings)
    return model, tokenizer


def chunk_text(text, max_tokens=4000, overlap=300):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i + max_tokens]
        chunks.append(" ".join(chunk))
        i += max_tokens - overlap
    return chunks

def summarize_paper(chunk, llm, tokenizer):
    prompt = prompts_type.format(paper=chunk)
    messages = [
    {
        "role": "system",
        "content": prompt
    }]
    prompt_ = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(
        prompt_,
        return_tensors="pt",
    ).to("cuda")

    output_tokens = llm.generate(
            **inputs,
            max_new_tokens=4096,
            temperature=0.7,
            repetition_penalty=1.2,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id 
        )
    
    output_text = tokenizer.decode(output_tokens[0], skip_special_tokens=True)
    summary = output_text.split(".assistant")[1].strip()  # Remove prompt, keep summar
    torch.cuda.empty_cache()

    return summary
    
    
if __name__ == "__main__":
    papers_dict = utils.read_txt_files_as_dict(text_types_addr.get("FP", ""))
    llm, tokenizer = model_load("meta-llama/Llama-3.1-8B-Instruct")
        
    result_addr = "/home/anil/LlamaTexts/summary/"
    for paper in tqdm(papers_dict):
        papers_text = utils.trim_input_to_max_tokens(papers_dict[paper], 100000, tokenizer)

        #chunks = chunk_text(papers_text)
        #summaries = [summarize_paper(chunk,llm, tokenizer) for chunk in chunks]
        #final_summary = "\n".join(summaries)
        
        final_summary = summarize_paper(papers_text ,llm, tokenizer)  
            
        with open(result_addr + paper + ".txt", "w", encoding="utf-8") as f:
            f.write(str(final_summary))

