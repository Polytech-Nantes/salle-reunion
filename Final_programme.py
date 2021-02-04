#Name : final program
#Date : 13/12/2020
#Creator : Syasya
#Function :  Resevation program for raspberry pi
#Note : bug in change year

#importing modules
from guizero import App, Text, Box, ListBox, PushButton, Window
from tkinter import Spinbox
from datetime import datetime, timedelta, date
from tkinter import Spinbox
from csv import DictWriter  

import pandas as pd
import sys

import pytz
import requests
from icalendar import Calendar, Event

import csv
import re
import locale

import serial
import time

#Global parameters
MAX_ROW = 26 #for 8h to 20h
MAX_COLUMN = 8 #for days
MIN_HOUR = 8 #starting hour

#Parameters to be modified depending on display plateform
MAX_WIDTH_COLUMN = 50
MAX_HEIGHT_ROW = 26
MAX_HEIGHT_HALF_ROW =13
MAX_WIDTH_ROW=250

#Define limit dates and file location
START_DATE = '2000-01-01'
END_DATE = '3000-12-30'
ICS_FILE_LOCATION = 'timetable.ics'
CSV_FILE_LOCATION = 'timetable.csv'

#Define days variables
MONDAY = 1
TUESDAY = 2
WEDNESDAY = 3
THURSDAY = 4
FRIDAY = 5
SATURDAY = 6

#Define reservation variables
h_debut=8
min_debut=0
h_fin=8
min_fin=0
j_fin=1
m_fin=1

#Define csv variables
gdate_csv = []
gstime_h_csv = []
gstime_m_csv = []
getime_h_csv = []
getime_m_csv = []
gsum_csv = []
gdate_week_no = []

#Create a display
app = App(title="Emplois du temps - IETR")
title_box = Box(app, width="fill", align="top")
reservation_box = Box(title_box, width=600, height=50, align="right")
border_box = Box(app, height="fill", width="fill", align="top",layout="grid")
row_box= [[0] * MAX_ROW for _ in range(MAX_COLUMN)]

#Create second window for reservation
window_reserv = Window(app,title="Reservation",height=400, width=400, layout="grid")
window_reserv.hide() #hide by default

#set language in french
locale.setlocale(locale.LC_ALL, 'fr')

#Define URL --for the moment we use edt setr for examples
URL = 'http://edt-v2.univ-nantes.fr/calendar/ics?timetables[0]=42004'

def init_data_array():  #clear data array
    global gdate_csv, gstime_h_csv, gstime_m_csv, getime_h_csv, getime_m_csv, gsum_csv
    
    gdate_csv.clear()
    gstime_h_csv.clear()
    gstime_m_csv.clear()
    getime_h_csv.clear()
    getime_m_csv.clear()
    gsum_csv.clear()

def url_to_ics(): #fetching data from url and transform to .ics

    now = datetime.utcnow() #provide a universal standardised reference point
    now.replace(tzinfo=pytz.utc) #accounting for daylight savings time

    today = datetime.utcnow().replace(tzinfo=pytz.utc).date()

    urls = [URL.strip() ] #strip url

    combined_cal = Calendar() #create calendar

    for url in urls:
        req = requests.get(url)
        if req.status_code != 200:  #error fetching url
            print("Error {} fetching {}: {}"
                  .format(url, req.status_code, req.text))
            continue

        cal = Calendar.from_ical(req.text)
        for event in cal.walk("VEVENT"):
            end = event.get('dtend')
            if end:
                if hasattr(end.dt, 'date'):
                    date = end.dt.date()
                else:
                    date = end.dt
                if date >= today or 'RRULE' in event:
                    copied_event = Event()
                    for attr in event:
                        if type(event[attr]) is list:
                            for element in event[attr]:
                                copied_event.add(attr, element)
                        else:
                            copied_event.add(attr, event[attr])
                    combined_cal.add_component(copied_event)
    with open("timetable.ics", "wb") as f:
        f.write(combined_cal.to_ical())

