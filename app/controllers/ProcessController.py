from .BaseController import BaseController
from .ProjectController import ProjectController
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.models.enums import ProcessingEnums
import os
from langchain_community.document_loaders import TextLoader, PyMuPDFLoader, UnstructuredWordDocumentLoader
from typing import Optional



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
        return loader.load()

    def process_file_content(self, file_id: str, file_content: list,
                             chunk_size: int=100, overlap_size: int=20):

        text_spliter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            overlap_size=overlap_size,
            length_function = len,
        )

        file_content_text = [
            rec.page_content
            for rec in file_content
        ]

        file_content_metadata = [
            rec.page_content
            for rec in file_content
        ]

        chunks = text_spliter.create_documents(
            file_content_text,
            metadatas=file_content_metadata
        )

        return chunks

