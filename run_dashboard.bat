@echo off
echo ========================================================
echo Launching UAE Telecom & Subsea Resilience Dashboard...
echo ========================================================
py -m streamlit run 09_Audit_and_Evaluation\dashboard\app.py --server.port 8501 --client.toolbarMode minimal
pause
