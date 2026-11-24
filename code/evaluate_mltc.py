"""evaluate_mltc.py
All metrics are computed over the full label space (paper x label). Runs directly with Run.
Settings are in the SETTINGS section. Output: outputs/results_v3/<dataset>/<model>_metrics.xlsx
"""
import os
import subprocess
import sys
import traceback
from pathlib import Path

# ---------- auto-install missing packages ----------
for _mod, _pip in [("numpy", "numpy"), ("pandas", "pandas"),
                   ("sklearn", "scikit-learn"), ("openpyxl", "openpyxl")]:
    try:
        __import__(_mod)
    except ImportError:
        print("Installing:", _pip)
        subprocess.check_call([sys.executable, "-m", "pip", "install", _pip])

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, hamming_loss

# ======================= SETTINGS =======================
SCRIPT_DIR = Path(__file__).resolve().parent
# The binaryFiles folder is searched automatically. If it is not found, uncomment the line below and set the path:
# BINARY_ROOT = Path(r"C:\Users\au785268\Downloads\DNRF_analysis\outputs\binaryFiles")
BINARY_ROOT = None
OUT_DIR = SCRIPT_DIR.parent / "outputs" / "results_llms"
DATASETS = ["external"]
MODELS = None                      # None = auto-detect from folders; or ["gemma", "llama", "qwen", "gpt-oss"]

# Expected number of rows (labels) in the raw files (BEFORE padding). None = no check
EXPECTED_LABELS = {"internal": 210, "external": 123}   # number of rows in the raw file
PAD_EXTERNAL_TO = 210    # pad the external data with zero rows up to this row count (None = no padding)

EXCLUDE = {"s52"}                  # the 1-shot example paper
# =======================================================

PROMPTS = {"SC": "SC", "COT": "CoT", "COT_SHOT": "1-CoT", "MP": "MP",
           "PS": "PS", "MP_SHOT": "1-MP", "SC_SHOT": "1-SC"}

# key -> (column index, name in the paper)    th = ST, fs = SP
CONFIGS = {
    "fp_th": (5, "FP + ST"),  "rag_th": (11, "RAG + ST"),
    "sf_th": (14, "SF + ST"), "fs_th": (8, "SP + ST"),
    "fp_ft": (3, "FP + FT"),  "fs_ft": (6, "SP + FT"),
    "sf_ft": (12, "SF + FT"), "rag_ft": (9, "RAG + FT"),
    "fp_ht": (4, "FP + HT"),  "fs_ht": (7, "SP + HT"),
    "sf_ht": (13, "SF + HT"), "rag_ht": (10, "RAG + HT"),
}
ROW_ORDER = ["FP + ST", "RAG + ST", "FP + FT", "SP + FT", "SP + ST", "SF + FT",
             "RAG + FT", "SF + ST", "FP + HT", "SP + HT", "SF + HT", "RAG + HT"]

# metric -> is higher better? (None = no ranking)
METRICS = {
    "macro_f1_supp": True,     # Equation (1): over labels with at least one positive
    "macro_f1_all": True,      # all labels (labels with zero support get F1=0)
    "micro_f1": True,          # pooled = 2J/(1+J)
    "sample_f1": True,         # mean of per-paper F1
    "precision": True,
    "recall": True,
    "hamming": False,          # (FP+FN)/(n_papers*n_labels)
    "jaccard": True,           # pooled
    "sample_jaccard": True,    # mean of per-paper Jaccard
    "hallucination": False,    # mean of per-paper FP/max(prediction count,1) (FDR in the paper)
    "cardinality_diff": None,  # mean prediction count - mean GT count (+ = over-generation)
    "legacy_macro_f1": True,   # OLD flawed protocol, for checking only
    "legacy_hamming": False,   # OLD flawed protocol, for checking only
}


