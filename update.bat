taskkill /f /im python.exe
git pull origin master --allow-unrelated-histories
pip -r requirements.txt
cd kpi_radio_bot
python main.py
exit
