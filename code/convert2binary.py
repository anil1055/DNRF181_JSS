import utils
import os
import csv
from collections import defaultdict
import pandas as pd
from collections import defaultdict
import zipfile

def dict2list(gt_dict):     
    all_labels = []

    for gt in gt_dict:
        for label in gt_dict[gt]:
            if label not in all_labels:
                all_labels.append(label.lower())
    return all_labels


def read_paperResult(folder_path):
    res = defaultdict(lambda: defaultdict(dict))      
    for subfolder in os.listdir(folder_path):
        subfolder_path = os.path.join(folder_path, subfolder)
        if os.path.isdir(subfolder_path):  
            for file_name in os.listdir(subfolder_path):
                try:
                    file_path = os.path.join(subfolder_path, file_name)
                    if file_name.endswith('.csv'):  
                        file_key = os.path.splitext(file_name)[0][:-2]
                        with open(file_path, 'r', encoding='utf-8') as csv_file:
                            reader = csv.DictReader(csv_file)
                            for row in reader:
                                paper = row['Paper'].strip()
                                predictors = [p.strip().lower() for p in  row['Predictors'].split(',')]
                                
                                if paper not in res[subfolder]:
                                    res[subfolder][paper] = {}
                                if file_key not in res[subfolder][paper]:
                                    res[subfolder][paper][file_key] = set()
                                res[subfolder][paper][file_key].update(predictors)
                except Exception as e:
                    print(e)

    # Convert sets to lists for JSON serialization (optional)
    res = {
        subfolder: {
            paper: {file_key: list(predictors) for file_key, predictors in papers.items()}
            for paper, papers in subfolders.items()
        }
        for subfolder, subfolders in res.items()
    }
    return res


def convert_TP_FN(res, papers, gt_dict):
    res_formal = defaultdict(lambda: defaultdict(dict))

    for subfolder, papers in res.items():
        for paper, experiments in papers.items():
            try:
                ground_truth = gt_dict[paper]#.get(paper, [])
                for experiment, predictors in experiments.items():
                    results = []
                    for gt_predictor in ground_truth:
                        if any(pred.lower() == gt_predictor.lower() for pred in predictors):
                            results.append("TP")
                        else:
                            results.append("FN")
                    res_formal[subfolder][paper][experiment] = results
            except Exception as e:
                print(str(e) + " don't have a GT")
                continue

    return res_formal


def generate_TP_FN_files(res_formal, output_path):

    for subfolder_name, papers in res_formal.items():
        for paper, experiment_data in papers.items():
            # Define the file path for this paper
            try:
                file_path = os.path.join(output_path, f"{paper.strip()}.xlsx")
                # Check if the file already exists
                file_exists = os.path.exists(file_path)        
                # Optional: Validate file before opening
                if file_exists:
                    try:
                        with zipfile.ZipFile(file_path, 'r') as zip_check:
                            zip_check.testzip()
                    except zipfile.BadZipFile:
                        print(f"Invalid Excel file: {file_path}. It will be recreated.")
                        os.remove(file_path)
                        file_exists = False
                # Use ExcelWriter with the appropriate mode
                with pd.ExcelWriter(file_path, engine='openpyxl', mode='a' if file_exists else 'w') as writer:
                    if file_exists and subfolder_name in writer.book.sheetnames:
                        print(f"Sheet '{subfolder_name}' already exists in '{paper}.xlsx'. Skipping.")
                        continue
                    # Prepare rows for the DataFrame
                    rows = []
                    columns = ["labels"] 
                    experiments = sorted(set(exp for exp in experiment_data.keys()))
                    columns.extend(experiments)
        
                    # Get the ground truth predictors for this paper
                    if paper.strip() not in gt_dict:
                        print(f"Warning: Ground truth not found for paper '{paper}'. Skipping.")
                        continue
                    ground_truth = gt_dict[paper.strip()]
                    for label in ground_truth:
                        row = [label]  # Start with the ground truth predictor
                        for experiment in experiments:
                            # Append TP/FN or "N/A" if the experiment is missing
                            row.append(
                                experiment_data.get(experiment, ["N/A"] * len(ground_truth))[
                                    ground_truth.index(label)
                                ]
                            )
                        rows.append(row)
        
                    df = pd.DataFrame(rows, columns=columns)
                    df.to_excel(writer, sheet_name=subfolder_name, index=False)
            except Exception as e:
                print(str(e) + ": " + paper)

    print("All results have been saved successfully.")

    

def generate_binary_files(res, gt, all_labels, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Collect all papers from the `res` structure
    papers = set(
        paper for prompts in res.values() for paper in prompts.keys()
    )
    
    for paper in papers:
        # Prepare Excel writer for the current paper
        try:
            output_path = os.path.join(output_folder, f"{paper}.xlsx")     
            #ground_truth = gt_dict[paper]
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                for prompt, papers in res.items():   
                    if (prompt == "COT_SHOT" or prompt == "SC_SHOT" or prompt == "MP_SHOT") and paper == "s52": # 1-shot CoT paper
                        continue
                    else:
                        experiments = papers[paper]
                        # Use `all_labels` directly
                        unique_labels = all_labels
                        is_gt = [1 if label in gt.get(paper, []) else 0 for label in unique_labels]
                        #is_gt = [1 for label in ground_truth]
                        
                        # Determine the maximum number of repetitions dynamically
                        max_repetition = 1               
                        # Prepare data rows for the sheet
                        rows = []
                        for repetition in range(1, max_repetition + 1):
                            for label, is_gt_val in zip(unique_labels, is_gt): #ground_truth
                                row = {"Labels": label, "is_gt": is_gt_val, "Repetition": repetition}
                                for exp_name, predictors in experiments.items():
                                    row[exp_name] = 1 if label in predictors else 0
                                rows.append(row)
                        
                        # Convert rows to DataFrame
                        df = pd.DataFrame(rows)
                        
                        # Ensure all experiment columns are included even if empty
                        exp_methods = [name for name in experiments.keys()]
                        for method in set(exp_methods):
                            if method not in df.columns:
                                df[method] = 0
                        # Write DataFrame to a sheet named after the prompt
                        df.to_excel(writer, index=False, sheet_name=prompt)
        except Exception as e:
            print(str(e) + ": " + paper)

    print(f"Excel files written to {output_folder}.")


if __name__ == "__main__":
    gt_dict = utils.return_ground_truth()
    all_labels = dict2list(gt_dict)
    for repetition in range(3,4):
        folder_path = "/home/precise_au/nvidia-workbench/dnrf_project/outputs/external/llama" #Should change filenames in the folder !!!!  _" + str(repetition) + "          
        res = read_paperResult(folder_path)
        folder = "llama" #+ str(1) #change for repetition
        target_folder = os.path.join("/home/precise_au/nvidia-workbench/dnrf_project/outputs/binaryFiles/external/", folder)
        os.makedirs(target_folder, exist_ok=True)
        generate_binary_files(res, gt_dict, all_labels, target_folder)

    