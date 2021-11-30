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
    debugInfo("Sending image: " + name, args.debug)
    for val in l:
        ser.write(val.to_bytes(1, byteorder='big'))
    debugInfo("done", args.debug)

def debugInfo(info, debug):
    if(debug):
        print(info)

def createPages(applications):
    pages = list()
    validAps = list()
    i = 0

    while i < len(applications):
        if checkExistAudio(applications[i]['exe'], AudioUtilities.GetAllSessions()):
            validAps.append(app.application(applications[i]['name'], applications[i]['exe'], applications[i]['logo_path']))
        i += 1
    i = 0
    while i < len(validAps):
        if i < len(validAps) - 1:
            pages.append(pg.page([validAps[i], validAps[i+1]]))
        else:
            pages.append(pg.page([validAps[i]]))
        i += 2
    return pages

def checkExistAudio(name, sessions):
    for session in sessions:
        if session.Process and session.Process.name() == name:
            return True
    return False

def initialize():
    applications = json.load(open('Applications.json'))['applications']
    pages = createPages(applications)
    debugInfo("Applications: " + applications.__str__(), args.applications)
    debugInfo("Pages: " + pages.__str__(), args.pages)
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
            debugInfo("cmd " + str(cmd), args.command)
            #change values
            if(cmd == 0):
                i = 0
                j = 0
                for application in current_page.applications:
                    debugInfo("changing " + application.exe, args.volumes)
                    if len(volumes) > i and checkExistAudio(application.exe, findCurrentSessions(current_page, sessions)):
                        debugInfo("volume " + str(i) + ": " + str(float(vals[j])), args.volumes)
                        volumes[i].SetMasterVolume(float(vals[j]), None)
                        i +=1
                    j += 1
            #next page
            elif(cmd == 1):
                pages = createPages(applications)
                page_index = nextPageIndex(pages, page_index)
                current_page = pages[page_index]
                debugInfo("page_index " + str(page_index) + current_page.__str__(), args.pages)
                sessions = AudioUtilities.GetAllSessions()
                volumes = changePage(current_page, sessions, ser)
        else:
            time.sleep(0.01)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true', help='display debug info')
    parser.add_argument('-a', '--applications', action='store_true', help='application list debug info')
    parser.add_argument('-v', '--volumes', action='store_true', help='volumes debug info')
    parser.add_argument('-c', '--command', action='store_true', help='command debug info')
    parser.add_argument('-p', '--pages', action='store_true', help='pages debug info')
    args = parser.parse_args()
    initialize()

#(0x([0-9]|[a-f]){2}) regex for changing hex in strings $1