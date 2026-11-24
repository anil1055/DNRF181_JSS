import pymupdf4llm
import os
from pymupdf4llm import LlamaMarkdownReader

reader = LlamaMarkdownReader()
excluded_sections = {
    "reference", "references", "related work", "related works",
    "bibliography", "bibliographies", "background", "literature review",
    "biography", "biographies", "acknowledgement", "acknowledgment",
    "acknowledgements", "acknowledgments"
}

def remove_sections(markdown, section_names):
    lines = markdown.splitlines()
    output = []
    skip = False

    for line in lines:
        if any(section.lower() in line.lower() for section in excluded_sections) and line.find("**") != -1:
            skip = True
            print("Section find!")
            continue
        if skip and line.strip().startswith("**"):
            if len(line.strip().split("**")[len(line.strip().split("**"))-1]) < 2:
                skip = False  # New section starts
        if not skip:
            output.append(line)

    return "\n".join(output)


for filename in os.listdir("/home/anil/Studies"):
    file_path = os.path.join("/home/anil/Studies", filename)  
    # Load PDF
    markdown = reader.load_data(file_path)
    full_text = "\n".join(doc.text for doc in markdown)
    # Load and structure the document
    cleaned_md = remove_sections(full_text, excluded_sections)
        
    with open("/home/anil/LlamaTexts/sections/" + filename[:-4] + ".txt", "w", encoding="utf-8") as f:
        f.write(cleaned_md)