"""Structural probe for the same account/records binding in each MainActivity copy.

Runtime Android/network behavior is recorded separately in DEVICE_TEST_RESULTS.xml.
"""
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
print("INPUT=account-and-records")
print("ACCOUNT_VIEWMODEL_BOUND=" + str("WelloraApp(accountModel" in source))
print("ACCOUNT_PANEL_BOUND=" + str("AccountPanel(accountModel, seniorMode)" in source))
print("LIVE_RECORDS_SUMMARY_BOUND=" + str("BasicProfileSummary(accountState)" in source))
