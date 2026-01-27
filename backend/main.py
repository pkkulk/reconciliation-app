from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from .services import reconcile_files
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for simplicity in dev, user can restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/reconcile")
async def reconcile(statement: UploadFile = File(...), settlement: UploadFile = File(...)):
    statement_bytes = await statement.read()
    settlement_bytes = await settlement.read()
    
    try:
        result = reconcile_files(statement_bytes, settlement_bytes)
        return result
    except Exception as e:
        return {"error": str(e)}
