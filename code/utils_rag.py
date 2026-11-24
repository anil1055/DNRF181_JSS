from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import numpy as np
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
import re
#embeddings = OllamaEmbeddings(model="gpt-oss-20b-128k") #model="llama3.1:8b", gpt-oss-20b
embeddings = OllamaEmbeddings(
    model="bge-m3",  # or "mxbai-embed-large" gemma bge-m3 for gpt-oss
)

def create_retriever(paper):
    """
    Create a retriever for a given paper.

    :param paper: The name of the paper
    :type paper: str

    :return: The retriever
    :rtype: langchain.retrieval.RetrievalQA
    """
    
    collection_path = "vdb_chroma_random/"+ paper
    paper_path = 'data/random_papers/full/' + paper + '.txt' #paper.upper() or lower
    
    print(f'Loading vector DB from {collection_path} ...')
    vdb = Chroma(persist_directory=collection_path, embedding_function=embeddings)

    if len(vdb.get()["ids"]) == 0:
        print("No documents found in VectorDB. Creating new index...")
        vdb = Chroma(persist_directory=collection_path, embedding_function=embeddings)
        file_loader = TextLoader(paper_path)
        document = file_loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
        chunks = text_splitter.split_documents(document)
        chunks = clean_chunks(chunks)
        print(f'Generated {len(chunks)} chunks from {paper}')
        for i, chunk in enumerate(chunks):
            try:
                vdb.add_documents([chunk])
            except Exception as e:
                print(f"❌ Chunk {i} failed: {repr(chunk.page_content[:100])}")
                continue
        print(f'{len(chunks)} documents have been added to the vector DB')    
    else:
        print(f"VectorDB already contains {len(vdb.get()['ids'])} documents. Skipping indexing.")

    #retriever = vdb.as_retriever(search_kwargs={"k":min(10,len(vdb.get()["ids"]))})

    return vdb

def clean_chunks(chunks):
    cleaned = []
    for chunk in chunks:
        text = chunk.page_content
        # Remove null bytes and non-printable characters
        text = text.replace('\x00', '').strip()
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        # Skip empty or too-short chunks
        if len(text) < 20:
            continue
        chunk.page_content = text
        cleaned.append(chunk)
    print(f"Cleaned: {len(chunks) - len(cleaned)} bad chunks removed, {len(cleaned)} remaining")
    return cleaned


def filter_chunks_by_similarity(vdb, query_text, fallback_k=5):
    # Get all chunks and their similarity scores to the query
    chunks_with_scores = vdb.similarity_search_with_score(query_text, k=len(vdb.get()["ids"]))
    
    scores = [score for _, score in chunks_with_scores]

    mean = np.mean(scores)
    median = np.median(scores)
    threshold = min(median, mean)

    # Filter chunks with better (lower) score
    filtered_chunks = [doc.page_content for doc, score in chunks_with_scores if score <= threshold]
    print(f"Similarity threshold: {threshold:.4f}, chunk size: {str(len(filtered_chunks))}")
    if (not filtered_chunks) or len(filtered_chunks) < 5:
        print(f"No chunks passed threshold. Falling back to top-{fallback_k} chunks.")
        filtered_chunks = [doc.page_content for doc, _ in chunks_with_scores[:fallback_k]]

    return filtered_chunks