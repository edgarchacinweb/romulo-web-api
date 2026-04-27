import os
from datetime import datetime
files = ['06-04-2026_21_55_43_002834.sql', '27-04-2026_01_27_17_600106.sql']
data = [{'Fecha': i.split('_')[0], 'Hora': datetime.strptime(':'.join(i.split('_')[1:3]), '%H:%M').strftime('%I:%M %p')} for i in files]
print(data)
data.sort(key=lambda x: datetime.strptime(f"{x['Fecha']} {x['Hora']}", '%d-%m-%Y %I:%M %p'), reverse=True)
print(data)
