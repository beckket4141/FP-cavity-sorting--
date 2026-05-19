"""
Read and extract text from the thesis PDF files.
Requires: pip install pymupdf (or PyPDF2 as fallback)
"""
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read_pdf_pymupdf(filepath):
    """Extract all text and metadata from a PDF using PyMuPDF (fitz)."""
    import fitz
    doc = fitz.open(filepath)
    metadata = doc.metadata
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        pages.append({"page": i + 1, "text": text})
    doc.close()
    return {"file": filepath, "metadata": metadata, "pages": pages, "num_pages": len(pages)}


def read_pdf_pypdf2(filepath):
    """Extract all text from a PDF using PyPDF2 (lightweight fallback)."""
    from PyPDF2 import PdfReader
    reader = PdfReader(filepath)
    metadata = reader.metadata
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        pages.append({"page": i + 1, "text": text or ""})
    return {"file": filepath, "metadata": metadata, "pages": pages, "num_pages": len(pages)}


def read_pdf(filepath):
    """Read a PDF with the best available library."""
    try:
        return read_pdf_pymupdf(filepath)
    except ImportError:
        print("PyMuPDF not installed, falling back to PyPDF2...")
        try:
            return read_pdf_pypdf2(filepath)
        except ImportError:
            raise ImportError(
                "Please install a PDF library: pip install pymupdf  (recommended) "
                "or pip install PyPDF2"
            )


def search_keywords(data, keywords):
    """Search for keywords in extracted PDF text, return pages with context."""
    results = {}
    for kw in keywords:
        results[kw] = []
        for page in data["pages"]:
            idx = page["text"].lower().find(kw.lower())
            if idx >= 0:
                start = max(0, idx - 50)
                end = min(len(page["text"]), idx + len(kw) + 100)
                results[kw].append({
                    "page": page["page"],
                    "context": "..." + page["text"][start:end] + "...",
                })
    return results


def safe_print(s):
    """Print safely on Windows GBK terminals."""
    try:
        print(s)
    except UnicodeEncodeError:
        print(s.encode("gbk", errors="replace").decode("gbk"))


def print_pdf_summary(data, keywords=None):
    """Print a summary of the PDF content."""
    safe_print(f"\n{'='*70}")
    safe_print(f"PDF: {data['file']}")
    safe_print(f"Pages: {data['num_pages']}")
    safe_print(f"{'='*70}")

    if keywords:
        safe_print(f"\n--- Keyword Search Results ---")
        results = search_keywords(data, keywords)
        for kw, hits in results.items():
            safe_print(f"\n  [{kw}] ({len(hits)} hits)")
            for h in hits[:3]:
                safe_print(f"    p.{h['page']}: {h['context'][:120]}")


if __name__ == "__main__":
    main_pdf = os.path.join(BASE_DIR, "Sorting_in_FP_cavities", "main.pdf")
    supp_pdf = os.path.join(
        BASE_DIR, "supplementary_matirial", "supplement 1.pdf"
    )

    keywords = [
        "Gouy", "FSR", "finesse", "capacity",
        "tau", "s_min", "extinction", "efficiency",
    ]

    for path in [main_pdf, supp_pdf]:
        if os.path.exists(path):
            data = read_pdf(path)
            print_pdf_summary(data, keywords=keywords)
        else:
            print(f"File not found: {path}")
