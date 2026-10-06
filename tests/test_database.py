import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import Base, Project, ProjectWeeklyData

# Safe in-memory SQLite database for testing, so we don't drop actual data
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="module")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def session(test_engine):
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()
    # clean tables between tests
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(table.delete())
    session.commit()

def test_project_insertion(session):
    project = Project(
        project_id=1,
        project_name="Test Project",
        BAC=100000.0,
        planned_duration=25,
        risk_profile="Stable"
    )
    session.add(project)
    session.commit()
    
    retrieved = session.query(Project).filter(Project.project_id == 1).first()
    assert retrieved is not None
    assert retrieved.project_name == "Test Project"
    assert retrieved.BAC == 100000.0

def test_weekly_data_insertion_with_foreign_key(session):
    # Setup project
    project = Project(project_id=1, project_name="P1", BAC=100.0, planned_duration=10)
    session.add(project)
    session.commit()
    
    # Insert weekly data
    weekly = ProjectWeeklyData(
        project_id=1,
        week=1,
        PV=10.0, EV=9.0, AC=11.0, CPI=0.81, SPI=0.9, EAC=120.0,
        Requirement_Volatility=0.01, Change_Requests=0, Scope_Change_Percentage=0.0,
        Task_Completion_Rate=0.1, Resource_Utilization=1.0, Team_Experience=5.0,
        Task_Complexity=5.0, Defect_Rate=0.01, Rework_Rate=0.01, Dependency_Delays=0,
        Delay_Severity=0.0, Project_Completion_Percentage=0.1,
        Final_Cost=120.0, Final_Duration=12
    )
    session.add(weekly)
    session.commit()
    
    retrieved = session.query(ProjectWeeklyData).filter_by(project_id=1, week=1).first()
    assert retrieved is not None
    assert retrieved.PV == 10.0

def test_unique_project_week_constraint(session):
    # Setup project
    project = Project(project_id=1, project_name="P1", BAC=100.0, planned_duration=10)
    session.add(project)
    session.commit()
    
    # Create weekly data template helper
    def create_weekly(week):
        return ProjectWeeklyData(
            project_id=1, week=week,
            PV=10.0, EV=9.0, AC=11.0, CPI=0.81, SPI=0.9, EAC=120.0,
            Requirement_Volatility=0.01, Change_Requests=0, Scope_Change_Percentage=0.0,
            Task_Completion_Rate=0.1, Resource_Utilization=1.0, Team_Experience=5.0,
            Task_Complexity=5.0, Defect_Rate=0.01, Rework_Rate=0.01, Dependency_Delays=0,
            Delay_Severity=0.0, Project_Completion_Percentage=0.1,
            Final_Cost=120.0, Final_Duration=12
        )
    
    # Insert first
    w1 = create_weekly(1)
    session.add(w1)
    session.commit()
    
    # Try inserting duplicate week
    w2 = create_weekly(1)
    session.add(w2)
    with pytest.raises(IntegrityError):
        session.commit()
