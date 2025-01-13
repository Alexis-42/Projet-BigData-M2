from fastapi import APIRouter, HTTPException, Depends
from typing import List
from dependencies import get_db_connection
from models import Repo

router = APIRouter()

items_db = []

@router.get("/repos/", response_model=List[Repo])
async def read_repos(db=Depends(get_db_connection)):
    repos = await db.repos.find().to_list(100)
    return repos

@router.get("/repos/{repo_id}", response_model=Repo)
async def read_repo(repo_id: str, db=Depends(get_db_connection)):
    repo = await db.repos.find_one({"_id": repo_id})
    if repo is None:
        raise HTTPException(status_code=404, detail="Repo not found")
    return repo