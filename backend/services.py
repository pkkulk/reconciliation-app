import pandas as pd
import numpy as np
from io import BytesIO
from .utils import extract_partner_pin

def process_statement(file_content: bytes) -> pd.DataFrame:
    # Read excel, assuming header is at row 10 (index 9) since rows 1-9 are deleted functionality
    # But user said "Delete rows 1 to 9". So row 10 is the header.
    try:
        df = pd.read_excel(BytesIO(file_content), header=9)
    except Exception as e:
        raise ValueError(f"Error reading Statement file: {e}")

    # User says "and 11". If row 10 is header (index 0 of df), then row 11 is index 0 of data.
    # We need to drop the first row of data.
    if not df.empty:
        df = df.iloc[1:].reset_index(drop=True)

    # Convert columns to likely indices if names overlap, but reliance on indices is safer per requirements
    # Col D is index 3
    # Col B is index 1
    # Col L is index 11
    
    # Ensure we have enough columns
    if df.shape[1] < 12:
        raise ValueError("Statement file does not have enough columns")

    # Rename for clarity (optional but good for debugging) or use by position
    # We will use position to be safe with "Col X" requirements
    
    
    def get_pin(row):
        val = row.iloc[3] # Col D
        return extract_partner_pin(val)

    df['PartnerPin'] = df.apply(get_pin, axis=1)
    
    # Tagging Logic
    # 1. Identify duplicates based on PartnerPin
    duplicates_mask = df.duplicated(subset=['PartnerPin'], keep=False) & df['PartnerPin'].notna()
    
    def tag_row(row, is_dup):
        # Col B is index 1 (Type)
        row_type = str(row.iloc[1]) 
        
        if is_dup:
            if "Cancel" in row_type:
                return "Should Reconcile"
            if "Dollar Received" in row_type:
                return "Should Not Reconcile"
            # Default for duplicates not matching above
            return "Should Not Reconcile" 
        else:
            # Non-duplicated
            if pd.notna(row['PartnerPin']):
                 return "Should Reconcile"
            return "Ignore" # No pin

    df['ReconTag'] = df.apply(lambda x: tag_row(x, duplicates_mask[x.name]), axis=1)
    
    # Settle Amt is Col L (index 11)
    # Clean it up to be numeric
    df['SettleAmt'] = pd.to_numeric(df.iloc[:, 11], errors='coerce').fillna(0)

    return df

def process_settlement(file_content: bytes) -> pd.DataFrame:
    # "Delete rows 1 and 2". Row 3 is header (index 2).
    try:
        df = pd.read_excel(BytesIO(file_content), header=2)
    except Exception as e:
        raise ValueError(f"Error reading Settlement file: {e}")

    # No extra rows to delete mentioned ("Delete 1 and 2" handled by header=2).
    
    # Col K (PayoutRoundAmt) -> Index 10
    # Col M (APIRate) -> Index 12
    # Col F (Type/Description?) -> Index 5 (User says "Cancel" type in Col F)
    # Col D (Partner Pin) -> Index 3

    if df.shape[1] < 13:
        raise ValueError("Settlement file does not have enough columns")

    # Cleaning: Drop rows that are clearly not transactions (e.g. Summary rows)
    # These usually don't have a valid PartnerPin or it is NaN
    # User said summary row has CollectAmt but no Pin. 
    # Index 3 is Partner Pin.
    # Handle potential float conversion (.0 suffix)
    # Filter out empty strings, whitespace, or nan
    df['PartnerPin'] = df.iloc[:, 3].astype(str).str.strip()
    df['PartnerPin'] = df['PartnerPin'].replace({'nan': np.nan, '': np.nan})
    df = df.dropna(subset=['PartnerPin'])
    df['PartnerPin'] = df['PartnerPin'].str.replace(r'\.0$', '', regex=True)

    # Calculate Estimated Amount
    # PayoutRoundAmt (Col K, idx 10) / APIRAte (Col M, idx 12)
    # Remove commas before conversion
    payout = pd.to_numeric(df.iloc[:, 10].astype(str).str.replace(",", ""), errors='coerce')
    rate = pd.to_numeric(df.iloc[:, 12].astype(str).str.replace(",", ""), errors='coerce')
    
    df['EstimatedUSD'] = payout / rate
    # Handle division by zero or NaN?
    df['EstimatedUSD'] = df['EstimatedUSD'].fillna(0.0)

    # Ensure SettleAmt (assuming Col L idx 11? No wait, SettleAmt in Settlement file?)
    # Wait, 'EstimatedUSD' is compared to 'SettleAmt' from Statement?
    # Or is 'SettleAmt' in Settlement?
    # User says: "OnlyInSettlement... CollectAmt 70,475".
    # In `reconcile_files`, Variance = EstimatedUSD - SettleAmt.
    # SettleAmt comes from Statement (df_st['SettleAmt']).
    # Wait, variance is between Estimated and SettleAmt. 
    # Estimated comes from Settlement. SettleAmt comes from Statement.
    # Confirm SettleAmt source.
    # In `process_statement`: `df['SettleAmt'] = pd.to_numeric(df.iloc[:, 11]...` -> Col L. Correct.

    
    # Tagging
    duplicates_mask = df.duplicated(subset=['PartnerPin'], keep=False) & df['PartnerPin'].notna()

    def tag_row(row, is_dup):
        # Col F is index 5
        row_type = str(row.iloc[5])
        
        if is_dup:
            if "Cancel" in row_type:
                return "Should Reconcile"
            # User doesn't explicitly say what to do with other duplicates.
            # Assuming "Should Not Reconcile" is safe default for collision/duplicates usually.
            return "Should Not Reconcile"
        else:
             return "Should Reconcile"

    df['ReconTag'] = df.apply(lambda x: tag_row(x, duplicates_mask[x.name]), axis=1)

    return df

