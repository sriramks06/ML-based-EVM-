import os
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ml_evm.db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"

    project_id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, index=True)
    BAC = Column(Float, nullable=False)
    planned_duration = Column(Integer, nullable=False)
    risk_profile = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    weekly_data = relationship("ProjectWeeklyData", back_populates="project", cascade="all, delete-orphan")


class ProjectWeeklyData(Base):
    __tablename__ = "project_weekly_data"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    week = Column(Integer, nullable=False)
    
    PV = Column(Float, nullable=False)
    EV = Column(Float, nullable=False)
    AC = Column(Float, nullable=False)
    CPI = Column(Float, nullable=False)
    SPI = Column(Float, nullable=False)
    EAC = Column(Float, nullable=False)
    
    Requirement_Volatility = Column(Float, nullable=False)
    Change_Requests = Column(Integer, nullable=False)
    Scope_Change_Percentage = Column(Float, nullable=False)
    Task_Completion_Rate = Column(Float, nullable=False)
    Resource_Utilization = Column(Float, nullable=False)
    Team_Experience = Column(Float, nullable=False)
    Task_Complexity = Column(Float, nullable=False)
    Defect_Rate = Column(Float, nullable=False)
    Rework_Rate = Column(Float, nullable=False)
    Dependency_Delays = Column(Integer, nullable=False)
    Delay_Severity = Column(Float, nullable=False)
    Project_Completion_Percentage = Column(Float, nullable=False)
    
    Final_Cost = Column(Float, nullable=False)
    Final_Duration = Column(Integer, nullable=False)

    project = relationship("Project", back_populates="weekly_data")
    
    @property
    def TCPI(self):
        # (BAC - EV) / (BAC - AC)
        if self.project and self.project.BAC:
            bac = self.project.BAC
            if (bac - self.AC) == 0:
                return float('inf')
            return (bac - self.EV) / (bac - self.AC)
        return 1.0
    
    __table_args__ = (
        UniqueConstraint('project_id', 'week', name='uix_project_week'),
    )


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    week = Column(Integer, nullable=False)
    
    predicted_final_cost = Column(Float, nullable=False)
    predicted_final_duration = Column(Float, nullable=False)
    cost_model = Column(String, nullable=False)
    schedule_model = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    week = Column(Integer, nullable=False)
    
    cost_risk = Column(String, nullable=False)
    schedule_risk = Column(String, nullable=False)
    overall_risk = Column(String, nullable=False)
    cost_overrun_percentage = Column(Float, nullable=False)
    schedule_overrun_percentage = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    week = Column(Integer, nullable=False)
    
    risk_factor = Column(String, nullable=False)
    recommendation = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
