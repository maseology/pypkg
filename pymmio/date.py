
from datetime import date

def today():
    today = date.today()
    return(today.strftime("%y%m%d"))