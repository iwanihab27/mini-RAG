from enum import Enum

class ResponseEnum(Enum):

    FILE_TYPE_NOT_SUPPORTED = "file_not_supported"
    FILE_SIZE_TOO_LARGE = "file_too_large"
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILED = "file_upload_failed"
    PROCESSING_FAILED = "processing_failed"
    PROCESSING_SUCCESS = "processing_success"
    NO_FILES_ERROR = "not_found_files"
    FILE_ID_ERROR = "file_id_error"
    PROJECT_NOT_FOUND = "project_not_found"
    INSERT_INTO_VECTOR_DB_ERROR = "insert_into_vector_db_error"
    INSERT_INTO_VECTOR_DB_SUCCESS = "insert_into_vector_db_success"
    VECTORDB_COLLECTION_RETRIEVED = "VECTORDB_COLLECTION_RETRIEVED"
    VECTORDB_SEARCH_ERROR = "VECTORDB_SEARCH_ERROR"
    VECTORDB_SEARCH_SUCCESS = "VECTORDB_SEARCH_SUCCESS"