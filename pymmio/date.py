
from datetime import date

def today():
    today = date.today()
    return(today.strftime("%y%m%d"))


def yearmon(dtb,dte):
    nowmon = dte.month
    nowyear = dte.year
    mon = dtb.month
    yr = dtb.year
    while yr<nowyear or mon<=nowmon:
        yield yr, mon
        mon += 1
        if mon>12:
            mon=1
            yr+=1