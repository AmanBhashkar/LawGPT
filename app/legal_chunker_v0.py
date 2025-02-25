import spacy
import re
from typing import List

class LegalDocumentChunker:
    def __init__(self, window_size=3, overlap=1, max_chunk_size=512):
        self.nlp = spacy.load("en_core_web_lg")
        self.nlp.max_length = 1000000
        self.window_size = window_size
        self.overlap = overlap
        self.max_chunk_size = max_chunk_size

        # Add chunk boundary patterns
        ruler = self.nlp.add_pipe("entity_ruler", before="ner")
        patterns = [
            {"label": "CHUNK_BOUNDARY", "pattern": [{"TEXT": {"REGEX": "(§|Article|Section|CLAUSE)"}}]},
            {"label": "CHUNK_BOUNDARY", "pattern": [{"LOWER": {"IN": ["plaintiff", "defendant", "exhibit"]}}]}
        ]
        ruler.add_patterns(patterns)

    def initial_split(self, content: str) -> List[str]:
        """Split content into paragraphs preserving markdown structure"""
        paragraphs = [
            p.strip() for p in re.split(r'\n\s*\n', content) 
            if p.strip() and not re.match(r'^#+ ', p)
        ]
        return paragraphs

    def process_chunk(self, text: str) -> List[str]:
        """Entity-aware chunking within a paragraph window"""
        doc = self.nlp(text)
        chunks = []
        current_chunk = []
        
        for sent in doc.sents:
            # Split at boundary entities
            if any(ent.label_ == "CHUNK_BOUNDARY" for ent in sent.ents):
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                chunks.append(sent.text)
            else:
                current_chunk.append(sent.text)
                if len(' '.join(current_chunk)) > self.max_chunk_size:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks

    def chunk_document(self, content: str) -> List[str]:
        # Split into paragraphs first
        paragraphs = self.initial_split(content)
        
        # Create sliding windows over paragraphs
        final_chunks = []
        for i in range(0, len(paragraphs), self.window_size - self.overlap):
            window_paras = paragraphs[i:i+self.window_size]
            window_text = '\n\n'.join(window_paras)
            
            # Process window with entity-aware chunking
            window_chunks = self.process_chunk(window_text)
            final_chunks.extend(window_chunks)
        
        return self._postprocess_chunks(final_chunks)

    def _postprocess_chunks(self, chunks: List[str]) -> List[str]:
        """Merge small chunks while respecting max size"""
        merged = []
        current_chunk = []
        
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
                
            if len(' '.join(current_chunk + [chunk])) <= self.max_chunk_size:
                current_chunk.append(chunk)
            else:
                merged.append(' '.join(current_chunk))
                current_chunk = [chunk]
        
        if current_chunk:
            merged.append(' '.join(current_chunk))
        
        return merged

    def save_chunks(self, chunks: List[str], filename: str):
        """Save chunks with separation boundaries"""
        with open(filename, 'w') as f:
            f.write('\n==========================\n'.join(chunks))

if __name__ == "__main__":
    chunker = LegalDocumentChunker(
        window_size=4,
        overlap=1,
        max_chunk_size=1024
    )
    with open('income_tax_act_1961.md', 'r') as f:
        content = f.read()
    chunks = chunker.chunk_document(content)
    chunker.save_chunks(chunks, 'legal_chunks_v0.txt')

