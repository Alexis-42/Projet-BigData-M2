from pydantic import BaseModel
from typing import Optional

class Repo(BaseModel):
    id: str  
    name: str
    description: Optional[str] = None
    readme: str

class RagParams(BaseModel):
    docCount: int
    similarityThreshold: float

class ProjectInfo(BaseModel):
    name: str
    description: str
    technologies: str