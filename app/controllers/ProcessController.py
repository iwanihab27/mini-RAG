from .BaseController import BaseController
from .ProjectController import ProjectController
from app.models.enums import ProcessingEnums
import os
from langchain_community.document_loaders import TextLoader, PyMuPDFLoader, UnstructuredWordDocumentLoader
from typing import Optional
from typing import List
from dataclasses import dataclass


@dataclass
class Document:
    page_content: str
    metadata: dict

class ProcessController(BaseController):

    def __init__(self, project_id: str):
        super().__init__()

        self.project_id = project_id
        self.project_path = ProjectController().get_project_path(project_id=project_id)

    def get_file_extension(self, file_id: str):
        ext = os.path.splitext(file_id)[-1]
        if not ext:
            raise ValueError(f"Cannot determine file extension for file_id: {file_id}")
        return ext.lower()

    def get_file_loader(self, file_id: str, file_path: str):

        file_ext = self.get_file_extension(file_id=file_id).strip().lower()

        if file_path is None:
            file_path = os.path.join(
                self.project_path,
                file_id
            )

        if not os.path.exists(file_path):
            return None

        if file_ext == ProcessingEnums.TXT.value:
            return TextLoader(file_path, encoding="utf-8")

        elif file_ext == ProcessingEnums.PDF.value:
            return PyMuPDFLoader(file_path)

        elif file_ext in [".doc", ".docx"]:
            return UnstructuredWordDocumentLoader(file_path)

        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

    def get_file_content(self, file_id: str):

        loader = self.get_file_loader(file_id=file_id, file_path=None)
        if loader:
            return loader.load()

        return None

    def process_file_content(self, file_id: str, file_content: list,
                             chunk_size: int=100, overlap_size: int=20):

        file_content_text = [
            rec.page_content
            for rec in file_content
        ]

        file_content_metadata = [
            rec.metadata
            for rec in file_content
        ]

        chunks = self.process_simpler_splitter(
            texts=file_content_text,
            metadatas=file_content_metadata,
            chunk_size=chunk_size,
        )

        return chunks

    def process_simpler_splitter(self, texts: List[str], metadatas: List[dict], chunk_size: int, splitter_tag: str="\n"):

        full_text = " ".join(texts)

        lines = [ doc.strip() for doc in full_text.split(splitter_tag) if len(doc.strip()) > 1 ]

        chunks = []
        current_chunks = ""

        for line in lines:
            current_chunks += line + splitter_tag
            if len(current_chunks) >= chunk_size:
                chunks.append(Document(
                    page_content=current_chunks.strip(),
                    metadata={}
                ))

                current_chunks = ""

        if len(current_chunks) >= 0:
            chunks.append(Document(
                page_content=current_chunks.strip(),
                metadata={}
            ))

        return chunks