def ics_to_csv():   #transform .ics to .csv

    #get update timetable
    url_to_ics()

    #print('Here is the data from ical!')
    #print(cal.to_ical().decode('utf-8'))

    # ICAL2CSV
    class Convert2CSV():
        def __init__(self):
            self.csv_data = []

        def read_ical(self, ical_file_location):
            with open(ical_file_location, 'r', encoding='utf-8') as ical_file:
                data = ical_file.read()
            self.cal = Calendar.from_ical(data)
            return self.cal

        def make_csv(self):

            for event in self.cal.subcomponents:
                if event.name != 'VEVENT':
                    continue
                if datetime.combine(event.get('DTSTART').dt, datetime.min.time()) >= datetime.fromisoformat(START_DATE) and datetime.combine(event.get('DTEND').dt, datetime.min.time()) <= datetime.fromisoformat(END_DATE):
                    row = [
                        # Date
                        event.get('DTSTART').dt.strftime("%Y-%m-%d"),
                        # Start Time
                        event.get('DTSTART').dt.strftime("%H:%M"),
                        # End Time
                        event.get('DTEND').dt.strftime("%H:%M"),
                        # # Summary
                        # str(event.get('SUMMARY')),
                        # # Location
                        # str(event.get('LOCATION')),
                        # Description
                        str(event.get('DESCRIPTION')),
                    ]
                    row = [x.strip() for x in row]
                    self.csv_data.append(row)

        def save_csv(self, csv_location):  # type: (str) -> None
            schema = ["Date", "Start Time", "End Time", "Description"]
            with open(csv_location, 'w', encoding='utf-8') as csv_handle:
                writer = csv.writer(csv_handle)
                writer.writerow([h for h in schema])
                for row in self.csv_data:
                    writer.writerow([r.strip() for r in row])


    Convert2CSV = Convert2CSV()
    Convert2CSV.ICS_FILE_LOCATION = ICS_FILE_LOCATION
    Convert2CSV.CSV_FILE_LOCATION = CSV_FILE_LOCATION

    Convert2CSV.read_ical(Convert2CSV.ICS_FILE_LOCATION)
    Convert2CSV.make_csv()
    Convert2CSV.save_csv(Convert2CSV.CSV_FILE_LOCATION)

def update_pandas_Data():   #update pandas dataframe 
    global df   #global data file
    global col_list
    
    #extract data in from csv
    col_list = ["Date", "Start Time", "End Time", "Description"]
    df = pd.read_csv("timetable.csv", usecols=col_list)
    #print(df[["Date", "Start Time", "End Time","Description"]])

def get_data_csv(): #extract reservation information from csv

    global df
    global gdate_csv
    global gstime_h_csv, gstime_m_csv
    global getime_h_csv, getime_m_csv
    global gsum_csv
    global gdate_week_no
    
    #clear data array
    init_data_array()
    
    #update pandas dataframe
    update_pandas_Data()
    #print(df[["Date", "Start Time", "End Time", "Description"]])
 
    #extract data from csv to data array 
    for index in range (0, df.shape[0]):
        #extracting date from csv
        date_raw = df.iloc[[index],[0]].to_string().split()
        date_week_raw = date_raw [2]
       
        #save week no
        Date = str(date_week_raw)
        gdate_week_no.append(calculate_week_number(datetime.strptime(Date, "%Y-%m-%d")))
        
        gdate_csv.append(date_week_raw)
        
        #extracting start time from csv
        stime_raw = df.iloc[[index],[1]].to_string().split()
        stime_csv = stime_raw [3].split(":")
        gstime_h_csv.append((int(stime_csv [0])))
        gstime_m_csv.append((int(stime_csv [1])))
        
        #extracting end time from csv
        etime_raw = df.iloc[[index],[2]].to_string().split()
        etime_csv = etime_raw [3].split(":")
        getime_h_csv.append((int(etime_csv [0])))
        getime_m_csv.append(( int(etime_csv [1])))
        
        #extracting summary from csv
        sum_raw = df.iloc[[index],[3]].to_string().split()
        
        if(len(sum_raw)>3):
            gsum_csv.append((sum_raw [2] + " " + sum_raw [3]))
        else:
            gsum_csv.append(sum_raw [2])
    
