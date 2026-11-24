import pandas as pd
import os
import numpy as np

def merge_files_one_folder(folder, output_file):
    # Expected sheet names
    sheet_names = ["SC", "COT", "COT_SHOT", "MP", "PS", "MP_SHOT", "SC_SHOT"]

    # Collect all Excel files in the folder
    files = [f for f in os.listdir(folder) if f.endswith(".xlsx")]

    if not files:
        print("[⚠️] No Excel files found in folder.")
        return

    # Read all files into memory
    workbooks = {f: pd.read_excel(os.path.join(folder, f), sheet_name=None) for f in files}

    # Start writer for merged output
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        for sheet in sheet_names:
            dfs = []
            for i, (filename, wb) in enumerate(workbooks.items()):
                if filename == "s52.xlsx":
                    continue
                if sheet not in wb:
                    print(f"[⚠️] Sheet '{sheet}' missing in {filename}, skipped.")
                    continue

                df = wb[sheet]
                # Drop "Repetition" column if it exists
                df = df.drop(columns=["Repetition"], errors="ignore")

                name_no_ext = os.path.splitext(filename)[0]

                if i == 0:
                    # Rename the label column too
                    df = df.add_suffix(f"_{name_no_ext}")
                    base_df = df.copy()
                else:
                    # Drop label column if exists
                    df = df.drop(columns=["Labels"], errors="ignore")
                    # Add suffix for uniqueness
                    df = df.add_suffix(f"_{name_no_ext}")
                    base_df = pd.concat([base_df, df], axis=1)

            if base_df is None:
                continue

            # Save merged dataframe
            base_df.to_excel(writer, sheet_name=sheet, index=False)

        print(f"[✅] Merged file written: {output_file}")

def merge_files(folder1, folder2, repetition, output_folder):
    sheet_names = ["SC", "COT", "COT_SHOT", "MP", "PS", "MP_SHOT"]

    # Match files by name
    files1 = set(os.listdir(folder1))
    files2 = set(os.listdir(folder2))
    common_files = files1 & files2  # process only files that exist in both
    for filename in common_files:
        path1 = os.path.join(folder1, filename)
        path2 = os.path.join(folder2, filename)

        try:
            wb1 = pd.read_excel(path1, sheet_name=None)  # all sheets
            wb2 = pd.read_excel(path2, sheet_name=None)

            # Start writer for this merged file
            output_path = os.path.join(output_folder, f"{filename}")
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                for sheet in sheet_names:
                    if (sheet == "COT_SHOT" or sheet == "SC_SHOT" or sheet == "MP_SHOT") and filename == "s52": # 1-shot CoT paper
                        continue
                    else:
                        if sheet not in wb1 or sheet not in wb2:
                            print(f"[⚠️] Sheet '{sheet}' missing in {filename}, skipped.")
                            continue

                        df1 = wb1[sheet]
                        df2 = wb2[sheet]
                        
                        df2["Repetition"] = repetition
                        # Check columns match by name (ignore order)
                        if set(df1.columns) != set(df2.columns):
                            print(f"[❌] Sheet '{sheet}' in '{filename}' has different columns. Skipping sheet.")
                            continue

                        # Reorder columns to match df1
                        df2 = df2[df1.columns]

                        # Combine rows
                        merged_df = pd.concat([df1, df2], axis=0, ignore_index=True)

                        # Save to sheet
                        merged_df.to_excel(writer, sheet_name=sheet, index=False)
                print(f"[✅] Merged file written: {output_path}")

        except Exception as e:
            print(f"[⚠️] Error processing {filename}: {str(e)}")


def merge_excel_sheets(input_file, output_file):
    # Define sheet names
    sheet_names = ["SC", "COT", "COT_SHOT", "MP", "PS", "MP_SHOT", "SC_SHOT"]

    # Read all sheets into dict of DataFrames
    sheets = {name: pd.read_excel(input_file, sheet_name=name) for name in sheet_names}

    # Use first sheet as reference for structure
    first_sheet = next(iter(sheets.values()))

    # Split into numeric and non-numeric columns
    numeric_cols = first_sheet.select_dtypes(include=[np.number]).columns
    non_numeric_cols = first_sheet.select_dtypes(exclude=[np.number]).columns

    # Collect numeric arrays from each sheet
    numeric_arrays = [df[numeric_cols].to_numpy(dtype=float) for df in sheets.values()]
    arr = np.stack(numeric_arrays)  # shape: (num_sheets, rows, cols)

    # Compute median, sum, average for numeric data
    median_arr = np.nanmedian(arr, axis=0)
    sum_arr = np.nansum(arr, axis=0)
    avg_arr = np.nanmean(arr, axis=0)

    # Reconstruct DataFrames
    median_df = pd.DataFrame(median_arr, columns=numeric_cols)
    sum_df = pd.DataFrame(sum_arr, columns=numeric_cols)
    avg_df = pd.DataFrame(avg_arr, columns=numeric_cols)

    # Add back non-numeric columns (take them from the first sheet)
    for col in non_numeric_cols:
        median_df[col] = first_sheet[col]
        sum_df[col] = first_sheet[col]
        avg_df[col] = first_sheet[col]

    # Reorder columns to match original order
    median_df = median_df[first_sheet.columns]
    sum_df = sum_df[first_sheet.columns]
    avg_df = avg_df[first_sheet.columns]

    # Save to Excel with 3 sheets
    with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
        median_df.to_excel(writer, sheet_name="Median", index=False)
        sum_df.to_excel(writer, sheet_name="Sum", index=False)
        avg_df.to_excel(writer, sheet_name="Average", index=False)

    print(f"[✅] Merged sheets written to {output_file}")


if __name__ == "__main__":
    process = 1
    if process == 1:
        merge_files_one_folder(
        folder="/home/precise_au/nvidia-workbench/dnrf_project/outputs/binaryFiles/external/llama", 
        output_file="/home/precise_au/nvidia-workbench/dnrf_project/outputs/merge_files/merged_llama_ext.xlsx"
        )
    else:
        merge_excel_sheets("/home/anil/DNRF/results_output/hamming_each_paper.xlsx", "/home/anil/DNRF/results_output/hamming_med_sum.xlsx")
    """
    for merge in range(1,4,2):        
        if merge == 1: 
            folder1 = "/home/anil/DNRF/binaryResults/repetition_" + str(merge) + "/"
            folder2 = "/home/anil/DNRF/binaryResults/repetition_" + str(merge+1) + "/"
            output_folder = "/home/anil/DNRF/binaryResults/repetition_4/"
            merge_files(folder1,folder2,2,output_folder) 
        else:
            folder1 = "/home/anil/DNRF/binaryResults/repetition_" + str(merge+1) + "/"
            folder2 = "/home/anil/DNRF/binaryResults/repetition_" + str(merge) + "/"
            output_folder = "/home/anil/DNRF/mergeOutput/" 
            merge_files(folder1,folder2,3,output_folder) 
    """