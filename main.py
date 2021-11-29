from __future__ import print_function
import argparse
import time
import serial
import json
import application as app
import page as pg
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume

def findAusioSession(name, sessions):
    for session in sessions:
        if session.Process and session.Process.name() == name:
            return session
    return None

def findCurrentSessions(current_page, sessions):
    current_sessions = list()
    
    for application in current_page.applications:
        session = findAusioSession(application.exe, sessions)
        if(session != None):
            current_sessions.append(session)
    return current_sessions

def findVolumes(current_sessions):
    return list(map(lambda x: x._ctl.QueryInterface(ISimpleAudioVolume), current_sessions))

def nextPageIndex(list, page):
    if(page == len(list)-1):
        return 0
    else:
        return page+1

def changePage(current_page, sessions, ser):
    current_sessions = findCurrentSessions(current_page, sessions)
    for application in current_page.applications:
        sendImage(application.logo, ser)
    if len(current_page.applications) < 2:
        sendImage("Logos/Test.json", ser)
    return findVolumes(current_sessions)

def readImageFromFile(name):
    values = list(json.load(open(name))['values'])
    l = list()
    for value in values:
        l.append(int(value, 16))
    return bytearray(l)

def sendImage(name, ser):
    l = readImageFromFile(name)
    print("sending image")
    for val in l:
        ser.write(val.to_bytes(1, byteorder='big'))
    print("done")

def debugInfo(info, debug):
    if(debug):
        print(info)

def initialize():
    pages = list()
    applications = json.load(open('Applications.json'))['applications']
    i = 0
    temp = list()

    while i < len(applications):
        app1 = app.application(applications[i]['name'], applications[i]['exe'], applications[i]['logo_path'])
        if(i < len(applications) - 1):
            app2 = app.application(applications[i+1]['name'], applications[i+1]['exe'], applications[i+1]['logo_path'])
            pages.append(pg.page([app1, app2]))
        else:
            pages.append(pg.page([app1]))
        i += 2
    
    if(i == 1):
        pages.append(pg.page(temp))
    
    debugInfo("Pages: " + pages.__str__(), args.debug)
    page_index = 0
    current_page = pages[page_index]

    sessions = AudioUtilities.GetAllSessions()
    
    ser = serial.Serial(port='COM3', baudrate=9600)
    time.sleep(2)
    volumes = changePage(current_page, sessions, ser)
    
    while True:
        if(ser.in_waiting > 0):
            line = str(ser.readline().strip())
            start = line.index('{')
            end = line.index('}',start+1)+1

            message = json.loads(str(line[start:end]))

            cmd = message["command"]
            vals = list([message["value1"], message["value2"]])
            debugInfo("cmd " + str(cmd), args.debug)

            if(cmd == 0):
                i = 0
                for volume in volumes:
                    debugInfo("volume " + str(i) + ": " + str(float(vals[i])), args.debug)
                    volume.SetMasterVolume(float(vals[i]), None)
                    i +=1
            #next page
            elif(cmd == 1):
                page_index = nextPageIndex(pages, page_index)
                current_page = pages[page_index]
                debugInfo("page_index " + str(page_index) + current_page.__str__(), args.debug)
                sessions = AudioUtilities.GetAllSessions()
                volumes = changePage(current_page, sessions, ser)
        else:
            time.sleep(0.01)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', help='display debug info')
    args = parser.parse_args()
    initialize()

#(0x([0-9]|[a-f]){2}) regex for changing hex in strings $1