def get_date_details():  #initiate time and date

    global df   #global data file
    global gweek_num
    global gstart, gend
    global gstart_year, gstart_month
    global gmonday, gtuesday, gwednesday, gthursday, gfriday, gsaturday

    #get updated csv
    ics_to_csv()

    #get current date
    dt = datetime.now()
    start = dt - timedelta(days=dt.weekday())
    end = start + timedelta(days=5)

    #initaite daily dates
    gmonday = start
    gtuesday = start + timedelta(days=1)
    gwednesday = start + timedelta(days=2)
    gthursday = start + timedelta(days=3)
    gfriday = start + timedelta(days=4)
    gsaturday = end

    #calculate week number
    week_num = calculate_week_number(dt)
    
    #transfering local to global data
    gweek_num = week_num
    gstart = start
    gend = end
    gstart_year = dt.year
    gstart_month = dt.month

    #initaite display information
    week_details = "   Semaine " + str(week_num) + " - " + start.strftime('%d/%m/%Y') + " au " + end.strftime('%d/%m/%Y') + "   "

    return (week_details)

 
def show_weeks():  #initial weekly display

    global gmonday, gtuesday, gwednesday, gthursday, gfriday, gsaturday
    global border_box, row_box
    global Monday, Tuesday, Wednesday, Thursday, Friday, Saturday

    #extract reservation information from csv
    get_data_csv()
    
    heure = MIN_HOUR
    bol=1;

    #row box for first column
    row_box[0][0] =  Box(border_box, width=50, height=MAX_HEIGHT_ROW, grid=[0,0], border=False)

    for m in range(1,MAX_ROW-1):
        row_box[0][m] =  Box(border_box ,width=50, height=MAX_HEIGHT_ROW, grid=[0,m], border=True)
        if(bol==1):
            time=str(heure)+"h"
            Text(row_box [0][m],text=time)
            heure+=1
            bol=0
        else:
            bol=1

    #column and row box
    for x in range(1,MAX_COLUMN-1):
        for m in range(0,MAX_ROW-1):
           row_box[x][m] =  Box(border_box, width=MAX_WIDTH_ROW, height=MAX_HEIGHT_ROW, grid=[x,m], border=True)


    Monday = Text(row_box[1][0], text=gmonday.strftime("%A")+ " " + gmonday.strftime('%d/%m'))
    Tuesday = Text(row_box[2][0], text=gtuesday.strftime("%A")+ " " + gtuesday.strftime('%d/%m'))
    Wednesday = Text(row_box[3][0], text=gwednesday.strftime("%A")+ " " + gwednesday.strftime('%d/%m'))
    Thursday = Text(row_box[4][0], text=gthursday.strftime("%A")+ " " + gthursday.strftime('%d/%m'))
    Friday = Text(row_box[5][0], text=gfriday.strftime("%A")+ " " + gfriday.strftime('%d/%m'))
    Saturday = Text(row_box[6][0], text=gsaturday.strftime("%A")+ " " + gsaturday.strftime('%d/%m'))
    
    #update display with reserved information from .csv
    update_display()
    
