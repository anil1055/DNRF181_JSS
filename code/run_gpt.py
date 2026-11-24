from hierarchical_prompts import COT_, MP_, PS_, SC_, COT_1shot_, MP_1shot_, SC_1shot_
from prompt_techniques import COT, MP, PS, SC, COT_1shot, MP_1shot, SC_1shot
import utils
import os
from tqdm import tqdm
from huggingface_hub import login
login(token = "user_token")
import torch
from openai import OpenAI
import random
from transformers import (
    AutoTokenizer,
)

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

  
def annotate_paper_multiple_times(client, tokenizer, prompt, prompt_type = "CoT"):
    """
    Annotate a paper multiple times with an LLM.

    Parameters
    ----------
    llm : str
        The name of the LLM to use.
    prompt : str
        The prompt to use for the LLM.
    num_runs : int, optional
        The number of times to run the LLM. Defaults to 3.
    temperature : float, optional
        The temperature to use for the LLM. Defaults to 0.7.

    Returns
    -------
    list
        A list of the results of each run.
    """
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
    for i in range(num_samples):     
        # Prepare sampling options
        options = {
            "repeat_penalty": 1.2,
        }

        if do_sample:
            options.update({
                "temperature": temperature,
                "top_p": 0.9,
                "top_k": top_k,
        })
        else:
            options["temperature"] = 0
            options["top_p"] = 1.0

        response = client.chat.completions.create(
            model="gpt-oss-20b-128k",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            extra_body={"options": options}
        )

        model_choice = response.choices[0].message
        model_response = model_choice.content
        if not model_response:
            model_response = model_choice.reasoning
        print(model_response)
        if prompt_type == "SC" or prompt_type == "SC_SHOT":            
            output = utils.filter_result(model_response.strip(), taxo_list)
            results.append(output)
        else:
            results.append(model_response.strip())

    torch.cuda.empty_cache()
    return results


def common_prepare_llm(papers_text, tax_text, prompt_type, content_type, client, tokenizer):
    raw_prompt = prompts_types.get(prompt_type)

    if prompt_type == "COT_SHOT" or prompt_type == "SC_SHOT" or prompt_type == "MP_SHOT": 
        example_text = ""
        if content_type == "FP": example_text = utils.read_txt_file_1_shot("data/results/S52.txt")
        elif content_type == "SF": example_text = utils.read_txt_file_1_shot("data/sections/S52.txt")
        else: example_text = utils.read_txt_file_1_shot("data/summary/s52.txt")
        prompt = raw_prompt.format(example_paper=example_text,paper=papers_text, taxonomy=tax_text)
    else: 
        prompt = raw_prompt.format(paper=papers_text, taxonomy=tax_text)
    result = annotate_paper_multiple_times(client, tokenizer, prompt, prompt_type=prompt_type)
    common_items = utils.get_common_items(result, k=k)

    res = (', '.join(common_items)).strip()
    return res
    
if __name__ == "__main__":
    gt_dict = utils.return_ground_truth()
    taxonomy_dict = utils.return_taxonomy()
    taxonomy_list = ["FT", "ST", "HT"] #FT, TH, HT

    client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama"
    )
    tokenizer = tokenizer = AutoTokenizer.from_pretrained("openai/gpt-oss-20b") #meta-llama/Llama-3.1-8B-Instruct, Qwen/Qwen2.5-14B-Instruct
    taxo_list = [str(value.split("(")[0]).strip() for cat in taxonomy_dict for value in taxonomy_dict[cat] ]
    prompt_names = prompts_types.keys()
    k = 1
    for taxonomy_type in taxonomy_list:
        if taxonomy_type == "HT": 
            prompt_names = hier_prompts_types.keys()
        for prompt_type in prompt_names:
            if prompt_type == 'SC' or prompt_type == "SC_SHOT": k = 2
            else: k = 1
            target_folder = os.path.join("outputs/external/gpt-oss/", prompt_type)
            os.makedirs(target_folder, exist_ok=True)
            for key, value in text_types_addr.items():
                content_type = key
                papers_dict = utils.read_txt_files_as_dict(value)
                
                result_addr = f'{content_type}_{taxonomy_type}_1.csv'
                results = []
                for paper in tqdm(papers_dict):
                    if (prompt_type == "COT_SHOT" or prompt_type == "SC_SHOT" or prompt_type == "MP_SHOT") and paper == "s52": # 1-shot CoT paper
                        continue
                    else:
                        papers_text = utils.trim_input_to_max_tokens(papers_dict[paper], 100000, tokenizer)

                        tax_text = ""               
                        if taxonomy_type == 'ST':
                            res_th = ""
                            for cat in taxonomy_dict:
                                tax_text = '\n'.join(taxonomy_dict[cat])
                                tax_text += '\n'

                                res = common_prepare_llm(papers_text, tax_text, prompt_type, content_type, client, tokenizer)
                                res_th += res + ", "
                            res = utils.filter_result(res_th, taxo_list)
                            print(res)
                            results.append([paper, "Hierarchical Taxonomy", res])
                                
                        if taxonomy_type == 'FT':
                            for cat in taxonomy_dict:
                                tax_text += '\n'.join(taxonomy_dict[cat])
                                tax_text += '\n'
                            res = common_prepare_llm(papers_text, tax_text, prompt_type, content_type, client, tokenizer)
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
                            
                            res = common_prepare_llm(papers_text, tax_text, prompt_type, content_type, client, tokenizer)
                            res = utils.filter_result(res, taxo_list)
                            print(res)
                            results.append([paper, "Hierarchical Prompt", res])

                utils.write_list_to_csv(results, target_folder + "/" + result_addr)