# ---------------------------------------------------------------- helpers
def ratio(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(b > 0, a / b, 0.0)


def to_bin(series):
    """NaN (rows added by padding) -> 0."""
    return pd.to_numeric(series, errors="coerce").fillna(0).to_numpy() > 0


def norm_labels(series):
    return series.astype(str).str.strip().str.lower()


def find_root():
    if BINARY_ROOT is not None:
        return Path(BINARY_ROOT)
    for base in [SCRIPT_DIR, SCRIPT_DIR.parent, SCRIPT_DIR.parent.parent, Path.cwd()]:
        cand = base / "outputs" / "binaryFiles"
        if cand.is_dir():
            return cand
    raise FileNotFoundError("outputs\\binaryFiles not found. Set BINARY_ROOT manually.")


def has_xlsx(d):
    return any(f.lower().endswith(".xlsx") for f in os.listdir(d))


def model_folders(root, dataset):
    base = root / "external" if dataset == "external" else root
    if not base.is_dir():
        return []
    names = MODELS or sorted(d.name for d in base.iterdir()
                             if d.is_dir() and d.name.lower() != "external")
    return [(n, base / n) for n in names if (base / n).is_dir() and has_xlsx(base / n)]


def paper_files(folder):
    for f in sorted(os.listdir(folder)):
        if not f.lower().endswith(".xlsx") or f.startswith("~$"):
            continue
        pid = os.path.splitext(f)[0]
        if pid.lower() in EXCLUDE or pid.lower().startswith("merged"):
            continue
        yield pid, os.path.join(folder, f)


def load_papers(folder):
    papers = {pid: pd.read_excel(path, sheet_name=list(PROMPTS))
              for pid, path in paper_files(folder)}
    if not papers:
        raise FileNotFoundError(f"no paper xlsx files: {folder}")
    return papers


def build(papers, sheet, expected=None, pad_to=None):
    """-> Y (n x L), {config: P (n x L)}, paper_ids, label_names.
    If pad_to is given, dummy rows with GT=0 and prediction=0 are appended to the end of each paper."""
    ids, ref = list(papers), None
    Y, P = [], {k: [] for k in CONFIGS}
    pad = np.zeros(0, dtype=bool)
    for pid in ids:
        df = papers[pid][sheet]
        lab = norm_labels(df.iloc[:, 0])
        if lab.duplicated().any():
            raise ValueError(f"{pid}/{sheet}: duplicate label found")
        if expected and len(df) != expected:
            raise ValueError(f"{pid}/{sheet}: {len(df)} rows, expected {expected}")
        df = df.set_axis(lab, axis=0)
        if ref is None:
            ref = list(lab)
        df = df.loc[ref]                              # raises KeyError if a label is missing
        pad = np.zeros(max((pad_to or 0) - len(ref), 0), dtype=bool)
        Y.append(np.concatenate([to_bin(df.iloc[:, 1]), pad]))
        for k, (j, _) in CONFIGS.items():
            P[k].append(np.concatenate([to_bin(df.iloc[:, j]), pad]))
    labels = ref + [f"pad_{i + 1}" for i in range(len(pad))]
    return np.stack(Y), {k: np.stack(v) for k, v in P.items()}, ids, labels


def compute(Y, P):
    n, L = Y.shape
    tp, fp, fn = Y & P, ~Y & P, Y & ~P
    TP, FP, FN = tp.sum(), fp.sum(), fn.sum()

    tp_l, fp_l, fn_l = tp.sum(0), fp.sum(0), fn.sum(0)          # per label (Equation 1)
    f1_l = ratio(2 * tp_l, 2 * tp_l + fp_l + fn_l)
    supp = Y.sum(0) > 0

    tp_i, fp_i, fn_i = tp.sum(1), fp.sum(1), fn.sum(1)          # per paper
    pred_i, gt_i = P.sum(1), Y.sum(1)

    return {
        "macro_f1_supp": float(f1_l[supp].mean()) if supp.any() else np.nan,
        "macro_f1_all": float(f1_l.mean()),
        "micro_f1": float(ratio(2 * TP, 2 * TP + FP + FN)),
        "sample_f1": float(ratio(2 * tp_i, 2 * tp_i + fp_i + fn_i).mean()),
        "precision": float(ratio(TP, TP + FP)),
        "recall": float(ratio(TP, TP + FN)),
        "hamming": float((FP + FN) / (n * L)),
        "jaccard": float(ratio(TP, TP + FP + FN)),
        "sample_jaccard": float(ratio(tp_i, tp_i + fp_i + fn_i).mean()),
        "hallucination": float((fp_i / np.maximum(pred_i, 1)).mean()),
        "cardinality_diff": float(pred_i.mean() - gt_i.mean()),
    }


def legacy(Y, P):
    """Copy of the old protocol: only GT=1 entries, y_true is always 1 (for checking only)."""
    m = Y.ravel()
    yt = np.ones(int(m.sum()), dtype=int)
    yp = P.ravel()[m].astype(int)
    return {"legacy_macro_f1": f1_score(yt, yp, average="macro", zero_division=0),
            "legacy_hamming": hamming_loss(yt, yp)}


def evaluate_model(folder, expected, pad_to=None):
    papers = load_papers(folder)
    rows = []
    for sheet, pname in PROMPTS.items():
        Y, P, ids, labels = build(papers, sheet, expected, pad_to)
        for key, (_, cname) in CONFIGS.items():
            r = compute(Y, P[key])
            r.update(legacy(Y, P[key]))
            r.update(prompt=pname, config=cname)
            rows.append(r)
    info = {"n_papers": len(ids), "n_labels": len(labels),
            "n_padded": sum(l.startswith("pad_") for l in labels),
            "n_positive_labels": int((Y.sum(0) > 0).sum()),
            "papers_without_GT": int((Y.sum(1) == 0).sum()),
            "mean_GT_per_paper": round(float(Y.sum(1).mean()), 2)}
    return pd.DataFrame(rows), info


# ---------------------------------------------------------------- output
def write_excel(long, path):
    cols = list(PROMPTS.values())
    with pd.ExcelWriter(path) as w:
        long.to_excel(w, sheet_name="long", index=False)
        for m in METRICS:
            base = long.pivot(index="config", columns="prompt", values=m).loc[ROW_ORDER, cols]
            t = base.copy()
            t["Mean"], t["Median"], t["STD"] = base.mean(1), base.median(1), base.std(1)
            t.loc["Mean"] = list(base.mean(0)) + [np.nan] * 3
            t.loc["Median"] = list(base.median(0)) + [np.nan] * 3
            t.loc["STD"] = list(base.std(0)) + [np.nan] * 3
            t.to_excel(w, sheet_name=m)
        tops = []
        for m, hb in METRICS.items():
            if hb is None or m.startswith("legacy"):
                continue
            top = long.sort_values(m, ascending=not hb).head(3)[["config", "prompt", m]].copy()
            top.insert(0, "metric", m)
            top.columns = ["metric", "config", "prompt", "value"]
            tops.append(top)
        pd.concat(tops).to_excel(w, sheet_name="top3", index=False)


def main():
    root = find_root()
    print("binaryFiles:", root)
    print("output     :", OUT_DIR)

    for dataset in DATASETS:
        os.makedirs(OUT_DIR / dataset, exist_ok=True)
        folders = model_folders(root, dataset)
        if not folders:
            print(f"[{dataset}] no model folder found, skipped.")
        for model, folder in folders:
            try:
                pad_to = PAD_EXTERNAL_TO if dataset == "external" else None
                long, info = evaluate_model(folder, EXPECTED_LABELS.get(dataset), pad_to)
                out = OUT_DIR / dataset / f"{model}_metrics.xlsx"
                write_excel(long, out)
                print(f"\n[{dataset}/{model}] {info}\n  -> {out}")
                chk = long[(long.config == "RAG + ST") & (long.prompt == "SC")]
                print("  check RAG+ST+SC:",
                      chk[["recall", "precision", "micro_f1", "macro_f1_supp",
                           "hamming"]].round(3).to_dict("records"))
            except Exception:
                print(f"\n[{dataset}/{model}] ERROR:")
                traceback.print_exc()
    print("\nDone.")


if __name__ == "__main__":
    main()