def show_past():    #show past week

    global gweek_num    #week number
    global gstart, gend #starting and ending date of the week
    global gstart_year
    global gmonday, gtuesday, gwednesday, gthursday, gfriday, gsaturday
    global Monday, Tuesday, Wednesday, Thursday, Friday, Saturday

    #go back a week earlier
    gweek_num = gweek_num-1

    #calculate weekly dates from week number
    d = '1/' + 'W'+ str(gweek_num) + '/' + str(gstart_year)
    dt = datetime.strptime(d, "%w/W%W/%Y")
    gstart = dt - timedelta(days=dt.weekday())
    gend = gstart + timedelta(days=5)

    #update daily dates for the week
    gmonday = gstart
    gtuesday = gstart + timedelta(days=1)
    gwednesday = gstart + timedelta(days=2)
    gthursday = gstart + timedelta(days=3)
    gfriday = gstart + timedelta(days=4)
    gsaturday = gstart + timedelta(days=5)

    #update display
    Semaine_n.value = "   Semaine " + str(gweek_num) + " - " + gmonday.strftime('%d/%m/%Y') + " au " + gsaturday.strftime('%d/%m/%Y') + "   "
    Monday.value = gmonday.strftime("%A")+ " " + gmonday.strftime('%d/%m')
    Tuesday.value = gtuesday.strftime("%A")+ " " + gtuesday.strftime('%d/%m')
    Wednesday.value = gwednesday.strftime("%A")+ " " + gwednesday.strftime('%d/%m')
    Thursday.value = gthursday.strftime("%A")+ " " + gthursday.strftime('%d/%m')
    Friday.value = gfriday.strftime("%A")+ " " + gfriday.strftime('%d/%m')
    Saturday.value = gsaturday.strftime("%A")+ " " + gsaturday.strftime('%d/%m')
    
    #update display with reservation data from .csv
    update_display()

def show_next():  #show next week (same as show_past)

    global gweek_num
    global gstart, gend
    global gstart_year
    global gmonday, gtuesday, gwednesday, gthursday, gfriday, gsaturday
    global Monday, Tuesday, Wednesday, Thursday, Friday, Saturday

    gweek_num = gweek_num+1

    d = '1/' + 'W'+ str(gweek_num) + '/' + str(gstart_year)
    dt = datetime.strptime(d, "%w/W%W/%Y")
    gstart = dt - timedelta(days=dt.weekday())
    gend = gstart + timedelta(days=5)
    
    gmonday = gstart
    gtuesday = gstart + timedelta(days=1)
    gwednesday = gstart + timedelta(days=2)
    gthursday = gstart + timedelta(days=3)
    gfriday = gstart + timedelta(days=4)
    gsaturday = gstart + timedelta(days=5)

    Semaine_n.value = "   Semaine " + str(gweek_num) + " - " + gmonday.strftime('%d/%m/%Y') + " au " + gsaturday.strftime('%d/%m/%Y') + "   "
    Monday.value = gmonday.strftime("%A")+ " " + gmonday.strftime('%d/%m')
    Tuesday.value = gtuesday.strftime("%A")+ " " + gtuesday.strftime('%d/%m')
    Wednesday.value = gwednesday.strftime("%A")+ " " + gwednesday.strftime('%d/%m')
    Thursday.value = gthursday.strftime("%A")+ " " + gthursday.strftime('%d/%m')
    Friday.value = gfriday.strftime("%A")+ " " + gfriday.strftime('%d/%m')
    Saturday.value = gsaturday.strftime("%A")+ " " + gsaturday.strftime('%d/%m')
    
    
    update_display()
    
def reservation():  #reservation window function

    global h_debut, min_debut, h_fin, min_fin, j_fin, m_fin
    global window_reserv

    #initialize variables
    h_debut=8
    min_debut=0
    h_fin=8
    min_fin=0
    j_fin=1
    m_fin=1
    
#gestion heure du debut

    def inc_h_debut():
        global h_debut
        h_debut+=1
        if h_debut==21:
            h_debut=8
        heure_debut.value=h_debut

    def dec_h_debut():
        global h_debut
        h_debut-=1
        if h_debut==7:
            h_debut=20
        heure_debut.value=h_debut

    def inc_min_debut():
        global min_debut
        min_debut+=15
        if min_debut==60:
            min_debut=0
        minute_debut.value=min_debut

    def dec_min_debut():
        global min_debut
        min_debut-=15
        if min_debut==-15:
            min_debut=45
        minute_debut.value=min_debut

