# Replication Package: Multi-Label Text Classification using Large Language Models and Prompting Techniques for Software Effort Estimation: An Extended Study

This repository is the replication package for the paper **"Multi-Label Text Classification using Large Language Models and Prompting Techniques for Software Effort Estimation: An Extended Study"**, submitted to the *Journal of Systems and Software* (JSS).

## Overview

The study evaluates how well open-weight large language models (LLMs) can identify which **web effort estimation predictors** a research paper uses. The task is multi-label text classification (MLTC): for each paper, the model selects zero or more predictors from a hierarchical taxonomy, and its output is compared with a manually built ground truth.

The package contains everything needed to inspect or re-run the study:

- the taxonomy and ground-truth annotations,
- the paper texts in the three input forms (full text, selected sections, summary),
- all prompt templates,
- the code that runs the LLMs, converts their answers to binary label matrices, and computes the metrics,
- the raw binary predictions and the final metric tables.

### Study design at a glance

| Dimension | Values |
|---|---|
| **Models** | `gpt-oss-20b`, `Llama-3.1-8B-Instruct`, `Qwen2.5-14B-Instruct`, `Gemma-3-12B` |
| **Prompting techniques** | SC (self-consistency), CoT (chain-of-thought), MP (metacognitive prompting), PS (plan-and-solve), plus 1-shot versions of SC, CoT and MP |
| **Paper input (content type)** | `FP`: full paper · `SF`: paper with non-essential sections removed · `FS`: LLM-generated summary (written `SP` in the paper's tables) · `RAG`: retrieved chunks of the full paper |
| **Taxonomy presentation** | `FT`: full taxonomy in one prompt · `ST`: taxonomy split into its level-3 categories, one prompt per category, answers merged · `HT`: hierarchical prompt (taxonomy shown as class → predictors) |
| **Datasets** | *internal*: 88 papers, 210 predictors · *external*: 24 papers, 120 predictors |

Each combination of a content type and a taxonomy presentation is a **configuration**, for example `FP + FT` or `RAG + HT`. The 12 configurations are crossed with the 7 prompting techniques for each model.

## Repository structure

```
.
├── Taxonomy_Britto.xlsx        # Original taxonomy (starting point)
├── Taxonomy_updated.xlsx       # Updated taxonomy used in the study (210 predictors)
├── GT_updated.xlsx             # Ground truth, internal dataset (predictor -> papers)
├── GT_external.xlsx            # Ground truth, external dataset (120 predictors, papers p1..p24)
│
├── Data/
│   ├── internal/               # 88 papers (s1..s88)
│   │   ├── full results/       #   full text (FP)
│   │   ├── sections/           #   selected sections (SF)
│   │   ├── summary/            #   LLM summaries (FS)
│   │   └── references_APA_88papers.xlsx   # APA reference of every paper
│   └── external/               # 24 papers (p1..p24)
│       ├── full/  sections/  summary/
│
├── Prompts/
│   ├── Summarize.py            # Prompt used to summarize papers
│   ├── prompt_techniques/      # SC, CoT, MP, PS and 1-shot variants (FT and ST)
│   └── hierarchical_prompts/   # Same techniques for the hierarchical (HT) prompt
│
├── code/
│   ├── pdf2text.py             # PDF -> text (full paper)
│   ├── pdf2text_secFiles.py    # PDF -> text without references, related work, background, ...
│   ├── extract_summarize.py    # LLM-based paper summaries
│   ├── run_llama.py            # Inference with Hugging Face models (Llama, Qwen, Gemma)
│   ├── run_gpt.py              # Inference with gpt-oss (via Ollama's OpenAI-compatible API)
│   ├── run_rag.py              # RAG inference, Hugging Face models
│   ├── run_rag_gpt.py          # RAG inference, gpt-oss
│   ├── utils.py, utils_rag.py  # Shared helpers (data loading, filtering, vector store)
│   ├── convert2binary.py       # Model answers (CSV) -> binary paper x label matrices
│   ├── merge_process.py        # Merge per-paper binary files into one workbook per model
│   └── evaluate_mltc.py        # Metric computation
│
├── binary_results/             # Binary predictions (merged), internal dataset
│   └── external/               # Binary predictions (merged), external dataset
└── results_llms/
    ├── internal/               # <model>_metrics.xlsx
    └── external/               # <model>_metrics.xlsx
```

## Data

**Taxonomy.** `Taxonomy_updated.xlsx` has four levels (`level1`–`level4`) and a description for every predictor. The predictors are the `level4` entries. Prompts show the model each predictor as `name (description)`, and the model must answer with exact predictor names.

**Ground truth.** In `GT_updated.xlsx` and `GT_external.xlsx`, each row is one predictor and the `papers` column lists the papers that use it (for example `s19, s47`).

**Papers.** Each paper is stored as a `.txt` file named after its ID, in three forms:

| Form | Folder | Content |
|---|---|---|
| Full paper (`FP`) | `full results/` (internal), `full/` (external) | Complete text converted from the PDF |
| Selected sections (`SF`) | `sections/` | Text without references, related work, background, biographies and acknowledgements |
| Summary (`FS`) | `summary/` | Summary generated with `Prompts/Summarize.py` |

Paper `s52` is the 1-shot example and is excluded from every evaluation.

> **Data availability note:** 

## Pipeline

```
PDF papers
   │  pdf2text.py / pdf2text_secFiles.py
   ▼
FP and SF texts ──extract_summarize.py──▶ FS texts
   │
   │  run_llama.py / run_gpt.py / run_rag.py / run_rag_gpt.py
   ▼
Predicted predictors per paper (CSV, one file per prompt × configuration)
   │  convert2binary.py
   ▼
Binary paper × label matrices (one .xlsx per paper, one sheet per prompt)
   │  merge_process.py
   ▼
merged_binary_<model>.xlsx   (in binary_results/)
   │  evaluate_mltc.py
   ▼
<model>_metrics.xlsx         (in results_llms/)
```

### Inference details

- **Decoding.** SC samples 3 answers at temperature 0.7 and keeps the predictors that appear in at least 2 of them. All other techniques use one deterministic run (temperature 0).
- **Context limit.** Inputs are truncated to 100,000 tokens.
- **ST.** One prompt is sent per level-3 taxonomy category, and the category answers are merged.
- **RAG.** Papers are split into chunks of 1,500 characters with 300 overlap, embedded with `bge-m3` (through Ollama) and stored in a Chroma vector store. Only the retrieved chunks go into the prompt.
- **Output filtering.** Answers are matched against the taxonomy list, so only valid predictor names are kept.

## Evaluation

`evaluate_mltc.py` computes all metrics on the full paper × label space. Each external paper is padded with all-zero rows up to 210 labels so that both datasets share the same label space.

| Metric | Meaning |
|---|---|
| `macro_f1_supp` | Macro F1 over labels with at least one positive paper (Equation 1 in the paper) |
| `macro_f1_all` | Macro F1 over all labels (labels without support count as F1 = 0) |
| `micro_f1`, `precision`, `recall`, `jaccard` | Pooled over all paper-label pairs |
| `sample_f1`, `sample_jaccard` | Mean of per-paper scores |
| `hamming` | (FP + FN) / (papers × labels) |
| `hallucination` | Mean per-paper share of predicted labels that are wrong (FP / predictions) |
| `cardinality_diff` | Mean number of predicted labels minus mean number of true labels (positive = over-generation) |
| `legacy_*` | Metrics of an earlier, flawed protocol, kept only for comparison |

Each `<model>_metrics.xlsx` contains a `long` sheet (every prompt × configuration), one sheet per metric (configurations × prompts, with mean, median and standard deviation) and a `top3` sheet.

## Reproducing the results

### Option A: recompute the tables from the shipped predictions (no GPU needed)

```bash
pip install numpy pandas scikit-learn openpyxl
python code/evaluate_mltc.py
```

Edit the `SETTINGS` block at the top of `evaluate_mltc.py` first:

- `DATASETS`: `["internal"]`, `["external"]` or both
- `BINARY_ROOT`: folder that holds the per-model folders of per-paper binary files
- `OUT_DIR`: where the metric workbooks are written

### Option B: re-run the full pipeline

1. **Install dependencies**

   ```bash
   pip install torch transformers huggingface_hub openai tqdm pandas numpy openpyxl xlsxwriter scikit-learn \
               pymupdf4llm langdetect \
               langchain-chroma langchain-community langchain-text-splitters langchain-ollama langchain-openai
   ```

2. **Prepare the services**
   - A Hugging Face account with access to the gated models, plus a token.
   - [Ollama](https://ollama.com) serving `gpt-oss` on `http://localhost:11434` (for `run_gpt.py` and `run_rag_gpt.py`) and `bge-m3` (for RAG).
   - A CUDA GPU large enough for the chosen model.

3. **Adjust paths and credentials.** Several scripts contain machine-specific values that must be changed before running:
   - `login(token="user_token")`: put in your own Hugging Face token (better: set the `HF_TOKEN` environment variable).
   - Data folders in `text_types_addr` (for example `data/results`, `data/external/results`) must point to the folders in `Data/`.
   - Absolute paths in `pdf2text*.py`, `extract_summarize.py`, `convert2binary.py` and `merge_process.py`.
   - The model name in `utils.model_load(...)` (or the Ollama model name for gpt-oss).
   - The `taxonomy_list` in the `__main__` block (`FT`, `ST`, `HT`).

4. **Run the stages in order**

   ```bash
   python code/pdf2text.py              # full text
   python code/pdf2text_secFiles.py     # selected sections
   python code/extract_summarize.py     # summaries
   python code/run_llama.py             # or run_gpt.py / run_rag.py / run_rag_gpt.py
   python code/convert2binary.py
   python code/merge_process.py
   python code/evaluate_mltc.py
   ```

LLM outputs can vary between hardware, library versions and sampling runs, so a re-run may not match the numbers in `results_llms/` exactly. The predictions used in the paper are in `binary_results/`.

## Results files

`binary_results/merged_binary_<model>.xlsx` (internal) and `binary_results/external/merged_binary_<model>_ext.xlsx` (external) hold one sheet per prompting technique (`SC`, `COT`, `COT_SHOT`, `MP`, `PS`, `MP_SHOT`, `SC_SHOT`). Rows are paper × label pairs and the columns are:

| Column | Meaning |
|---|---|
| `Labels` | Predictor name |
| `is_gt` | 1 if the predictor is in the ground truth of that paper |
| `<content>_<taxonomy>` | 1 if the model predicted the predictor, for example `FP_FT`, `RAG_HT`, `SF_ST`. `FS_*` columns are the `SP` configurations of the paper; in some files `ST` is spelled `TH` |
| `File_name` | Paper ID |

## Citation

If you use this package, please cite:

```bibtex
@article{[CITATION-KEY],
  title   = {Multi-Label Text Classification using Large Language Models and Prompting Techniques for Software Effort Estimation: An Extended Study},
  author  = {[AUTHORS]},
  journal = {Journal of Systems and Software},
  year    = {[YEAR]},
  doi     = {[DOI]}
}
```
