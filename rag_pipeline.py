"""
rag_pipeline.py - Clean version with NO problematic dependencies
Uses simple text splitting and TF-IDF for embeddings
"""
import os
import re
import pickle
import numpy as np
from pypdf import PdfReader
import chromadb
import config
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class LocalRAGPipeline:
    def __init__(self, db_dir=None):
        if db_dir is None:
            db_dir = config.CHROMA_DB_DIR
        
        print("[rag_pipeline] Initializing...")
        
        # We'll use TF-IDF for embeddings (no heavy libraries!)
        self.vectorizer = TfidfVectorizer(max_features=200, stop_words='english', ngram_range=(1, 2))
        self.is_fitted = False
        self.all_chunks_cache = []  # Cache for chunks when fitting
        self.vectorizer_path = os.path.join(db_dir, "vectorizer.pkl")
        
        self.chroma_client = chromadb.PersistentClient(path=db_dir)
        print("[rag_pipeline] ChromaDB client created")
        
        self.collection = self.chroma_client.get_or_create_collection(
            name=config.COLLECTION_NAME
        )
        print(f"[rag_pipeline] Collection '{config.COLLECTION_NAME}' ready")
        
        # Try to load existing vectorizer
        self._load_vectorizer()

    def _load_vectorizer(self):
        """Load the fitted vectorizer from disk if it exists"""
        try:
            if os.path.exists(self.vectorizer_path):
                with open(self.vectorizer_path, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                    self.is_fitted = True
                    print("[rag_pipeline] Loaded fitted vectorizer from disk")
            else:
                print("[rag_pipeline] No fitted vectorizer found on disk")
        except Exception as e:
            print(f"[rag_pipeline] Error loading vectorizer: {e}")

    def _save_vectorizer(self):
        """Save the fitted vectorizer to disk"""
        try:
            with open(self.vectorizer_path, 'wb') as f:
                pickle.dump(self.vectorizer, f)
                print("[rag_pipeline] Saved fitted vectorizer to disk")
        except Exception as e:
            print(f"[rag_pipeline] Error saving vectorizer: {e}")

    def read_file(self, filepath: str) -> str:
        print(f"[rag_pipeline] Reading file: {filepath}")
        if filepath.lower().endswith(".pdf"):
            reader = PdfReader(filepath)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
            print(f"[rag_pipeline] PDF read: {len(text)} characters")
            return text
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            print(f"[rag_pipeline] Text file read: {len(content)} characters")
            return content

    def simple_text_splitter(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list:
        """Simple text splitter that doesn't need any external libraries"""
        # Split by paragraphs first
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                # Start new chunk with overlap
                if len(current_chunk) > overlap:
                    current_chunk = current_chunk[-overlap:] + para + "\n\n"
                else:
                    current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # If no chunks were created (single paragraph), split by sentences
        if not chunks:
            # Split by sentences using simple regex
            sentences = re.split(r'(?<=[.!?])\s+', text)
            current_chunk = ""
            for sent in sentences:
                if len(current_chunk) + len(sent) <= chunk_size:
                    current_chunk += sent + " "
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sent + " "
            if current_chunk:
                chunks.append(current_chunk.strip())
        
        print(f"[rag_pipeline] Split text into {len(chunks)} chunks")
        return chunks

    def build_knowledge_base(self, data_dir=None, force_rebuild=False):
        print("[rag_pipeline] ===== STARTING KNOWLEDGE BASE BUILD ===== ")
        
        if data_dir is None:
            data_dir = config.DATA_DIR
        
        print(f"[rag_pipeline] Data directory: {data_dir}")
        
        existing_count = self.collection.count()
        print(f"[rag_pipeline] Existing chunks in DB: {existing_count}")
        
        if existing_count > 0 and not force_rebuild and self.is_fitted:
            print("[rag_pipeline] Skipping rebuild - already has data and fitted vectorizer")
            return
        
        if force_rebuild and existing_count > 0:
            print("[rag_pipeline] Forcing rebuild - deleting old collection")
            try:
                self.chroma_client.delete_collection(config.COLLECTION_NAME)
            except:
                pass
            self.collection = self.chroma_client.get_or_create_collection(
                name=config.COLLECTION_NAME
            )
            # Also delete the saved vectorizer
            try:
                if os.path.exists(self.vectorizer_path):
                    os.remove(self.vectorizer_path)
                    print("[rag_pipeline] Removed old vectorizer file")
            except:
                pass
        
        supported_extensions = (".txt", ".md", ".pdf")
        files = [f for f in os.listdir(data_dir) if f.lower().endswith(supported_extensions)]
        print(f"[rag_pipeline] Found files: {files}")
        
        if not files:
            print(f"[rag_pipeline] WARNING: No supported files found in '{data_dir}'")
            return
        
        print(f"[rag_pipeline] Found {len(files)} document(s). Building knowledge base...")
        
        all_chunks = []
        all_metadata = []
        
        for filename in files:
            filepath = os.path.join(data_dir, filename)
            print(f"[rag_pipeline] Processing {filename} ...")
            content = self.read_file(filepath)
            
            chunks = self.simple_text_splitter(content, config.CHUNK_SIZE, config.CHUNK_OVERLAP)
            
            for idx, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                all_chunks.append(chunk)
                all_metadata.append({"source": filename, "chunk_index": idx})
        
        print(f"[rag_pipeline] Total chunks to store: {len(all_chunks)}")
        
        if not all_chunks:
            print("[rag_pipeline] WARNING: No chunks created!")
            return
        
        # Fit TF-IDF on all chunks
        print("[rag_pipeline] Creating TF-IDF embeddings...")
        try:
            self.vectorizer.fit(all_chunks)
            self.is_fitted = True
            # Save the fitted vectorizer
            self._save_vectorizer()
            embeddings = self.vectorizer.transform(all_chunks)
        except Exception as e:
            print(f"[rag_pipeline] Error creating embeddings: {e}")
            return
        
        # Store each chunk with its embedding
        for idx, (chunk, metadata) in enumerate(zip(all_chunks, all_metadata)):
            chunk_id = f"chunk_{idx}"
            embedding = embeddings[idx].toarray()[0].tolist()
            
            self.collection.add(
                ids=[chunk_id],
                embeddings=[embedding],
                metadatas=[metadata],
                documents=[chunk]
            )
            if idx % 10 == 0:
                print(f"[rag_pipeline] Stored chunk {idx+1}/{len(all_chunks)}")
        
        final_count = self.collection.count()
        print(f"[rag_pipeline] ===== DONE! Knowledge base has {final_count} searchable chunks ===== ")

    def retrieve_context(self, query: str, top_k: int = None) -> list:
        if top_k is None:
            top_k = config.TOP_K_RESULTS
        
        # Check if vectorizer is fitted
        if not self.is_fitted:
            print("[rag_pipeline] WARNING: Vectorizer is not fitted! Trying to load or rebuild...")
            # Try to load from disk
            self._load_vectorizer()
            if not self.is_fitted:
                print("[rag_pipeline] ERROR: Vectorizer not fitted. Please rebuild the knowledge base.")
                return []
        
        if self.collection.count() == 0:
            print("[rag_pipeline] WARNING: Collection is empty!")
            return []
        
        print(f"[rag_pipeline] Retrieving context for query: {query[:50]}...")
        
        # Get all chunks from the database
        all_data = self.collection.get()
        if not all_data or not all_data.get('documents'):
            return []
        
        chunks = all_data['documents']
        metadatas = all_data['metadatas']
        
        # Get all chunk embeddings
        chunk_embeddings = self.collection.get(include=['embeddings'])
        
        if chunk_embeddings is None:
            print("[rag_pipeline] No embeddings found!")
            return []
        
        embeddings_list = chunk_embeddings.get('embeddings')
        if embeddings_list is None or len(embeddings_list) == 0:
            print("[rag_pipeline] No embeddings found!")
            return []
        
        # Create query embedding using the same vectorizer
        try:
            query_embedding = self.vectorizer.transform([query])
        except Exception as e:
            print(f"[rag_pipeline] Error creating query embedding: {e}")
            return []
        
        # Calculate similarities
        similarities = []
        for emb in embeddings_list:
            try:
                chunk_emb = np.array(emb).reshape(1, -1)
                query_emb = query_embedding.toarray()
                sim = cosine_similarity(query_emb, chunk_emb)[0][0]
                similarities.append(sim)
            except Exception as e:
                similarities.append(0.0)
        
        # Get top K results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        retrieved_items = []
        for idx in top_indices:
            retrieved_items.append({
                "text": chunks[idx],
                "source": metadatas[idx]["source"],
                "score": float(similarities[idx])
            })
        
        print(f"[rag_pipeline] Retrieved {len(retrieved_items)} chunks")
        return retrieved_items