#gestion heure de fin

    def inc_h_fin():
        global h_fin
        h_fin+=1
        if h_fin==21:
            h_fin=8
        heure_fin.value=h_fin

    def dec_h_fin():
        global h_fin
        h_fin-=1
        if h_fin==7:
            h_fin=20
        heure_fin.value=h_fin

    def inc_min_fin():
        global min_fin
        min_fin+=15
        if min_fin==60:
            min_fin=0
        minute_fin.value=min_fin

    def dec_min_fin():
        global min_fin
        min_fin-=15
        if min_fin==-15:
            min_fin=45
        minute_fin.value=min_fin

#gestion date

    def inc_j_fin():
        global j_fin
        j_fin+=1
        if j_fin==32:
            j_fin=1
        t_jour.value=j_fin

    def dec_j_fin():
        global j_fin
        j_fin-=1
        if j_fin==0:
            j_fin=31
        t_jour.value=j_fin

    def inc_m_fin():
        global m_fin
        m_fin+=1
        if m_fin==13:
            m_fin=1
        t_mois.value=m_fin

    def dec_m_fin():
        global m_fin
        m_fin-=1
        if m_fin==0:
            m_fin=12
        t_mois.value=m_fin

    #show window
    window_reserv.show()

    #Box for choosing starting time to reserve
    Debut = Box(window_reserv,  width=200, height=200, grid=[0,0],align="top",layout="grid")
    
    t_debut = Text(Debut,text= "Heure de debut :", grid=[0,1])
    plus_h_debut = PushButton(Debut,command=inc_h_debut, text="+", grid=[1,0])
    heure_debut = Text(Debut, text= h_debut, grid=[1,1])
    moins_h_debut = PushButton(Debut,command=dec_h_debut, text="-", grid=[1,2])
   
    points_heure_debut = Text(Debut, text= " : ", grid=[2,1])

    plus_min_debut = PushButton(Debut,command=inc_min_debut, text="+", grid=[3,0])
    minute_debut = Text(Debut, text= min_debut, grid=[3,1])
    moins_min_debut = PushButton(Debut,command=dec_min_debut, text="-", grid=[3,2])

    #Box for choosing ending time to reserve
    fin = Box(window_reserv,  width=200, height=200, grid=[0,1],align="top",layout="grid")
    
    t_fin = Text(fin, text= "Heure de fin :", grid=[0,1])
    plus_h_fin = PushButton(fin,command=inc_h_fin, text="+", grid=[1,0])
    heure_fin = Text(fin, text= h_fin, grid=[1,1])
    moins_h_fin = PushButton(fin,command=dec_h_fin, text="-", grid=[1,2])
   
    points_heure_fin = Text(fin, text= " : ", grid=[2,1])
    
    plus_min_fin = PushButton(fin,command=inc_min_fin, text="+", grid=[3,0])
    minute_fin = Text(fin, text= min_fin, grid=[3,1])
    moins_min_fin = PushButton(fin,command=dec_min_fin, text="-", grid=[3,2])

    #Box for choosing date to reserve
    jour = Box(window_reserv,  width=200, height=200, grid=[1,0],align="top" and "right",layout="grid")
    
    t_jour = Text(jour, text= "Jour :", grid=[0,1])
    plus_jour = PushButton(jour,command=inc_j_fin, text="+", grid=[1,0])
    t_jour = Text(jour, text=j_fin, grid=[1,1])
    moins_h_fin = PushButton(jour,command=dec_j_fin, text="-", grid=[1,2])

    shlach_jour = Text(jour, text= "/", grid=[2,1])

    plus_mois = PushButton(jour,command=inc_m_fin, text="+", grid=[3,0])
    t_mois = Text(jour, text= m_fin, grid=[3,1])
    moins_mois = PushButton(jour,command=dec_m_fin, text="-", grid=[3,2])

    #save reservation date and time
    confirm= PushButton(window_reserv, command=save_reservation, text="Confirmer", align="right", grid=[1,1])

