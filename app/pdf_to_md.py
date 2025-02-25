import fitz  # PyMuPDF
from multiprocessing import Pool, cpu_count
import os

def bbox_contains(outer, inner):
    """Check if inner bbox is contained within outer bbox"""
    return (inner[0] >= outer[0] and inner[1] >= outer[1] and
            inner[2] <= outer[2] and inner[3] <= outer[3])

def format_as_markdown_table(data):
    """Convert 2D array to Markdown table"""
    if not data or not any(data):
        return ""
    
    # Convert None to empty string and clean empty rows
    data = [
        [cell or "" for cell in row]
        for row in data
        if any((cell or "").strip() for cell in row)
    ]
    
    if not data:
        return ""
    
    columns = max(len(row) for row in data)
    
    # Create header separator
    separator = ["---"] * columns
    
    # Build table
    table = []
    for i, row in enumerate(data):
        # Fill missing columns and ensure string type
        row = [str(cell or "") for cell in row[:columns]] + [""] * (columns - len(row))
        # Escape pipes in content
        row = [cell.replace("|", "\\|") for cell in row]
        table.append("| " + " | ".join(row) + " |")
        if i == 0:
            table.append("| " + " | ".join(separator) + " |")
    
    return "\n".join(table)

def process_page(args):
    """Process a single page in parallel"""
    pdf_path, page_num = args
    try:
        doc = fitz.open(pdf_path)
        page = doc.load_page(page_num)
        markdown = []
        
        # First extract tables and their bounding boxes
        tables = page.find_tables()
        table_bboxes = [table.bbox for table in tables]
        
        # Process tables first
        for table in tables:
            table_data = table.extract()
            md_table = format_as_markdown_table(table_data)
            if md_table:
                markdown.append(md_table + "\n")
        
        # Process text blocks that are not in tables
        blocks = page.get_text("blocks")
        for block in blocks:
            if block[6] == 0:  # Text block
                text = block[4].strip()
                if text:
                    block_bbox = (block[0], block[1], block[2], block[3])
                    # Skip blocks inside table areas
                    if any(bbox_contains(t_bbox, block_bbox) for t_bbox in table_bboxes):
                        continue
                    # Simple heading detection (adjust threshold as needed)
                    if block[3] - block[1] > 20:  # Height-based heading detection
                        markdown.append(f"# {text}")
                    else:
                        markdown.append(text)
        
        doc.close()
        return (page_num, "\n\n".join(markdown))
    
    except Exception as e:
        print(f"Error processing page {page_num}: {str(e)}")
        return (page_num, "")

def pdf_to_markdown(pdf_path, md_path, processes=None):
    """Convert PDF to Markdown using multiprocessing"""
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    doc.close()
    
    # Create pool of workers
    processes = processes or os.cpu_count()
    with Pool(processes=processes) as pool:
        # Distribute page numbers across workers
        results = pool.map(process_page, [(pdf_path, pn) for pn in range(total_pages)])
    
    # Sort results by page number and combine
    results.sort(key=lambda x: x[0])
    full_md = "\n\n".join([r[1] for r in results if r[1]])
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(full_md)

if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert PDF to Markdown")
    parser.add_argument("input", help="Input PDF file")
    parser.add_argument("output", help="Output Markdown file")
    parser.add_argument("--processes", type=int, 
                      help="Number of parallel processes (default: CPU count)")
    args = parser.parse_args()
    
    pdf_to_markdown(args.input, args.output, args.processes)