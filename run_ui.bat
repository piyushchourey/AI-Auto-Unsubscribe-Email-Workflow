@echo off
echo Starting Unsubscribe Email Workflow UI...
echo.
echo Make sure the API is running in another terminal:
echo python main.py
echo.
pause
call venv\Scripts\activate.bat
streamlit run streamlit_app.py