def reservation_success():  #success reservation window function
    global window_reserv
    
    #hide reservation window
    window_reserv.hide()
    
    #a function to create reservation displays
    window = Window(app,title=" ", height=100, width=400)

    #Box for choosing starting time to reserve
    text = Text(window, text= "Reservation success!", align="top")

def reservation_error():  #success reservation window function
    
    #a function to create reservation displays
    window_err = Window(app,title=" ", height=100, width=400)

    #Box for choosing starting time to reserve
    text = Text(window_err, text= "ID Unrecognized. No rights to reserved", align="top")



def save_reservation():   #save date and time in csv file and call reunion function
     
    reservation_success()
     
    #exemple input
    Date = "2021-"+str(m_fin)+"-"+str(j_fin)
    STime = str(h_debut)+":"+str(min_debut)
    ETime = str(h_fin)+":"+str(min_fin)
    Name = "GUERIN"
    
    new_row = {'Date':Date,'Start Time':STime,'End Time':ETime,'Description':Name}
    
    #update dataframe with .csv data
    update_pandas_Data()
    
    with open('timetable.csv', 'a') as f_object: 
        # Open your CSV file in append mode 
        # Create a file object for this file 
        dictwriter_object = DictWriter(f_object, fieldnames=col_list) 
      
        #Pass the file object and a list of column names to DictWriter() 
        #Pass the dictionary as an argument to the Writerow() 
        dictwriter_object.writerow(new_row) 
      
        #Close the file object 
        f_object.close() 
    
    #refresh display
    update_reserved_display()

def reunion (heure_debut,min_debut,heure_fin,min_fin,jour,personne):    #change display with red backgroud for reserved slot
    global row_box
    
    y=heure_debut*2+int(min_debut/30)-15
    temps_de_la_reunion=(heure_fin*2+int(min_fin/30))-((heure_debut*2+int(min_debut/30)))
    
    for i in range (0,temps_de_la_reunion):
        text= Text(row_box[jour][y+i],text=personne, bg="red")
        #print(str(heure_debut)+"    "+str(heure_fin)+"  "+str(jour)+"   "+str(personne))
        
        
def determine_day(Date):    #return days name for input date

    dt = datetime.strptime(Date, "%Y-%m-%d")
    jour = dt.strftime("%A")
    switcher ={
            "lundi":MONDAY,
            "mardi":TUESDAY,
            "mercredi":WEDNESDAY,
            "jeudi":THURSDAY,
            "vendredi":FRIDAY,
            "samedi":SATURDAY
            }
    return switcher.get(jour,"Invalid day of week")

def calculate_week_number(dt):  #return the week number of the input date

    date = pd.Timestamp(year = dt.year, month = dt.month, day = dt.day, hour = 0, second = 0, tz = 'Europe/Paris')
    year, week_num, day_of_week = date.isocalendar()
    
    return(week_num)

