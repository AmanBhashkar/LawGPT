from legal_chunker import legal_chunker as chunker
from pinecone_service import pinecone_service
from tqdm import tqdm

try:
    # Read and process document
    print("Reading document...")
    with open('income_tax_act_1961.md', 'r') as f:
        content = f.read()
    
    print("Chunking document...")
    chunks = chunker.chunk_document(content)
    print(f"Chunk sizes: {[len(c.split()) for c in chunks]}")
    print(f"Max chunk size: {max(len(c.split()) for c in chunks)}")
    
    # Store in Pinecone with progress tracking
    print(f"\nStoring {len(chunks)} chunks in Pinecone...")
    with tqdm(total=len(chunks), desc="Uploading chunks") as pbar:
        pinecone_service.store_legal_chunks(
            chunks=chunks,
            document_id="income_tax_act_1961",
            progress_bar=pbar  # Pass the progress bar directly
        )
    print(f"\n✅ Successfully stored {len(chunks)} legal chunks in Pinecone")

    # After generating chunks

except Exception as e:
    print(f"\n❌ Error processing document: {str(e)}")
    raise