# ML-Enhanced EVM Project

This project extends traditional Earned Value Management (EVM) with Machine Learning for project cost and schedule forecasting.

## Architecture

1. **Synthetic Data Generator** (`src/generate_data.py`): Generates project-week condition data.
2. **EVM Calculation Module** (`src/evm.py`): Processes PV, EV, AC, CPI, SPI, and EAC.
3. **Feature Engineering** (`src/features.py`): Prepares a clean ML-ready dataset, safely handling values and target leakage.
4. **Database Layer** (`src/database.py`, `src/load_database.py`): PostgreSQL persistent data layer.
   - Flow: CSV -> Preprocessing -> PostgreSQL -> Future ML training
5. **Machine Learning** (`src/train_models.py`): Predicts final cost and duration using isolated CV structures.
6. **Risk & Explainability** (`src/risk.py`, `src/predict.py`): Forecasts overrun boundaries and identifies root causes.
7. **Recommendation Engine** (`src/recommendations.py`): Rule-based decision-support engine.
8. **FastAPI Backend** (`src/main.py`): RESTful API exposing intelligence to the frontend.

## Database Layer

The persistent application data is stored in PostgreSQL (or SQLite for local testing), while the generated CSV files are kept as reproducible artifacts.

### Configuration

Create a `.env` file (see `.env.example`) containing your connection string. Do not commit credentials.
```
DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/ml_evm
```
*(For local testing/demonstration, `sqlite:///ml_evm.db` can be used)*

### Commands

**Initialize Database (Create tables):**
```bash
python src/init_db.py
```

**Load Data into Database:**
```bash
python src/load_database.py
```

## FastAPI Backend

The REST API exposes the project intelligence layers (EVM, ML, Risk, and Recommendations).

### Running the API Server

```bash
uvicorn src.main:app --reload
```

The server will start at `http://127.0.0.1:8000`.
You can view the interactive Swagger documentation at `http://127.0.0.1:8000/docs`.

### Core API Endpoints

- `GET /projects` - List all projects.
- `GET /projects/{id}/weeks` - List all weekly observations for a project.
- `POST /evm` - Calculate traditional EVM metrics.
- `POST /analyze` - Orchestrates the entire pipeline (Current Data -> EVM -> ML -> Risk -> Explainability -> Recommendations) and saves the results to the database.

**Example Request to `/analyze`:**
```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{"project_id": 1, "week": 10}'
```