def add_data_array():   #append reservation information
    
    global df
    global gdate_csv
    global gstime_h_csv, gstime_m_csv
    global getime_h_csv, getime_m_csv
    global gsum_csv
    global gdate_week_no
    
    #update pandas dataframe 
    update_pandas_Data()
    
    #go to last row on array
    index = df.shape[0]-1
    
    #extracting date from csv
    date_raw = df.iloc[[index],[0]].to_string().split()
    date_week_raw = date_raw [2]
    
    #save week no
    Date = str(date_week_raw)
    gdate_week_no.append(calculate_week_number(datetime.strptime(Date, "%Y-%m-%d")))
    
    gdate_csv.append(date_week_raw)
    
    #extracting start time from csv
    stime_raw = df.iloc[[index],[1]].to_string().split()
    stime_csv = stime_raw [3].split(":")
    gstime_h_csv.append((int(stime_csv [0])))
    gstime_m_csv.append((int(stime_csv [1])))
    
    #extracting end time from csv
    etime_raw = df.iloc[[index],[2]].to_string().split()
    etime_csv = etime_raw [3].split(":")
    getime_h_csv.append((int(etime_csv [0])))
    getime_m_csv.append(( int(etime_csv [1])))
    
    #extracting summary from csv
    sum_raw = df.iloc[[index],[3]].to_string().split()
    
    if(len(sum_raw)>3):
        gsum_csv.append((sum_raw [2] + " " + sum_raw [3]))
    else:
        gsum_csv.append(sum_raw [2])


def clear_cal():   #clear display
    global border_box, row_box
    
    for x in range(1,MAX_COLUMN-1):
        for m in range(1,MAX_ROW-1):
           row_box[x][m] =  Box(border_box, width=MAX_WIDTH_ROW, height=MAX_HEIGHT_ROW, grid=[x,m], border=True)
    
def update_display():   #update display with reservation details
    global df
    global gweek_num
    global gdate_csv, gstime_h_csv, gstime_m_csv, getime_h_csv, getime_m_csv, gsum_csv

    #update pandas dataframe
    update_pandas_Data()
    
    #clear display
    clear_cal()
    
    #display all reservation data corresponding to its weekly 
    for i in range (0, df.shape[0]):
        if(gdate_week_no[i] == gweek_num):  #compare week no from the date and the weekly display 
            #change reserved slot to red
            reunion (gstime_h_csv[i],gstime_m_csv[i],getime_h_csv[i],getime_m_csv[i],determine_day(gdate_csv[i]),gsum_csv[i])

def update_reserved_display():  #update display with new added reservation details from reservation window
    
    global df
    global gweek_num
    global gdate_csv, gstime_h_csv, gstime_m_csv, getime_h_csv, getime_m_csv, gsum_csv
    
    #append new reservation information
    add_data_array()
    
    #go to last array index
    end_of_row = df.shape[0] - 1
    
    if(gdate_week_no[end_of_row] == gweek_num): #compare week no from the date and the weekly display 
        #change reserved slot to red
        reunion (gstime_h_csv[end_of_row],gstime_m_csv[end_of_row],getime_h_csv[end_of_row],getime_m_csv[end_of_row],determine_day(gdate_csv[end_of_row]),gsum_csv[end_of_row])

def id_check():
    scan=1
    read_id=0
    
    ser = serial.Serial('COM5', 9600, timeout=1) #verifier tape << ls /dev/tty* >> sur commande prompt //w pc
    ser.flush()
    
    user1 = "04 3B 84 62 94 57 80"
    
    id_ok=1
    
    while (scan):
        if (ser.in_waiting > 0):
            #print("here")
            line = ser.readline().decode('utf-8').rstrip()
            print(line)
            
            if(read_id):
                print(line)
                if(user1 == line):
                    #print("OK")
                    reservation()
                    scan=0
                else:
                    print("ko")
                    reservation_error()
                    scan=0
            if(line=="Firmware ver. 1.6"):
                read_id=1
                


#
#main
if __name__ == '__main__':
    global Semaine_n
    
    heading_title_week = get_date_details()

    Gauche = PushButton(title_box, command=show_past, text="<", align="left")
    Semaine_n = Text(title_box, text= heading_title_week, align="left")
    Droite = PushButton(title_box, command=show_next, text=">", align="left")

    #change TO id check
    Reserver = PushButton(reservation_box, command=id_check, text="Reservez un creneau d'horaire", align="right")
    show_weeks()
    app.display() #display end
