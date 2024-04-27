from pydantic import BaseModel, Field


class Point(BaseModel):
    id: int = Field(default=0, description="ID of the point.")
    text: str = Field(default="", description="Content of the point.")
    file_path: str = Field(default="", description="The file that the points come from.")
    start_line: int = Field(default=0, description="The starting line number that the point refers to.")
    end_line: int = Field(default=0, description="The ending line number that the point refers to.")
    detail: str = Field(default="", description="File content from start_line to end_line.")
