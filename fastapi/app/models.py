from pydantic import BaseModel
from typing import Optional

class Repo(BaseModel):
    name: str
    full_name: str
    html_url: str
    description: Optional[str] = None
    readme: str