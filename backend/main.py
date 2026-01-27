from fastapi import FastAPI,UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd 
from services import reconcile_files

app=FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/reconcile")
async def reconcile(statement:UploadFile=File(...),settlement:UploadFile=File(...)):
    statement_df=pd.read_csv(statement.file)
    settlement_df=pd.read_csv(settlement.file)
    result=reconcile_files(statement_df,settlement_df)
    return result



