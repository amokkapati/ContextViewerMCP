"""Test 2: PDF Text Extraction Accuracy

Generates PDFs with known ground-truth text using reportlab, then extracts
text using pdfplumber (analogous to PDF.js getTextContent) and measures
accuracy via difflib.SequenceMatcher.
"""

import difflib
import os
import textwrap

import matplotlib.pyplot as plt
import pdfplumber
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

# Ground-truth texts for each PDF
DOCUMENTS = {
    "Simple Paragraph": (
        "The ContextViewerMCP system provides a web-based interface for "
        "browsing and selecting code. Users can highlight text in their browser "
        "and submit selections for analysis by Claude. The server handles file "
        "serving, PDF rendering, and state management through a clean REST API."
    ),
    "Multi-Paragraph": (
        "Modern software development relies heavily on tooling that bridges the "
        "gap between code editors and AI assistants. The ability to select and "
        "share specific code regions enables more precise and contextual "
        "conversations about software.\n\n"
        "The MCP protocol provides a standardized interface for tool integration. "
        "By exposing file browsing, text selection, and navigation capabilities "
        "through MCP, the ContextViewerMCP project enables seamless interaction "
        "between developers and AI models.\n\n"
        "Performance characteristics of such systems are critical for user "
        "experience. Latency in file serving, accuracy of text extraction from "
        "PDFs, and throughput under concurrent load all impact the perceived "
        "responsiveness and reliability of the tool."
    ),
    "Two-Column Layout": (
        "Column layouts present a challenge for text extraction systems. "
        "When text flows across multiple columns on a page, extraction tools "
        "must correctly identify the reading order. PDF.js and pdfplumber "
        "both attempt to reconstruct reading order from the underlying text "
        "objects embedded in the PDF stream."
    ),
    "Bullet Points": (
        "Key features of ContextViewerMCP include: "
        "1. Real-time file browsing with directory tree navigation. "
        "2. Syntax-highlighted code viewing for over 50 languages. "
        "3. PDF rendering with text selection support. "
        "4. LaTeX compilation and preview capability. "
        "5. MCP integration for AI assistant tool use."
    ),
    "Dense Academic": (
        "We present an evaluation framework for measuring the performance "
        "characteristics of web-based code viewing systems. Our methodology "
        "encompasses three dimensions: file serving latency as a function of "
        "document size, fidelity of text extraction from rendered PDF documents, "
        "and system throughput under varying levels of concurrent request load. "
        "Results demonstrate sub-linear latency scaling with respect to file "
        "size and robust handling of concurrent connections up to moderate load "
        "levels, validating the architectural choices underlying the system."
    ),
}


def _build_simple_pdf(path, text):
    """Build a single-flow PDF with the given text."""
    doc = SimpleDocTemplate(path, pagesize=letter,
                            leftMargin=inch, rightMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    style = styles["BodyText"]
    style.fontSize = 11
    style.leading = 14

    story = []
    for para in text.split("\n\n"):
        story.append(Paragraph(para, style))
        story.append(Spacer(1, 12))
    doc.build(story)


def _build_two_column_pdf(path, text):
    """Build a two-column layout PDF."""
    frame1 = Frame(inch, inch, 3 * inch, 9 * inch, id="col1")
    frame2 = Frame(4.5 * inch, inch, 3 * inch, 9 * inch, id="col2")
    doc = BaseDocTemplate(path, pagesize=letter)
    doc.addPageTemplates([
        PageTemplate(id="TwoCol", frames=[frame1, frame2])
    ])
    styles = getSampleStyleSheet()
    style = styles["BodyText"]
    style.fontSize = 11
    style.leading = 14
    story = [Paragraph(text, style)]
    doc.build(story)


def generate_pdfs(tmp_dir):
    """Generate test PDFs, return dict of {name: path}."""
    paths = {}
    for name, text in DOCUMENTS.items():
        fname = name.lower().replace(" ", "_") + ".pdf"
        path = os.path.join(tmp_dir, fname)
        if name == "Two-Column Layout":
            _build_two_column_pdf(path, text)
        else:
            _build_simple_pdf(path, text)
        paths[name] = path
    return paths


def extract_text(pdf_path):
    """Extract text from a PDF using pdfplumber."""
    text_parts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return " ".join(text_parts)


def normalize(text):
    """Normalize whitespace for comparison."""
    return " ".join(text.split())


def run(base_url, tmp_dir, results_dir):
    """Run PDF accuracy test and save graph."""
    pdf_paths = generate_pdfs(tmp_dir)

    names = []
    accuracies = []

    for name, path in pdf_paths.items():
        ground_truth = normalize(DOCUMENTS[name])
        extracted = normalize(extract_text(path))
        ratio = difflib.SequenceMatcher(None, ground_truth, extracted).ratio()
        accuracy = ratio * 100

        names.append(name)
        accuracies.append(accuracy)
        print(f"  {name:>20s}: {accuracy:.1f}%")

    # Plot
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#2563eb", "#7c3aed", "#db2777", "#ea580c", "#16a34a"]
    bars = ax.bar(names, accuracies, color=colors[:len(names)], edgecolor="white",
                  linewidth=0.5)

    # Add value labels on bars
    for bar, acc in zip(bars, accuracies):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                f"{acc:.1f}%", ha="center", va="bottom", fontsize=10,
                fontweight="bold")

    ax.set_ylim(0, 105)
    ax.set_ylabel("Extraction Accuracy (%)", fontsize=12)
    ax.set_title("PDF Text Extraction Accuracy by Document Type", fontsize=14)
    ax.tick_params(axis="x", rotation=15)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()

    out_path = os.path.join(results_dir, "pdf_text_accuracy.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  Saved: {out_path}")
    return out_path
