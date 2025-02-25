#!/usr/bin/env python3
import argparse
import pdfplumber
import os

def extract_pdf_text(input_pdf, output_txt):
    """Extract text from PDF and save to text file"""
    try:
        with pdfplumber.open(input_pdf) as pdf:
            content = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    content.append(text)
            
            full_text = "\n\n".join(content)
            
            # Create output directory if needed
            os.makedirs(os.path.dirname(output_txt), exist_ok=True)
            
            with open(output_txt, 'w', encoding='utf-8') as f:
                f.write(full_text)
                
            print(f"Successfully extracted text to {output_txt}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract text from PDF')
    parser.add_argument('-i', '--input', required=True, help='Input PDF file')
    parser.add_argument('-o', '--output', help='Output text file')
    
    args = parser.parse_args()
    
    # Set default output filename if not provided
    output_path = args.output or os.path.splitext(args.input)[0] + '.txt'
    
    extract_pdf_text(args.input, output_path) 