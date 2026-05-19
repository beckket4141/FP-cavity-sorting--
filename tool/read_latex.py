"""
Parse the thesis LaTeX files: main.tex and supplement.tex.
Extract structure (sections), equations, figures, tables, and key parameters.
"""
import re
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def strip_comments(text):
    """Remove LaTeX comments (lines starting with %)."""
    lines = []
    for line in text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("%"):
            continue
        lines.append(line)
    return "\n".join(lines)


def extract_equations(text):
    """Extract equations with their labels."""
    patterns = [
        (r"\\begin\{equation\}(.*?)\\end\{equation\}", "equation"),
        (r"\\begin\{align\*\}(.*?)\\end\{align\*\}", "align*"),
        (r"\\begin\{align\}(.*?)\\end\{align\}", "align"),
        (r"\\\[(.*?)\\\]", "display"),
    ]
    equations = []
    for pattern, env in patterns:
        for m in re.finditer(pattern, text, re.DOTALL):
            body = m.group(1).strip()
            label = ""
            label_m = re.search(r"\\label\{([^}]+)\}", body)
            if label_m:
                label = label_m.group(1)
            equations.append({"label": label, "body": body, "env": env})
    return equations


def extract_figures(text):
    """Extract figure captions and labels."""
    figs = []
    for m in re.finditer(
        r"\\begin\{figure\}.*?\\caption\{(.*?)\}.*?\\label\{([^}]+)\}",
        text, re.DOTALL,
    ):
        figs.append({"caption": m.group(1).strip(), "label": m.group(2)})
    return figs


def extract_tables(text):
    """Extract table captions and labels."""
    tabs = []
    for m in re.finditer(
        r"\\begin\{table\}.*?\\caption\{(.*?)\}.*?\\label\{([^}]+)\}",
        text, re.DOTALL,
    ):
        tabs.append({"caption": m.group(1).strip(), "label": m.group(2)})
    return tabs


def extract_sections(text):
    """Extract section titles."""
    secs = []
    for m in re.finditer(r"\\(?:sub)?section\*?\{(.*?)\}", text):
        secs.append(m.group(1).strip())
    return secs


def extract_key_params(text):
    """Extract key physical and design parameters."""
    params = {}

    # k* values
    k_stars = re.findall(r"\$k\^\*=\s*([0-9/]+)\$", text)
    params["k_star_candidates"] = list(set(k_stars))

    # M values
    m_vals = re.findall(r"\$M\s*=\s*(\d+)\$", text)
    params["M_values_in_text"] = list(set(m_vals))

    # Finesse
    f_vals = re.findall(
        r"\$\\mathcal\{F\}(?:_\{\\min\})?\s*=\s*([0-9.]+)\$", text
    )
    params["finesse_values"] = list(set(f_vals))

    # tau_0
    tau_vals = re.findall(r"\$\\tau_0\s*=\s*(\d+)\$", text)
    params["tau0_values"] = list(set(tau_vals))

    # L/R
    lr_vals = re.findall(r"\$L/R\s*=\s*([0-9.]+)\$", text)
    params["LR_values"] = list(set(lr_vals))

    # FSR values
    fsr_vals = re.findall(
        r"\$([0-9.]+)\\pm[0-9.]+\$.*?GHz.*FSR", text
    )
    if not fsr_vals:
        fsr_vals = re.findall(r"FSR.*?([0-9.]+)\\pm", text)
    params["FSR_values"] = list(set(fsr_vals))

    return params


def read_latex(filepath):
    """Read and parse a LaTeX file, returning structured content."""
    with open(filepath, "r", encoding="utf-8") as f:
        raw = f.read()

    clean = strip_comments(raw)
    equations = extract_equations(clean)
    figures = extract_figures(clean)
    tables = extract_tables(clean)
    sections = extract_sections(clean)
    params = extract_key_params(clean)

    # Extract abstract
    abstract = ""
    abs_m = re.search(r"\\begin\{abstract\*\}(.*?)\\end\{abstract\*\}", clean, re.DOTALL)
    if abs_m:
        abstract = abs_m.group(1).strip()

    return {
        "file": filepath,
        "abstract": abstract,
        "sections": sections,
        "equations": equations,
        "figures": figures,
        "tables": tables,
        "params": params,
    }


def print_summary(data):
    """Pretty-print a summary of the parsed LaTeX document."""
    print(f"\n{'='*70}")
    print(f"File: {data['file']}")
    print(f"{'='*70}")

    print(f"\n--- Abstract ({len(data['abstract'])} chars) ---")
    print(data["abstract"][:300] + "..." if len(data["abstract"]) > 300 else data["abstract"])

    print(f"\n--- Sections ({len(data['sections'])}) ---")
    for s in data["sections"]:
        print(f"  - {s}")

    print(f"\n--- Equations ({len(data['equations'])}) ---")
    for eq in data["equations"]:
        tag = eq["label"] if eq["label"] else "(no label)"
        body_preview = eq["body"].replace("\n", " ")[:100]
        print(f"  [{tag}] {body_preview}...")

    print(f"\n--- Figures ({len(data['figures'])}) ---")
    for fig in data["figures"]:
        print(f"  [{fig['label']}] {fig['caption'][:120]}...")

    print(f"\n--- Tables ({len(data['tables'])}) ---")
    for tab in data["tables"]:
        print(f"  [{tab['label']}] {tab['caption'][:120]}...")

    print(f"\n--- Key Parameters ---")
    for k, v in data["params"].items():
        if v:
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main_tex = os.path.join(BASE_DIR, "Sorting_in_FP_cavities", "main.tex")
    supp_tex = os.path.join(BASE_DIR, "supplementary_matirial", "supplement.tex")

    for path in [main_tex, supp_tex]:
        if os.path.exists(path):
            data = read_latex(path)
            print_summary(data)
        else:
            print(f"File not found: {path}")
