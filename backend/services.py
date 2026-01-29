import pandas as pd
import numpy as np
from io import BytesIO
try:
    from .utils import extract_partner_pin
except ImportError:
    from utils import extract_partner_pin
def process_statement(file_content: bytes) -> pd.DataFrame:
    try:
        df = pd.read_excel(BytesIO(file_content), header=9)
    except Exception as e:
        raise ValueError(f"Error reading Statement file: {e}")
    if not df.empty:
        df = df.iloc[1:].reset_index(drop=True)
    if df.shape[1] < 12:
        raise ValueError("Statement file does not have enough columns")
    def get_pin(row):
        val = row.iloc[3] 
        return extract_partner_pin(val)
    df['PartnerPin'] = df.apply(get_pin, axis=1)
    duplicates_mask = df.duplicated(subset=['PartnerPin'], keep=False) & df['PartnerPin'].notna()
    def tag_row(row, is_dup):
        row_type = str(row.iloc[1]) 
        if is_dup:
            if "Cancel" in row_type:
                return "Should Reconcile"
            if "Dollar Received" in row_type:
                return "Should Not Reconcile"
            return "Should Not Reconcile" 
        else:
            if pd.notna(row['PartnerPin']):
                 return "Should Reconcile"
            return "Ignore" 
    df['ReconTag'] = df.apply(lambda x: tag_row(x, duplicates_mask[x.name]), axis=1)
    df['SettleAmt'] = pd.to_numeric(df.iloc[:, 11], errors='coerce').fillna(0)
    return df
def process_settlement(file_content: bytes) -> pd.DataFrame:
    try:
        df = pd.read_excel(BytesIO(file_content), header=2)
    except Exception as e:
        raise ValueError(f"Error reading Settlement file: {e}")
    if df.shape[1] < 13:
        raise ValueError("Settlement file does not have enough columns")
    df['PartnerPin'] = df.iloc[:, 3].astype(str).str.strip()
    df['PartnerPin'] = df['PartnerPin'].replace({'nan': np.nan, '': np.nan})
    df = df.dropna(subset=['PartnerPin'])
    df['PartnerPin'] = df['PartnerPin'].str.replace(r'\.0$', '', regex=True)
    # Remove '777' prefix to match with Statement file's XXP-extracted 8-digit ID
    df['PartnerPin'] = df['PartnerPin'].str.replace(r'^777', '', regex=True)
    payout = pd.to_numeric(df.iloc[:, 10].astype(str).str.replace(",", ""), errors='coerce')
    rate = pd.to_numeric(df.iloc[:, 12].astype(str).str.replace(",", ""), errors='coerce')
    df['EstimatedUSD'] = payout / rate
    df['EstimatedUSD'] = df['EstimatedUSD'].fillna(0.0)
    duplicates_mask = df.duplicated(subset=['PartnerPin'], keep=False) & df['PartnerPin'].notna()
    def tag_row(row, is_dup):
        row_type = str(row.iloc[5])
        if is_dup:
            if "Cancel" in row_type:
                return "Should Reconcile"
            return "Should Not Reconcile"
        else:
             return "Should Reconcile"
    df['ReconTag'] = df.apply(lambda x: tag_row(x, duplicates_mask[x.name]), axis=1)
    return df
def reconcile_files(statement_bytes: bytes, settlement_bytes: bytes):
    st_df = process_statement(statement_bytes)
    se_df = process_settlement(settlement_bytes)
    st_reconcile = st_df[st_df['ReconTag'] == "Should Reconcile"].copy()
    se_reconcile = se_df[se_df['ReconTag'] == "Should Reconcile"].copy()
    def get_stmt_sign(row):
        t = str(row.iloc[1]) 
        val = str(row.iloc[1])
        if 'Cancel' in val:
            return -1
        return 1
    def get_settle_sign(row):
        val = row['EstimatedUSD']
        if val < 0:
             return -1
        return 1
    st_reconcile['MatchSign'] = st_reconcile.apply(get_stmt_sign, axis=1)
    se_reconcile['MatchSign'] = se_reconcile.apply(get_settle_sign, axis=1)
    merged = pd.merge(
        se_reconcile, 
        st_reconcile, 
        on=['PartnerPin', 'MatchSign'], 
        how='outer', 
        indicator=True,
        suffixes=('_se', '_st')
    )
    merged.drop(columns=['MatchSign'], inplace=True)
    results = {
        "PresentInBoth": [],
        "OnlyInSettlement": [],
        "OnlyInStatement": [],
        "Variance": []
    }
    in_both = merged[merged['_merge'] == 'both'].copy()
    in_both['VarianceVal'] = in_both['EstimatedUSD'] - in_both['SettleAmt']
    variance_threshold = 0.01
    matched_df = in_both[in_both['VarianceVal'].abs() <= variance_threshold].copy()
    variance_df = in_both[in_both['VarianceVal'].abs() > variance_threshold].copy()
    only_se_df = merged[merged['_merge'] == 'left_only'].copy()
    only_st_df = merged[merged['_merge'] == 'right_only'].copy()
    se_pins = set(only_se_df['PartnerPin'].dropna())
    st_pins = set(only_st_df['PartnerPin'].dropna())
    reversal_pins = se_pins.intersection(st_pins)
    reversal_mismatch_se = only_se_df[only_se_df['PartnerPin'].isin(reversal_pins)].copy()
    reversal_mismatch_st = only_st_df[only_st_df['PartnerPin'].isin(reversal_pins)].copy()
    reversal_mismatch_df = pd.concat([reversal_mismatch_se, reversal_mismatch_st], ignore_index=True)
    only_se_final = only_se_df[~only_se_df['PartnerPin'].isin(reversal_pins)].copy()
    only_st_final = only_st_df[~only_st_df['PartnerPin'].isin(reversal_pins)].copy()

    # Map Statement columns to standard columns for better visibility in Frontend
    # Statement 'Date' -> 'PostDate'
    if 'Date' in only_st_final.columns:
        only_st_final['PostDate'] = only_st_final['Date']
    # Statement 'PQsTrOptOons' (Description) -> 'Pin Number' (Show description context)
    if 'PQsTrOptOons' in only_st_final.columns:
        only_st_final['Pin Number'] = only_st_final['PQsTrOptOons']
    # Statement 'Settle.Amt' -> 'TransferAmt'
    if 'Settle.Amt' in only_st_final.columns:
        only_st_final['TransferAmt'] = only_st_final['Settle.Amt']
    def to_dict_records(df):
        return df.astype(object).where(pd.notnull(df), None).to_dict(orient='records')
    results = {
        "matched": to_dict_records(matched_df),
        "variance": to_dict_records(variance_df),
        "only_in_statement": to_dict_records(only_st_final),
        "only_in_settlement": to_dict_records(only_se_final),
        "reversal_mismatch": to_dict_records(reversal_mismatch_df),
        "summary": {
            "total_statement": len(st_df),
            "total_settlement": len(se_df),
            "matched": len(matched_df),
            "variance": len(variance_df),
            "only_in_statement": len(only_st_final),
            "only_in_settlement": len(only_se_final),
            "reversal_mismatch": len(reversal_mismatch_se),
             "reversal_mismatch_rows": len(reversal_mismatch_df)
        }
    }
    return results
