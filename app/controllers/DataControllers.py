from aiofiles import os
from .BaseController import BaseController
from fastapi import APIRouter, FastAPI, Depends, UploadFile
from app.models.enums import ResponseEnum
from .ProjectController import ProjectController
import re
import os


class DataController(BaseController):
    def __init__(self):
        super().__init__()
        self.size_scale = 1048576

    def ValidateUploadedFile(self, file: UploadFile):

        if file.content_type not in self.settings.FILE_ALLOWED_TYPES:
            print("file.content_type>>>>>", file.content_type)
            return False, ResponseEnum.FILE_TYPE_NOT_SUPPORTED.value

        if file.size > self.settings.FILE_MAX_SIZE:
            print("file.size>>>>>", file.size)
            return False, ResponseEnum.FILE_SIZE_TOO_LARGE.value

        else:
            return True, ResponseEnum.FILE_UPLOAD_SUCCESS.value


    def generate_uniqe_filepath(self, orig_filename: str, project_id: str):

        random_file_name = self.generate_random_string()
        project_path = ProjectController().get_project_path(project_id=project_id)

        cleaned_filename = self.get_clean_filename(
            orig_filename=orig_filename

        )

        new_file_path = os.path.join(
            project_path,
            random_file_name + "_" + cleaned_filename
        )

        while os.path.exists(new_file_path):
            random_file_name = self.generate_random_string()
            new_file_path = os.path.join(
                project_path,
                random_file_name + "_" + cleaned_filename
            )

        return new_file_path, random_file_name + "_" + cleaned_filename



    def get_clean_filename(self, orig_filename: str):

        cleaned_filename = re.sub(r'[^\w.]', '', orig_filename.strip())
        # clean from everything except _

        cleaned_filename = cleaned_filename.replace(' ', '_')
        # change space into underscore


        return cleaned_filename



