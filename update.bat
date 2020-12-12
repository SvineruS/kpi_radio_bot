taskkill /f /im python.exe
git pull origin master --allow-unrelated-histories
pip install -r requirements.txt
cd kpi_radio
python main.py
exit
