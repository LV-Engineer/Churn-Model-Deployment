from pydantic import BaseModel

class UploadResponse(BaseModel):
    rows_added: int
    rows_skipped: int


class DeleteResponse(BaseModel):
    rows_deleted: int