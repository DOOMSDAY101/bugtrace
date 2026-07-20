from langchain_openai import OpenAIEmbeddings
import os

from bugtrace.rag.embeddings.base import BaseEmbedder
from dotenv import load_dotenv
load_dotenv()

class OpenAIEmbedder(BaseEmbedder):
    def __init__(self):
        try:
            self.embedder = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=os.getenv("OPENAI_API_KEY"),
            )

            # determine dimension once
            self._dimension = len(
                self.embed_query("test")
            )

        except Exception as e:
            raise RuntimeError(
                "Failed to initialize OpenAI embeddings.\n"
                "Make sure:\n"
                "  1. OPENAI_API_KEY is set in your environment (.env or system env)\n"
                "  2. You have access to the embedding model\n"
                "  3. Your internet connection is working\n\n"
                f"Error: {e}"
            )
    def embed_texts(self, texts):
        return self.embedder.embed_documents(texts)
    
    def embed_documents(self, texts):
        return self.embedder.embed_documents(texts)

    def embed_query(self, text):
        return self.embedder.embed_query(text)

    def get_dimension(self):
        return self._dimension