"""
File Extraction Helper for Project Proposal Reports.
Extracts clean text from PDF, Word (.docx), and text files.
"""
import os
import re
import zipfile
import xml.etree.ElementTree as ET

try:
    import pypdf
except ImportError:
    pypdf = None

def extract_text_from_document(file_path):
    """
    Extracts text content from PDF, DOCX, and TXT files.
    Returns clean text string or empty string on error.
    """
    if not os.path.exists(file_path):
        return ""

    ext = file_path.lower().split('.')[-1]

    # 1. PDF Extraction
    if ext == 'pdf':
        if not pypdf:
            return ""
        try:
            reader = pypdf.PdfReader(file_path)
            extracted = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    extracted.append(text)
            return "\n".join(extracted).strip()
        except Exception as e:
            print(f"[!] Error extracting PDF text: {e}")
            return ""

    # 2. DOCX Word Document Extraction (Pure Python via Zip XML)
    elif ext == 'docx':
        try:
            with zipfile.ZipFile(file_path) as z:
                xml_content = z.read('word/document.xml')
                tree = ET.fromstring(xml_content)
                texts = [node.text for node in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
                return " ".join(texts).strip()
        except Exception as e:
            print(f"[!] Error extracting DOCX text: {e}")
            return ""

    # 3. Plain Text / Markdown / Code files
    else:
        encodings = ['utf-8', 'latin-1', 'cp1252']
        for enc in encodings:
            try:
                with open(file_path, 'r', encoding=enc, errors='ignore') as f:
                    return f.read().strip()
            except Exception:
                continue
        return ""
