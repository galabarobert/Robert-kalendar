#!/usr/bin/env python3
"""Generate a rolling Slovak iCalendar feed.
Requires skyfield for accurate moon phases and equinoxes/solstices.
School holidays are data-driven: update SCHOOL_HOLIDAYS when the Slovak Ministry publishes new dates.
"""
from datetime import date, timedelta
from pathlib import Path
import calendar, uuid

OUT = Path('robert-kalendar.ics')
START_YEAR = date.today().year
END_YEAR = START_YEAR + 2

# Nitriansky kraj. Add official Ministry terms here when published.
SCHOOL_HOLIDAYS = {
  2027: [
    ('2027-01-01','2027-01-08','🎄 Vianočné prázdniny'),
    ('2027-02-01','2027-02-02','🏫 Polročné prázdniny'),
    ('2027-03-01','2027-03-06','🏫 Jarné prázdniny – Nitriansky kraj'),
    ('2027-03-25','2027-03-31','🐣 Veľkonočné prázdniny'),
    ('2027-07-01','2027-09-01','☀️ Letné prázdniny'),
    ('2027-10-28','2027-10-30','🍂 Jesenné prázdniny'),
    ('2027-12-23','2028-01-08','🎄 Vianočné prázdniny'),
  ]
}

def esc(s): return s.replace('\\','\\\\').replace(';','\\;').replace(',','\\,').replace('\n','\\n')
def add(lines, d, title, end=None):
    end = end or (d + timedelta(days=1))
    uid = uuid.uuid5(uuid.NAMESPACE_URL, f'robert-sk:{d}:{title}')
    lines += ['BEGIN:VEVENT',f'UID:{uid}@github',f'DTSTART;VALUE=DATE:{d:%Y%m%d}',f'DTEND;VALUE=DATE:{end:%Y%m%d}',f'SUMMARY:{esc(title)}','END:VEVENT']
def easter(y):
    a=y%19;b=y//100;c=y%100;d=b//4;e=b%4;f=(b+8)//25;g=(b-f+1)//3;h=(19*a+b-d-g+15)%30;i=c//4;k=c%4;l=(32+2*e+2*i-h-k)%7;m=(a+11*h+22*l)//451
    return date(y,(h+l-7*m+114)//31,((h+l-7*m+114)%31)+1)
def last_sunday(y,m):
    d=date(y,m,calendar.monthrange(y,m)[1]); return d-timedelta(days=(d.weekday()-6)%7)
def nth_sunday(y,m,n):
    d=date(y,m,1); return d+timedelta(days=(6-d.weekday())%7+7*(n-1))

# Fixed Slovak namedays. Date mapping is stable; update source table only if official calendar changes.
NAMES = {
(1,1):'Alexandra, Sandra, Karina',(1,2):'Daniela',(1,3):'Drahoslav',(1,4):'Andrea, Artur',(1,5):'Antónia',(1,6):'Bohuslava, Atila',(1,7):'Severín',(1,8):'Alexej, Alex, Alexia',(1,9):'Daša',
}
# The checked-in feed remains the complete source of current name days. See README before expanding years.

def generate():
    lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Robert Galaba//SK Calendar//SK','CALSCALE:GREGORIAN','METHOD:PUBLISH','X-WR-CALNAME:Robert – SK kalendár','X-WR-TIMEZONE:Europe/Bratislava','X-PUBLISHED-TTL:PT12H','REFRESH-INTERVAL;VALUE=DURATION:PT12H']
    for y in range(START_YEAR, END_YEAR+1):
        for (m,d),n in NAMES.items(): add(lines,date(y,m,d),n)
        e=easter(y)
        fixed=[(1,1,'🇸🇰 Deň vzniku Slovenskej republiky'),(1,6,'🇸🇰 Zjavenie Pána – Traja králi'),(5,1,'🇸🇰 Sviatok práce'),(5,8,'🇸🇰 Deň víťazstva nad fašizmom'),(7,5,'🇸🇰 Sv. Cyril a Metod'),(8,29,'🇸🇰 Výročie SNP'),(9,1,'🇸🇰 Deň Ústavy SR'),(9,15,'🇸🇰 Sedembolestná Panna Mária'),(10,28,'🇸🇰 Deň vzniku samostatného česko-slovenského štátu'),(11,1,'🇸🇰 Sviatok Všetkých svätých'),(11,17,'🇸🇰 Deň boja za slobodu a demokraciu'),(12,24,'🇸🇰 Štedrý deň'),(12,25,'🇸🇰 Prvý sviatok vianočný'),(12,26,'🇸🇰 Druhý sviatok vianočný')]
        for m,d,t in fixed: add(lines,date(y,m,d),t)
        add(lines,e-timedelta(days=2),'🇸🇰 Veľký piatok'); add(lines,e+timedelta(days=1),'🇸🇰 Veľkonočný pondelok')
        add(lines,last_sunday(y,3),'⏰ Začína letný čas'); add(lines,last_sunday(y,10),'⏰ Začína zimný čas')
        add(lines,date(y,2,14),'❤️ Valentín'); add(lines,nth_sunday(y,5,2),'❤️ Deň matiek'); add(lines,nth_sunday(y,6,3),'❤️ Deň otcov')
        add(lines,date(y,3,8),'🌷 Medzinárodný deň žien'); add(lines,date(y,6,1),'🧒 Medzinárodný deň detí'); add(lines,date(y,4,22),'🌍 Deň Zeme'); add(lines,date(y,12,6),'🎅 Mikuláš'); add(lines,date(y,12,31),'🎆 Silvester')
        for s,e2,t in SCHOOL_HOLIDAYS.get(y,[]): add(lines,date.fromisoformat(s),t,date.fromisoformat(e2))
    # Accurate astronomy generated if skyfield is available in GitHub Actions.
    try:
        from skyfield.api import load
        from skyfield import almanac
        ts=load.timescale(); eph=load('de421.bsp')
        t0=ts.utc(START_YEAR,1,1); t1=ts.utc(END_YEAR+1,1,1)
        times, phases=almanac.find_discrete(t0,t1,almanac.moon_phases(eph))
        for t,p in zip(times,phases):
            if int(p) in (0,2):
                d=t.utc_datetime().date(); add(lines,d,'🌑 Nov' if int(p)==0 else '🌕 Spln')
        times,seasons=almanac.find_discrete(t0,t1,almanac.seasons(eph))
        labels=['🌱 Začiatok jari','☀️ Začiatok leta','🍂 Začiatok jesene','❄️ Začiatok zimy']
        for t,s in zip(times,seasons): add(lines,t.utc_datetime().date(),labels[int(s)])
    except Exception as ex:
        print('Astronomy skipped:',ex)
    lines.append('END:VCALENDAR')
    OUT.write_text('\r\n'.join(lines)+'\r\n',encoding='utf-8')
if __name__=='__main__': generate()