def reconcile_files(statement_bytes: bytes, settlement_bytes: bytes):
    st_df = process_statement(statement_bytes)
    se_df = process_settlement(settlement_bytes)
    
    # Filter "Should Reconcile"
    st_reconcile = st_df[st_df['ReconTag'] == "Should Reconcile"].copy()
    se_reconcile = se_df[se_df['ReconTag'] == "Should Reconcile"].copy()
    
    # Match on PartnerPin AND Sign to avoid variance (Positive vs Negative)
    
    def get_stmt_sign(row):
        # Statement: Cancel is negative
        t = str(row.iloc[1]) # Type is Col B / index 1. Or use 'Type' if we renamed? 
        # In process_statement we didn't rename columns nicely to names, just used indices mostly or created vars.
        # But wait, did we create 'Type' column? No, we used indices.
        # However, earlier code used `row.iloc[1]`.
        # Let's verify we can access it safely.
        # process_statement returns df. We didn't rename cols.
        # col 1 is Type.
        val = str(row.iloc[1])
        if 'Cancel' in val:
            return -1
        return 1
        
    def get_settle_sign(row):
        # Settlement: Negative amounts (e.g. Canceled status)
        # We calculated EstimatedUSD. If it's negative, sign is -1.
        val = row['EstimatedUSD']
        if val < 0:
             return -1
        return 1

    st_reconcile['MatchSign'] = st_reconcile.apply(get_stmt_sign, axis=1)
    se_reconcile['MatchSign'] = se_reconcile.apply(get_settle_sign, axis=1)

    # Outer join to capture all
    merged = pd.merge(
        se_reconcile, 
        st_reconcile, 
        on=['PartnerPin', 'MatchSign'], 
        how='outer', 
        indicator=True,
        suffixes=('_se', '_st')
    )
    
    # Drop helper
    merged.drop(columns=['MatchSign'], inplace=True)
    
    # Labeling
    # "Present in Both" -> both
    # "Present in Settlement but not in Statement" -> left_only (since SE is left)
    # "Not Present in Settlement but Present in Statement" -> right_only
    
    results = {
        "PresentInBoth": [],
        "OnlyInSettlement": [],
        "OnlyInStatement": [],
        "Variance": []
    }
    
    def to_dict_records(df):
        # Convert timestamps to str for JSON serialization if needed
        return df.astype(object).where(pd.notnull(df), None).to_dict(orient='records')

    # Present in Both
    in_both = merged[merged['_merge'] == 'both'].copy()
    
    # Variance Check for In Both
    in_both['VarianceVal'] = in_both['EstimatedUSD'] - in_both['SettleAmt']
    
    results["PresentInBoth"] = to_dict_records(in_both)
    
    variance_threshold = 0.01
    variance_df = in_both[in_both['VarianceVal'].abs() > variance_threshold]
    results["Variance"] = to_dict_records(variance_df)

    # Only in Settlement
    only_se = merged[merged['_merge'] == 'left_only'].copy()
    results["OnlyInSettlement"] = to_dict_records(only_se)
    
    # Only in Statement
    only_st = merged[merged['_merge'] == 'right_only'].copy()
    results["OnlyInStatement"] = to_dict_records(only_st)

    # Variance Logic Update:
    # "Variance will be the transactions that are not present in the Transaction Report but are present in the Partner Settlement File"
    # So Variance = (InBoth with diffs) + (OnlyInSettlement)
    
    # We already have variance_df from InBoth
    # Add OnlyInSettlement to Variance list
    variance_list = results["Variance"] 
    variance_list.extend(results["OnlyInSettlement"])
    results["Variance"] = variance_list
    
    return results
