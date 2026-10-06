from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from src.database import get_db, Project, ProjectWeeklyData
from src.schemas import ProjectResponse, ProjectWeekResponse

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("", response_model=List[ProjectResponse])
def get_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    projects = db.query(Project).offset(skip).limit(limit).all()
    return projects

@router.get("/{project_id}/weeks", response_model=List[ProjectWeekResponse])
def get_project_weeks(project_id: int, db: Session = Depends(get_db)):
    # Verify project exists
    project = db.query(Project).filter(Project.project_id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} was not found.")
        
    weeks = db.query(ProjectWeeklyData).filter(ProjectWeeklyData.project_id == project_id).order_by(ProjectWeeklyData.week).all()
    return weeks
