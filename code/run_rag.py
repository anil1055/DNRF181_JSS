from hierarchical_prompts import COT_, MP_, PS_, SC_, COT_1shot_, MP_1shot_, SC_1shot_
from prompt_techniques import COT, MP, PS, SC, COT_1shot, MP_1shot, SC_1shot
import utils
import utils_rag
import os
from tqdm import tqdm
from huggingface_hub import login
login(token = "user_token")
import torch
'''
text_types_addr = {
    'FP': 'data/results', 
    'SF': 'data/sections',
    'FS': 'data/summary'
    }
'''
text_types_addr = {
    'FP': 'data/external/results', 
    'SF': 'data/external/sections',
    'FS': 'data/external/summary'
    }

hier_prompts_types = {
    'COT': COT_.PROMPT,
    'COT_SHOT': COT_1shot_.PROMPT,
    'SC': SC_.PROMPT,
    'PS': PS_.PROMPT,
    'MP': MP_.PROMPT,
    'SC_SHOT': SC_1shot_.PROMPT,
    'MP_SHOT': MP_1shot_.PROMPT
    }   

prompts_types = {
    'COT': COT.PROMPT,
    'COT_SHOT': COT_1shot.PROMPT,
    'SC': SC.PROMPT,
    'PS': PS.PROMPT,
    'MP': MP.PROMPT,
    'SC_SHOT': SC_1shot.PROMPT,
    'MP_SHOT': MP_1shot.PROMPT
    } 


def generate_output(tokenizer, output_tokens):
    output_text = tokenizer.decode(output_tokens, skip_special_tokens=True)  
    model_response = output_text.split("'None'.assistant")[1] #'None'.\n\nassistant
    model_response = utils.smart_split(model_response)

    return model_response

def annotate_paper_multiple_times(llm, tokenizer, prompt, prompt_type = "CoT"):

    if prompt_type == 'SC' or prompt_type == "SC_SHOT":
        temperature = 0.7
        num_samples = 3
        do_sample = True
        top_k = 50
    else:
        temperature = 0.0
        num_samples = 1
        do_sample = False
        top_k = 0  # unused

    results = []
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
        
    for i in range(num_samples):
        output_tokens = llm.generate(
        **inputs,
        max_new_tokens=300,
        temperature=temperature,
        do_sample=do_sample,
        top_p=0.9,
        top_k=top_k if do_sample else None,
        repetition_penalty=1.2,
        pad_token_id=tokenizer.eos_token_id
        )

        model_response = generate_output(tokenizer, output_tokens[0])
        if prompt_type == "SC" or prompt_type == "SC_SHOT":          
            output = utils.filter_result(model_response.strip(), taxo_list)
            results.append(output)
        else:
            results.append(model_response.strip())

    torch.cuda.empty_cache()
    return results


def common_prepare_llm(chunks, tax_text, prompt_type, llm, tokenizer):
    raw_prompt = prompts_types.get(prompt_type)
    
    if prompt_type == "COT_SHOT" or prompt_type == "SC_SHOT" or prompt_type == "MP_SHOT":        
        vdb_ex = utils_rag.create_retriever("S52")
        example_chunks = utils_rag.filter_chunks_by_similarity(vdb_ex, query_text=tax_text)
        prompt = raw_prompt.format(example_paper=example_chunks,paper='\n'.join(chunks), taxonomy=tax_text)
    else: 
        prompt = raw_prompt.format(paper='\n'.join(chunks), taxonomy=tax_text)

    result = annotate_paper_multiple_times(llm, tokenizer, prompt, prompt_type=prompt_type)
    common_items = utils.get_common_items(result, k=k)

    res = (', '.join(common_items)).strip()

    return res

if __name__ == "__main__":
    gt_dict = utils.return_ground_truth()
    taxonomy_dict = utils.return_taxonomy()
    content_type = "RAG"
    taxonomy_list = ["FT", "ST", "HT"] #FT, TH, HT
    llm, tokenizer = utils.model_load("meta-llama/Llama-3.1-8B-Instruct") #meta-llama/Llama-3.1-8B-Instruct, Qwen/Qwen2.5-14B-Instruct
    taxo_list = [str(value.split("(")[0]).strip() for cat in taxonomy_dict for value in taxonomy_dict[cat] ]
    prompt_names = prompts_types.keys()
    k=1
    for taxonomy_type in taxonomy_list: 
        if taxonomy_type == "HT": 
            prompt_names = hier_prompts_types.keys()
        for prompt_type in prompt_names:
            if prompt_type == 'SC' or prompt_type == "SC_SHOT": k = 2
            else: k = 1
            target_folder = os.path.join("outputs/external/llama/", prompt_type)
            os.makedirs(target_folder, exist_ok=True)
            papers_dict = utils.read_txt_files_as_dict("data/external/results/")    
            
            result_addr = f'{content_type}_{taxonomy_type}_1.csv'
            results = []
            for paper in tqdm(papers_dict):
                if (prompt_type == "COT_SHOT" or prompt_type == "SC_SHOT" or prompt_type == "MP_SHOT") and paper == "s52": # 1-shot CoT paper
                        continue
                else:
                    vdb = utils_rag.create_retriever(paper)
                    tax_text = ""           
                    if taxonomy_type == 'ST':
                        res_th = ""
                        for cat in taxonomy_dict:
                            tax_text = '\n'.join(taxonomy_dict[cat])
                            tax_text += '\n'
                            chunks = utils_rag.filter_chunks_by_similarity(vdb, query_text=tax_text)
                            res = common_prepare_llm(chunks, tax_text, prompt_type, llm, tokenizer)
                            res_th += res + ", "
                        res = utils.filter_result(res_th, taxo_list)
                        print(res)
                        results.append([paper, "Hierarchical Taxonomy", res])
                            
                    if taxonomy_type == 'FT':
                        for cat in taxonomy_dict:
                            tax_text += '\n'.join(taxonomy_dict[cat])
                            tax_text += '\n'
                        chunks = utils_rag.filter_chunks_by_similarity(vdb, query_text=tax_text)
                        res = common_prepare_llm(chunks, tax_text, prompt_type, llm, tokenizer)              
                        res = utils.filter_result(res, taxo_list)
                        print(res)
                        results.append([paper, "Full Taxonomy", res])
                    
                    if taxonomy_type == 'HT':
                            """#OPTION 1
                            for cat in taxonomy_dict:
                                tax_text += "-" + str(cat).upper() + '\n+'
                                tax_text += '\n+'.join(taxonomy_dict[cat])
                                tax_text += '\n'
                            """
                            #OPTION 2
                            for cat in taxonomy_dict:
                                tax_text += "-" + str(cat).upper() + ': ["'
                                tax_text += '", "'.join(taxonomy_dict[cat])
                                tax_text += '"]\n'       
                            chunks = utils_rag.filter_chunks_by_similarity(vdb, query_text=tax_text)
                            res = common_prepare_llm(chunks, tax_text, prompt_type, llm, tokenizer)              
                            res = utils.filter_result(res, taxo_list)
                            print(res)
                            results.append([paper, "Real Hierarchical", res])
                                
            utils.write_list_to_csv(results, target_folder + "/" + result_addr)
            
        

