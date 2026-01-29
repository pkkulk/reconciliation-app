from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
try:
    from .services import reconcile_files
except ImportError:
    from services import reconcile_files
import uvicorn
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "Reconciliation Backend is Live", "documentation": "/docs"}

@app.post("/reconcile")
async def reconcile_endpoint(
    statement_file: UploadFile = File(...), 
    settlement_file: UploadFile = File(...)
):
    try:
        st_content = await statement_file.read()
        se_content = await settlement_file.read()
        results = reconcile_files(st_content, se_content)
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
