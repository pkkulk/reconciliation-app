import pandas as pd
from backend.services import reconcile_files, process_statement, process_settlement
from io import BytesIO
def create_mock_statement():
    data = [
        ["Junk"] * 12, ["Junk"] * 12, ["Junk"] * 12, ["Junk"] * 12, ["Junk"] * 12,
        ["Junk"] * 12, ["Junk"] * 12, ["Junk"] * 12, ["Junk"] * 12, 
        ["ColA", "Type", "ColC", "Description", "ColE", "ColF", "ColG", "ColH", "ColI", "ColJ", "ColK", "SettleAmt"],
        ["JunkData"] * 12,
        ["A", "Normal", "C", "Desc: XXP12345678", "E", "F", "G", "H", "I", "J", "K", 100.0],
        ["A", "Cancel", "C", "Desc: XXP12345679", "E", "F", "G", "H", "I", "J", "K", -200.0],
        ["A", "Cancel", "C", "Desc: XXP12345680", "E", "F", "G", "H", "I", "J", "K", -50.0],
        ["A", "Dollar Received", "C", "Desc: XXP12345680", "E", "F", "G", "H", "I", "J", "K", 50.0],
    ]
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, header=False)
    return output.getvalue()
def create_mock_settlement():
    data = [
        ["Junk"] * 13, ["Junk"] * 13,
        ["ColA", "ColB", "ColC", "PartnerPin", "ColE", "Type", "ColG", "ColH", "ColI", "ColJ", "PayoutRoundAmt", "ColL", "APIRate"],
        ["", "", "", "77712345678", "", "Normal", "", "", "", "", 200.0, "", 2.0], 
        ["", "", "", "77712345679", "", "Post-Cancel", "", "", "", "", 400.0, "", 2.0], 
        ["", "", "", "77712345679", "", "Canceled", "", "", "", "", -400.0, "", 2.0], 
        ["", "", "", None, "", "Total", "", "", "", "", 70000.0, "", 1.0],
        ["", "", "", "77712345680", "", "Canceled", "", "", "", "", -100.0, "", 2.0], 
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
    print("\n--- Reconciliation Result ---")
    import json
    print(json.dumps(result, indent=2))
    in_both = result['PresentInBoth']
    only_se = result['OnlyInSettlement']
    only_st = result['OnlyInStatement']
    match_normal = [x for x in in_both if x['PartnerPin'] == '77712345678']
    assert len(match_normal) == 1, "Normal transaction failed to match"
    match_cancel = [x for x in in_both if x['PartnerPin'] == '77712345679']
    assert len(match_cancel) == 1, "Cancel transaction failed to match negative-to-negative"
    assert match_cancel[0]['EstimatedUSD'] == -200.0, "Matched with wrong Settlement record (should be negative)"
    post_cancel = [x for x in only_se if x['PartnerPin'] == '77712345679' and x['PayoutRoundAmt'] == 400.0]
    assert len(post_cancel) == 1, "Positive Post-Cancel should stay in OnlyInSettlement (no match for it)"
    summary_check = [x for x in only_se if x['PayoutRoundAmt'] == 70000.0]
    assert len(summary_check) == 0, "Summary row was not filtered out!"
    match_dup = [x for x in in_both if x['PartnerPin'] == '77712345680']
    assert len(match_dup) == 1, "Duplicate logic failed: 'Cancel' type should have matched"
    var_list = result['Variance']
    var_post_cancel = [x for x in var_list if x['PartnerPin'] == '77712345679' and x['PayoutRoundAmt'] == 400.0]
    assert len(var_post_cancel) == 1, "OnlyInSettlement items should be duplicated into Variance list"
    print("\n✅ Verification Successful: All logic checks passed.")
if __name__ == "__main__":
    test_reconciliation()
