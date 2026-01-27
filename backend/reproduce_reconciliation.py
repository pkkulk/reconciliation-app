
import pandas as pd
from backend.services import reconcile_files, process_statement, process_settlement
from io import BytesIO

def create_mock_statement():
    # Columns expected: 
    # Index 0: ColA
    # Index 1: Type (ColB)
    # Index 3: Description (ColD) - containing PartnerPin
    # Index 11: SettleAmt (ColL)
    
    # We returned df.iloc[1:] in process_statement, so we need to simulate that structure.
    # Actually process_statement reads bytes. We need to create an Excel file in bytes.
    
    data = [
        # Row 0-8: Junk
        ["Junk"] * 12, ["Junk"] * 12, ["Junk"] * 12, ["Junk"] * 12, ["Junk"] * 12,
        ["Junk"] * 12, ["Junk"] * 12, ["Junk"] * 12, ["Junk"] * 12, 
        # Row 9: Header
        ["ColA", "Type", "ColC", "Description", "ColE", "ColF", "ColG", "ColH", "ColI", "ColJ", "ColK", "SettleAmt"],
        # Row 10: Junk Data Row (skipped)
        ["JunkData"] * 12,
        
        # Row 11+: Real Data
        # 1. Normal Match
        ["A", "Normal", "C", "Desc: XXP12345678", "E", "F", "G", "H", "I", "J", "K", 100.0],
        
        # 2. Cancel Match (Negative SettleAmt)
        # PartnerPin: 77712345679. Type: Cancel. SettleAmt: -200.0
        ["A", "Cancel", "C", "Desc: XXP12345679", "E", "F", "G", "H", "I", "J", "K", -200.0],
        
        # 3. Duplicate Pin - "Cancel" (Should Reconcile)
        ["A", "Cancel", "C", "Desc: XXP12345680", "E", "F", "G", "H", "I", "J", "K", -50.0],

        # 4. Duplicate Pin - "Dollar Received" (Should Not Reconcile)
        ["A", "Dollar Received", "C", "Desc: XXP12345680", "E", "F", "G", "H", "I", "J", "K", 50.0],
    ]
    
    df = pd.DataFrame(data)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, header=False)
    return output.getvalue()

def create_mock_settlement():
    # Columns expected:
    # Row 0-1: Junk
    # Row 2: Header
    # Col 3: PartnerPin (ColD)
    # Col 5: Type (ColF)
    # Col 10: PayoutRoundAmt (ColK)
    # Col 12: APIRate (ColM)
    
    data = [
        # Row 0-1 Junk
        ["Junk"] * 13, ["Junk"] * 13,
        # Row 2 Header
        ["ColA", "ColB", "ColC", "PartnerPin", "ColE", "Type", "ColG", "ColH", "ColI", "ColJ", "PayoutRoundAmt", "ColL", "APIRate"],
        
        # Data
        # 1. Normal Match
        # PartnerPin: 77712345678
        ["", "", "", "77712345678", "", "Normal", "", "", "", "", 200.0, "", 2.0], # Est = 100.0
        
        # 2. "Post-Cancel" (Positive) - Should NOT match Statement Cancel (because sign mismatch)
        # PartnerPin: 77712345679
        ["", "", "", "77712345679", "", "Post-Cancel", "", "", "", "", 400.0, "", 2.0], # Est = 200.0
        
        # 3. "Canceled" (Negative) - Should MATCH Statement Cancel
        # PartnerPin: 77712345679
        ["", "", "", "77712345679", "", "Canceled", "", "", "", "", -400.0, "", 2.0], # Est = -200.0
        
        # 4. Summary Row (Should be filtered out)
        # No Pin, High Amount
        ["", "", "", None, "", "Total", "", "", "", "", 70000.0, "", 1.0],

        # 5. Duplicate Pin (Should Reconcile with the Cancel one)
        # PartnerPin: 77712345680
        ["", "", "", "77712345680", "", "Canceled", "", "", "", "", -100.0, "", 2.0], # Est = -50.0
    ]
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, header=False)
    return output.getvalue()

def test_reconciliation():
    st_bytes = create_mock_statement()
    se_bytes = create_mock_settlement()
    
    print("\nRunning Reconciliation with Updated Logic...")
    result = reconcile_files(st_bytes, se_bytes)
    
    # Validation
    
    print("\n--- Reconciliation Result ---")
    import json
    print(json.dumps(result, indent=2))
    
    in_both = result['PresentInBoth']
    only_se = result['OnlyInSettlement']
    only_st = result['OnlyInStatement']
    
    # Check 1: Normal Match
    match_normal = [x for x in in_both if x['PartnerPin'] == '77712345678']
    assert len(match_normal) == 1, "Normal transaction failed to match"
    
    # Check 2: Cancel Match (Negative to Negative)
    # Should match 77712345679 (Statement Cancel) to 77712345679 (Settlement Canceled -400)
    match_cancel = [x for x in in_both if x['PartnerPin'] == '77712345679']
    assert len(match_cancel) == 1, "Cancel transaction failed to match negative-to-negative"
    assert match_cancel[0]['EstimatedUSD'] == -200.0, "Matched with wrong Settlement record (should be negative)"
    
    # Check 3: Post-Cancel (Positive) should be Unmatched (OnlyInSettlement)
    # AND should be in Variance list now (Round 2 requirement)
    post_cancel = [x for x in only_se if x['PartnerPin'] == '77712345679' and x['PayoutRoundAmt'] == 400.0]
    assert len(post_cancel) == 1, "Positive Post-Cancel should stay in OnlyInSettlement (no match for it)"
    
    # Check 4: Summary Row Elimination
    # Should not exist in any list (Total 70000)
    summary_check = [x for x in only_se if x['PayoutRoundAmt'] == 70000.0]
    assert len(summary_check) == 0, "Summary row was not filtered out!"
    
    # Check 5: Duplicate Tagging
    match_dup = [x for x in in_both if x['PartnerPin'] == '77712345680']
    assert len(match_dup) == 1, "Duplicate logic failed: 'Cancel' type should have matched"

    # Check 6: Variance Population (Round 2)
    # Variance list should contain the Unmatched "Post-Cancel" item
    var_list = result['Variance']
    var_post_cancel = [x for x in var_list if x['PartnerPin'] == '77712345679' and x['PayoutRoundAmt'] == 400.0]
    assert len(var_post_cancel) == 1, "OnlyInSettlement items should be duplicated into Variance list"

    
    print("\n✅ Verification Successful: All logic checks passed.")

if __name__ == "__main__":
    test_reconciliation()
