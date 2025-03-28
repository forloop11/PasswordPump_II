#!/usr/bin/env python
#
# GUI to interface with the PasswordPump
#
#  Copyright
#  =========
#  - Copyright ©2018, ©2019, ©2020 Daniel J Murphy <dan-murphy@comcast.net>
#
# Built on Python 3.8
#
# Purpose:
#   This is the client side of the PasswordPump.  This program's job is to
#   allow the user to edit the credentials that are stored inside the EEprom
#   chips that reside on the PasswordPump device.

# Defects and Enhancements Key:
# - = outstanding
# x = fixed but needs testing
# * = fixed
#
# Defects:
# - If a password starts with a 0 it is left off when exported into a .csv
#   file.
# - If an account name contains a comma, and you visit the field, after
#   exiting the GUI and reloading all of the accounts, the comma has changed
#   into a hashtag and all of the remaining fields are blank.
# - After adding a new account, if the style isn't specified (or left on the
#   default), ValueError: invalid literal for int() with base 10: '' occurs
#   on subsequent visits to that account.
# * Change the 0 / 1 for Tab and Return to just Tab and Return.  Select tab
#   as the default.
# * If input focus is on the password field, and you select Insert, then
#   navigate to the Account field, the password field of the account you
#   were on originally is set to blank.
# * During import of PasswordPump format, the username is occasionally dropped
# * Similarly, if any of the fields have an embedded | (pipe) character the
#   fields in the PasswordPumpGUI can get out of synch; e.g. account name
#   appears in the username field.
# * If a password (or any other field) contains a ~ or a |, python throws an
#   exception during import or changes those characters into /1 otherwise.
# * If there's a / at the end of a URL during import python throws an
#   exception, so strip it.
# * Hangs the MCU when adding credentials without Style or URL.
# * Sometimes changing the URL in place is not working
# * All buttons except Exit should be disabled before the port is opened.
# * When an account is inserted the accounts list box doesn't refresh, you must
#   click on Save.
# * Add style to the PP format.
# * Remove the Save button.
# * skip the heading row if it exists when importing PasswordPump format.
# * In this UI make style last
# * The 32nd character of the URL is missing after import.
# * Leading spaces are not respected in Account Name.
# * After importing from a file the record selected and the record displayed
#   do not match.
# * Style is garbage when importing PasswordPump file.
# * When clicking on Next and Previous the Account List textbox selected
#   account isn't following along.
# * URLs are getting chopped off at 32 characters. Had to break the URL into 3
#   equally sized pieces and send them individually to the PasswordPump where
#   the final URL is assembled and saved to EEprom.
#
# Enhancements:
# - Rename account
# - Settings (RGB LED Intensity, Timeout Minutes, Login Attempts)
# - Configurable Generate Password length
# * Custom group names (currently only editable via device)
# * Settings (Show Password, Decoy Password, Change Master Password,
#   Factory Reset)
# * Respect the show password setting
# * Add old password to PasswordPump format
# * Save to old password
# * Generate password
# * Export to PasswordPump format
# * Only allow one instance of the PasswordPump to run at a time.
# * Confirm before deleting
# * When importing from PasswordPump format, import the groups, too.
# * Save a field when it loses focus (via <Tab> or <Return> or clicking out of
#   the field)
# * Add groups to the UI
# * Import files via this UI.
# * Add a scrollbar to the account list box.
#
# Required Libraries:
# - Tendo
#   pip install tendo
# - PyCmdMessenger
#   https://github.com/harmsm/PyCmdMessenger
#   sudo pip3 install PyCmdMessenger
# - Tkinter
#   sudo apt-get install python3.6-tk   -OR-
#   sudo apt-get install python3-tk
# - powned
#   pip install powned
#
#  License                                                                       
#  =======
#  Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
#  (CC BY-NC-SA 4.0). https://creativecommons.org/licenses/by-nc-sa/4.0/
#  This program and device are distributed in the hope that they will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
#  or FITNESS FOR A PARTICULAR PURPOSE.
#
#  You are free to:
#    Share — copy and redistribute the material in any medium or format
#    Adapt — remix, transform, and build upon the material
#    The licensor cannot revoke these freedoms as long as you follow the license
#    terms.
#
#  Under the following terms:
#  Attribution — You must give appropriate credit, provide a link to the license,
#  and indicate if changes were made. You may do so in any reasonable manner, but
#  not in any way that suggests the licensor endorses you or your use.
#
#  NonCommercial — You may not use the material for commercial purposes.
#
#  ShareAlike — If you remix, transform, or build upon the material, you must
#  distribute your contributions under the same license as the original.
#
#  No additional restrictions — You may not apply legal terms or technological 
#  measures that legally restrict others from doing anything the license permits.
#
#  Notices:
#  You do not have to comply with the license for elements of the material in the
#  public domain or where your use is permitted by an applicable exception or
#  limitation.
#  
#  No warranties are given. The license may not give you all of the permissions
#  necessary for your intended use. For example, other rights such as publicity,
#  privacy, or moral rights may limit how you use the material.

from tkinter import *
from tkinter.ttk import *
from tkinter.filedialog import askopenfilename
from tkinter.filedialog import asksaveasfilename

import tkinter.simpledialog
import tkinter.messagebox
import PyCmdMessenger
import serial
import serial.tools.list_ports
from serial.tools.list_ports import comports
#import argparse
import csv
import time
from tendo import singleton
#import string
from random import *
import platform
import powned

me = singleton.SingleInstance()                                                # will sys.exit(-1) if other instance is running

global c
window = Tk()
window.title("PasswordPump Edit Credentials v2.0.4")

if (platform.system() == "Windows"):                                           # e.g. Windows10
    window.geometry('400x560')
elif (platform.system() == "Darwin"):                                          # Macintosh
    window.geometry('580x600')
elif (platform.system() == "Linux"):                                           # e.g. Ubuntu
    window.geometry('580x600')
else:
    window.geometry('400x555')

lbl_port = Label(window, text="Port", anchor=E, justify=RIGHT, width=10)
lbl_port.grid(column=1, row=0)
frame = Frame(window, width=200, height=200)

frame.grid(column=2,row=1)
lb = Listbox(frame, selectmode=SINGLE, justify=LEFT, width=38, bd=0, exportselection=False)
scrollbar = Scrollbar(frame, orient=VERTICAL)
scrollbar.pack(side=RIGHT, fill=Y)
scrollbar.config(command=lb.yview)
lb.config(yscrollcommand=scrollbar.set)
lb.pack()

lbl_acct = Label(window, text="Account", anchor=E, justify=RIGHT, width=10)
lbl_acct.grid(column=1, row=2)

lbl_user = Label(window, text="User Name", anchor=E, justify=RIGHT, width=10)
lbl_user.grid(column=1, row=3)

lbl_old_pass = Label(window, text="Old Password", anchor=E, justify=RIGHT, width=10)
lbl_old_pass.grid(column=1, row=5)

lbl_url = Label(window, text="URL", anchor=E, justify=RIGHT, width=10)
lbl_url.grid(column=1, row=6)

lbl_style = Label(window, text="Style", anchor=E, justify=RIGHT, width=10)
lbl_style.grid(column=1, row=7)

translation_table = dict.fromkeys(map(ord, ',|~"'), '#')

def stripBadChars(unicode_line):
    unicode_line = unicode_line.translate(translation_table)
    return(unicode_line.strip("/"))

def calcAcctPositionSend(aPosition):
    if (aPosition < 251):
        aPosition += 4
    if (aPosition == 92):
        aPosition = 1
    elif (aPosition == 124):
        aPosition = 2
    elif (aPosition == 126):
        aPosition = 3
    return(aPosition)

def calcAcctPositionReceive(aPosition):
    if (aPosition == 1):
        aPosition = 88
    elif (aPosition == 2):
        aPosition = 120
    elif (aPosition == 3):
        aPosition = 122
    else:
        if (aPosition < 255):
            aPosition -= 4
    return(aPosition)

def clickedOpen():
    global arduino
    global arduinoAttached
    window.config(cursor="watch")
    updateDirections("Connecting to PasswordPump.")
    try:                                                                       #
        arduino = PyCmdMessenger.ArduinoBoard(port, baud_rate=115200, timeout=20.0, settle_time=2.0, enable_dtr=False,
                                              int_bytes=4, long_bytes=8, float_bytes=4, double_bytes=8)
        arduinoAttached = 1
    except serial.serialutil.SerialException:
        updateDirections("Error when attaching to\r\nPasswordPump.  Device not\n\rfound. Power cycle the\n\rPasswordPump and try again.")

    global commands
    commands = [["kAcknowledge","b"],                                          # List of command names (and formats for their associated arguments). These must
                ["kStrAcknowledge", "s"],                                      # be in the same order as in the Arduino sketch.
                ["pyReadAccountName", "b"],
                ["pyReadUserName", "b"],
                ["pyReadPassword", "b"],
                ["pyReadOldPassword", "b"],
                ["pyReadURL", "b"],
                ["pyReadStyle", "b"],
                ["pyReadGroup", "b"],
                ["pyUpdateAccountName", "s"],
                ["pyUpdateUserName", "bs"],
                ["pyUpdatePassword", "bs"],
                ["pyUpdateURL", "bs"],
                ["pyUpdateURL_1", "s"],
                ["pyUpdateURL_2", "s"],
                ["pyUpdateURL_3", "bs"],
                ["pyUpdateStyle", "bs"],
                ["pyUpdateGroup","bb"],
                ["pyUpdateOldPassword","bs"],
                ["pyGetNextPos","b"],
                ["pyGetPrevPos","b"],
                ["pyGetAcctPos",""],
                ["pyReadHead",""],
                ["pyReadTail",""],
                ["pyGetNextFreePos",""],
                ["kError",""],
                ["pyDeleteAccount","b"],
                ["pyExit",""],
                ["pyBackup",""],
                ["pyFactoryReset",""],
                ["pyRestore",""],
                ["pyGetAccountCount", ""],
                ["pyDecoyPassword", "b"],
                ["pyShowPasswords", "b"],
                ["pyReadGroup1Name",""],
                ["pyReadGroup2Name",""],
                ["pyReadGroup3Name",""],
                ["pyReadGroup4Name",""],
                ["pyReadGroup5Name",""],
                ["pyReadGroup6Name",""],
                ["pyReadGroup7Name",""],
                ["pyUpdateCategoryName","bs"],
                ["pyChangeMasterPass", "s"]]

    global c                                                                   # Initialize the messenger
    c = PyCmdMessenger.CmdMessenger(arduino, commands, field_separator='~', command_separator='|', escape_separator='\\')

    #txt_acct.bind("<Return>",(lambda _: clickedAcctParam(txt_acct)))          # When the user clicks on return save the edited item
    #txt_user.bind("<Return>",(lambda _: clickedUserParam(txt_user)))
    #txt_pass.bind("<Return>",(lambda _: clickedPassParam(txt_pass)))
    #txt_url.bind("<Return>",(lambda _: clickedUrlParam(txt_url)))

    #txt_acct.bind("<Tab>",(lambda _: clickedAcctParam(txt_acct)))             # When the user tabs off of the field save the edited item
    #txt_user.bind("<Tab>",(lambda _: clickedUserParam(txt_user)))
    #txt_pass.bind("<Tab>",(lambda _: clickedPassParam(txt_pass)))
    #txt_url.bind("<Tab>",(lambda _: clickedUrlParam(txt_url)))

    txt_acct.bind("<FocusOut>",(lambda _: clickedAcctParam(txt_acct)))         # When the user clicks off of the field save the edited item
    txt_user.bind("<FocusOut>",(lambda _: clickedUserParam(txt_user)))
    txt_pass.bind("<FocusOut>",(lambda _: clickedPassParam(txt_pass)))
    txt_old_pass.bind("<FocusOut>",(lambda _: clickedOldPassParam(txt_old_pass)))
    txt_url.bind("<FocusOut>",(lambda _: clickedUrlParam(txt_url)))

    c.send("pyReadHead")
    try:
        response = c.receive()
        #print(response)
        response_list = response[1]
        global head
        head = calcAcctPositionReceive(response_list[0])
    except Exception as e:
        updateDirections("Exception encountered reading\r\nreturn value from pyReadHead:\r\n" + str(e))
        head = 0
    global position
    position = head
    c.send("pyGetAccountCount")
    response = c.receive()
    #print(response)
    global acctCount
    global selection
    try:
        response_list = response[1]
        acctCount = calcAcctPositionReceive(response_list[0])
    except TypeError as te:
        updateDirections("TypeError encountered in clickedOpen():\r\n" + str(te))
        acctCount = 0
    if (acctCount > 0):
        loadListBox()
        selection = 0
        getRecord()
        lb.select_set(selection)
        lb.see(selection)
        lb.activate(selection)
    cb.config(state='disabled')
    btn_open.config(state='disabled')
    #btn_close.config(state='normal')
    btn_next.config(state='normal')
    btn_previous.config(state='normal')
    btn_insert.config(state='normal')
    btn_delete.config(state='normal')
    btn_generate.config(state='normal')
    btn_powned.config(state='normal')
    btn_flip_pw.config(state='normal')
    menubar.entryconfig('File', state='normal')
    menubar.entryconfig('Backup/Restore', state='normal')
    menubar.entryconfig('Settings', state='normal')
    window.config(cursor="")
    updateDirections("Opened port")

    ReadGroupNames()

    textboxWork.config(text=groupName1)
    textboxPersonal.config(text=groupName2)
    textboxHome.config(text=groupName3)
    textboxSchool.config(text=groupName4)
    textboxFinancial.config(text=groupName5)
    textboxMail.config(text=groupName6)
    textboxCustom.config(text=groupName7)

    groupsMenu.entryconfigure(1, label = groupName1)
    groupsMenu.entryconfigure(2, label = groupName2)
    groupsMenu.entryconfigure(3, label = groupName3)
    groupsMenu.entryconfigure(4, label = groupName4)
    groupsMenu.entryconfigure(5, label = groupName5)
    groupsMenu.entryconfigure(6, label = groupName6)
    groupsMenu.entryconfigure(7, label = groupName7)

def updateDirections(directions):
    txt_dir.delete('1.0', END)
    txt_dir.insert(END, directions)
    #print (directions)
    window.update()

def clickedAcctParam(txt_acct_param):
    clickedAcct()

def clickedAcct():
    window.config(cursor="watch")                                              # TODO: this is not working
    window.update()
    aResAcct = stripBadChars(txt_acct.get())
    resAcct = aResAcct[0:32]
    global position                                                            # the position on EEprom, don't confuse with selection
    global state
    global selection
    if (len(resAcct) > 0):                                                     # if the URL doesn't exist don't send it
        c.send("pyUpdateAccountName", resAcct)                                 # FindAccountPos called on an insert
        try:
            response = c.receive()
            #print(response)
            response_list = response[1]
            last_position = position
            position = calcAcctPositionReceive(response_list[0])               # this position may or may not be populated)
            if position == 255:
                position = last_position                                       # TODO: not sure if this is necessary...
            local_position = position
            #txt_acct.config(state='normal')

    #      if (state == "Inserting"):
            if (state != "Importing"):
                lb.delete(0, END)
                loadListBox()                                                  # as a side effect position is changed
                selection = 0
                for key in accountDict:
                    if accountDict[key] != local_position:
                        selection += 1
                    else:
                        break
                lb.select_set(selection)
                lb.see(selection)
                lb.activate(selection)
                position = local_position                                       # because loadListBox changes position
                getRecord()
                updateDirections("Updated account name.")
        except ValueError as e:
            updateDirections("Value error encountered in\r\nclickedAcct:\r\n" + str(e))
        except Exception as ex:
            updateDirections("Exception encountered in\r\nclickedAcct:\r\n" + str(ex))
    else:
        updateDirections("Empty account name discarded.")
    window.config(cursor="")
    window.update()

def clickedUserParam(txt_user_param):
    clickedUser()

def clickedUser():
    global position
    aResUser = stripBadChars(txt_user.get())
    resUser = aResUser[0:32]
    if (len(resUser) > 0):
        c.send("pyUpdateUserName", calcAcctPositionSend(position), resUser)
    else:
        c.send("pyUpdateUserName", calcAcctPositionSend(position), "")
    response = c.receive()
    #print(response)
    response_list = response[1]
    position = calcAcctPositionReceive(response_list[0])
    txt_user.config(state='normal')
    directions = """Updated user name."""
    updateDirections(directions)
    window.update()

def clickedPassParam(txt_pass_param):
    clickedPass()

def clickedPass():
    global position
    aResPass = stripBadChars(txt_pass.get())
    resPass = aResPass[0:32]
    if (len(resPass) > 0):
        c.send("pyUpdatePassword", calcAcctPositionSend(position), resPass)
    else:
        c.send("pyUpdatePassword", calcAcctPositionSend(position), "")
    response = c.receive()
    #print(response)
    response_list = response[1]
    position = calcAcctPositionReceive(response_list[0])
    txt_pass.config(state='normal')
    directions = """Updated password."""
    updateDirections(directions)
    window.update()
    passesComplexityCheck = passwordComplexityCheck(aResPass)

def clickedOldPassParam(txt_old_pass_param):
    clickedOldPass()

def clickedOldPass():
    global position
    aResOldPass = stripBadChars(txt_old_pass.get())
    resOldPass = aResOldPass[0:32]
    if (len(resOldPass) > 0):
        c.send("pyUpdateOldPassword", calcAcctPositionSend(position), resOldPass)
    else:
        c.send("pyUpdateOldPassword", calcAcctPositionSend(position), "")
    response = c.receive()
    #print(response)
    response_list = response[1]
    position = calcAcctPositionReceive(response_list[0])
    txt_old_pass.config(state='normal')
    directions = """Updated old password."""
    updateDirections(directions)
    window.update()

def clickedStyle():
    global position
    resStyle = cbStyle.current()
    if ((resStyle != 0) and (resStyle != 1)):                                  # style must be 0 or 1
        resStyle = 1;                                                          # default is 1
    c.send("pyUpdateStyle", calcAcctPositionSend(position), resStyle)
    response = c.receive()
    #print(response)
    response_list = response[1]
    position = calcAcctPositionReceive(response_list[0])
    directions = """Updated style."""
    updateDirections(directions)
    window.update()

def updateGroup():
    global position
    global group
    c.send("pyUpdateGroup", calcAcctPositionSend(position), group + 3)
    response = c.receive()
    #print(response)
    response_list = response[1]
    position = calcAcctPositionReceive(response_list[0])
    directions = """Updated groups."""
    updateDirections(directions)
    window.update()

def clickedUrlParam(txt_url_param):
    clickedUrl_New()

def clickedUrl():
    global position
    aURL = stripBadChars(txt_url.get())
    resURL = aURL[0:32]                                                        # max length of a URL is 96 chars
    txt_url.config(state='normal')
    if (len(resURL) > 0):                                                      # if the URL doesn't exist don't send it
        c.send("pyUpdateURL", calcAcctPositionSend(position), resURL)
    else:
        c.send("pyUpdateURL", calcAcctPositionSend(position), "")
    response = c.receive()
    #print(response)
    response_list = response[1]
    position = calcAcctPositionReceive(response_list[0])
    txt_url.config(state='normal')
    directions = """Updated URL."""
    updateDirections(directions)
    window.update()

def clickedUrl_New():                                                          # send the website over in 3 chunks instead of all at once to circumvent problems encountered when sending it all at once.
    txt_url.config(state='normal')
    global position
    aURL = stripBadChars(txt_url.get())
    resURL_1 = aURL[0:32]                                                      # max length of a URL is 96 chars
    if (len(resURL_1) > 0):                                                    # if the URL doesn't exist don't send it
        c.send("pyUpdateURL_1", resURL_1)
        response = c.receive()
        #print(response)
        response_list = response[1]
        position = calcAcctPositionReceive(response_list[0])
        resURL_2 = aURL[32:64]                                                 # max length of a URL is 96 chars
        if (len(resURL_2) > 0):                                                # if the URL doesn't exist don't send it
            c.send("pyUpdateURL_2", resURL_2)
            response = c.receive()
            #print(response)
            response_list = response[1]
            position = calcAcctPositionReceive(response_list[0])
            resURL_3 = aURL[64:96]                                             # max length of a URL is 96 chars
            if (len(resURL_3) > 0):                                            # if the URL doesn't exist don't send it
                c.send("pyUpdateURL_3", calcAcctPositionSend(position), resURL_3)
                response = c.receive()
                #print(response)
                response_list = response[1]
                position = calcAcctPositionReceive(response_list[0])
            else:
                c.send("pyUpdateURL_3", calcAcctPositionSend(position), "")
                response = c.receive()
                #print(response)
                response_list = response[1]
                position = calcAcctPositionReceive(response_list[0])
        else:
            c.send("pyUpdateURL", calcAcctPositionSend(position), aURL)
            response = c.receive()
            #print(response)
            response_list = response[1]
            position = calcAcctPositionReceive(response_list[0])
    else:
        c.send("pyUpdateURL", calcAcctPositionSend(position), "")
        response = c.receive()
        #print(response)
        response_list = response[1]
        position = calcAcctPositionReceive(response_list[0])
    txt_url.config(state='normal')
    directions = """Updated URL."""
    updateDirections(directions)
    window.update()

def clickedClose():
    global arduinoAttached
    if (arduinoAttached == 1):
        try:
            c.send("pyExit")
            response = c.receive()
            #print(response)
            response_list = response[1]
            acctCount = calcAcctPositionReceive(response_list[0])              # not used
        except Exception as e:
            updateDirections("There was an error closing the\r\napplication:\r\n" + str(e))
    sys.exit(1)

def clickedPrevious():
    global position
    global selection
    #if (selection > 0):
    #    selection -= 1
    c.send("pyGetPrevPos", calcAcctPositionSend(position))
    response = c.receive()
    #print(response)
    response_list = response[1]
    last_position = position
    position = calcAcctPositionReceive(response_list[0])
    if position == 255:
        position = last_position
        updateDirections("Reached the beginning of the\r\nlist.")
    else:
        items = lb.curselection()
        selection = items[0]
        OnEntryUpNoEvent()
        lb.activate(selection)                                                 # has no effect
        #updateDirections("Navigated to previous record.")

def clickedNext():
    global position
    global selection
    c.send("pyGetNextPos", calcAcctPositionSend(position))
    response = c.receive()
    #print(response)
    response_list = response[1]
    last_position = position
    position = calcAcctPositionReceive(response_list[0])                       # used when we call OnEntryDownNoEvent->OnEntryDown->clickedLoad->getRecord
    if position == 255:
        position = last_position
        updateDirections("Reached the end of the list.")
    else:
        items = lb.curselection()                                              # Gets a list of the currently selected alternatives.
        selection = items[0]
        OnEntryDownNoEvent()
        lb.activate(selection)                                                 # has no effect
        #updateDirections("Navigated to next record.")

def loadListBox():                                                             # TODO: reorganize the logic in this function
    window.config(cursor="watch")                                              # TODO: this is not working
    window.update()
    lb.delete(0,END)                                                           # clear out the listbox
    global position
    global head
    c.send("pyReadHead")                                                       # Get the list head
    try:
        response = c.receive()
        #print(response)
        response_list = response[1]
        head = calcAcctPositionReceive(response_list[0])
        position = head
        global accountDict
        accountDict = ({})                                                     # Load the dictionary
        while position < 255:                                                  # '<' not supported between instances of 'str' and 'int'
            c.send("pyReadAccountName", calcAcctPositionSend(position))
            try:
                response = c.receive()
                accountName_list = response[1]
                accountName = accountName_list[0]
            except UnicodeDecodeError as e:
                updateDirections("UnicodeDecodeError in\r\npyReadAccountName:\r\n" + str(e))
                accountName = "UnicodeDecodeError"
            except ValueError as ve:
                updateDirections("ValueError in\r\npyReadAccountName:\r\n" + str(ve))
                accountName = "ValueError"
            except Exception as e:
                updateDirections("Exception in\r\npyReadAccountName:\r\n" + str(e))
                accountName = "Exception"
            accountDict[accountName] = position
            lb.insert(END, accountName)                                        # Load the listbox
            c.send("pyGetNextPos", calcAcctPositionSend(position))             # calls getNextPtr(acctPosition) in C program
            try:
                response = c.receive()
                response_list = response[1]
                position = calcAcctPositionReceive(response_list[0])
            except ValueError as ve:
                updateDirections("Error in pyGetNextPos:\r\n" + str(ve))
                raise ve
            except Exception as e:
                updateDirections("Exception in pyGetNextPos:\r\n" + str(e))
                raise e
        position = head
        window.config(cursor="")
        window.update()
    except ValueError as ve:
        updateDirections("ValueError in pyReadHead,\r\npyReadAccountName or\r\npyGetNextPos:\r\n" + str(ve))
        head = 0
    except Exception as e:
        updateDirections("Exception in pyReadHead,\r\npyReadAccountName or\r\npyGetNextPos:\r\n" + str(e))
        head = 0

def ReadGroupNames():
    global groupName1
    global groupName2
    global groupName3
    global groupName4
    global groupName5
    global groupName6
    global groupName7
    try:
        c.send("pyReadGroup1Name")
        response = c.receive()
        groupName_list = response[1]
        groupName1 = groupName_list[0]

        c.send("pyReadGroup2Name")
        response = c.receive()
        groupName_list = response[1]
        groupName2 = groupName_list[0]

        c.send("pyReadGroup3Name")
        response = c.receive()
        groupName_list = response[1]
        groupName3 = groupName_list[0]

        c.send("pyReadGroup4Name")
        response = c.receive()
        groupName_list = response[1]
        groupName4 = groupName_list[0]

        c.send("pyReadGroup5Name")
        response = c.receive()
        groupName_list = response[1]
        groupName5 = groupName_list[0]

        c.send("pyReadGroup6Name")
        response = c.receive()
        groupName_list = response[1]
        groupName6 = groupName_list[0]

        c.send("pyReadGroup7Name")
        response = c.receive()
        groupName_list = response[1]
        groupName7 = groupName_list[0]

    except UnicodeDecodeError as e:
        updateDirections("UnicodeDecodeError in\r\npyReadGroup1Name:\r\n" + str(e))
        groupName1 = "UnicodeDecodeError"
    except ValueError as ve:
        updateDirections("ValueError in\r\npyReadGroupName:\r\n" + str(ve))
        groupName1 = "ValueError"
    except Exception as e:
        updateDirections("Exception in\r\npyReadGroupName:\r\n" + str(e))
        groupName1 = "Exception"


def OnEntryDownNoEvent():
    OnEntryDown(0)

def OnEntryDown(event):
    global selection
    if selection < lb.size()-1:
        lb.select_clear(selection)                                             # Removes one or more items from the selection.
        selection += 1
        lb.select_set(selection)                                               # Adds one or more items to the selection.
        lb.see(selection)                                                      # Makes sure the given list index is visible.
        clickedLoad()                                                          # calls getRecord()

def OnEntryUpNoEvent():
    OnEntryUp(0)

def OnEntryUp(event):
    global selection
    if selection > 0:
        lb.select_clear(selection)                                             # Removes one or more items from the selection.
        selection -= 1
        lb.select_set(selection)                                               # Adds one or more items to the selection.
        lb.see(selection)                                                      # Makes sure the given list index is visible.
        clickedLoad()                                                          # calls getRecord()

def clickedInsert():
    global state
    state = "Inserting"

    txt_acct.bind("<FocusOut>",(lambda _: doNothing(txt_acct)))                # When the user clicks off of the field do nothing
    txt_user.bind("<FocusOut>",(lambda _: doNothing(txt_user)))
    txt_pass.bind("<FocusOut>",(lambda _: doNothing(txt_pass)))
    txt_old_pass.bind("<FocusOut>",(lambda _: doNothing(txt_old_pass)))
    txt_url.bind("<FocusOut>",(lambda _: doNothing(txt_url)))

    #txt_acct.config(state='normal')
    txt_acct.delete(0, END)
    txt_user.delete(0, END)
    txt_pass.delete(0, END)
    txt_old_pass.delete(0, END)
    txt_url.delete(0, END)

    txt_acct.focus_set()                                                       # Put input focus on the account field

    txt_acct.bind("<FocusOut>",(lambda _: clickedAcctParam(txt_acct)))         # When the clicks off of the field save the edited item
    txt_user.bind("<FocusOut>",(lambda _: clickedUserParam(txt_user)))
    txt_pass.bind("<FocusOut>",(lambda _: clickedPassParam(txt_pass)))
    txt_old_pass.bind("<FocusOut>",(lambda _: clickedOldPassParam(txt_old_pass)))
    txt_url.bind("<FocusOut>",(lambda _: clickedUrlParam(txt_url)))

def doNothing(txt_param):
    x = 0                                                                      # do nothing

def clickedLoadDB(event):
    global selection
    w = event.widget                                                           # Note here that Tkinter passes an event object to onselect()
    selection = int(w.curselection()[0])
    value = w.get(selection)
    updateDirections('You selected item %d: "%s"' % (selection, value))
    clickedLoad()                                                              # calls getRecord()

def clickedLoad():
    global position
    global accountDict
    item = lb.curselection()
    global selection
    selection = item[0]
    theText = lb.get(item)
    position = accountDict[theText]
    getRecord()

def clickedDelete():
    if tkinter.messagebox.askyesno("Delete", "Delete this record?"):
        global selection
        lb.delete(selection)
        global position
        c.send("pyDeleteAccount",calcAcctPositionSend(position))
        response = c.receive()
        #print(response)
        response_list = response[1]
        position = calcAcctPositionReceive(response_list[0])                   # returns head position
        getRecord()
        selection = 0
        lb.select_set(selection)
        lb.see(selection)
        lb.activate(selection)
        updateDirections("Record deleted.")

def clickedChangeMasterPass():
    newMasterPass = tkinter.simpledialog.askstring("Change Master Password", "New Master Password")
    if newMasterPass is not None:
        window.config(cursor="watch")
        window.update();
        c.send("pyChangeMasterPass", newMasterPass)
        response = c.receive()
        #print(response)
        response_list = response[1]
        position = calcAcctPositionReceive(response_list[0])                   # returns head position
        getRecord()
        selection = 0
        lb.select_set(selection)
        lb.see(selection)
        lb.activate(selection)
        window.config(cursor="")
        updateDirections("Master password changed.")

def clickedShowPassword():
    yes = tkinter.messagebox.askyesno("Show Password", "Do you want to see the password on the PasswordPump?")
    if yes:
        c.send("pyShowPasswords", 1)
        response = c.receive()
        #print(response)
        response_list = response[1]
        unusedHead = calcAcctPositionReceive(response_list[0])                 # returns head position
        updateDirections("Turned on password viewing on\r\nthe PasswordPump.")
    else:
        c.send("pyShowPasswords", 0)
        response = c.receive()
        #print(response)
        response_list = response[1]
        unusedHead = calcAcctPositionReceive(response_list[0])                 # returns head position
        updateDirections("Turned off password viewing on\r\nthe PasswordPump.")

def clickedDecoyPassword():
    yes = tkinter.messagebox.askyesno("Decoy Password", "Do you want to enable the decoy password feature?")
    if yes:
        c.send("pyDecoyPassword", 1)
        response = c.receive()
        #print(response)
        response_list = response[1]
        unusedHead = calcAcctPositionReceive(response_list[0])                 # returns head position
        updateDirections("Enabled the decoy password\r\nfeature on the PasswordPump")
    else:
        c.send("pyDecoyPassword", 0)
        response = c.receive()
        #print(response)
        response_list = response[1]
        unusedHead = calcAcctPositionReceive(response_list[0])                 # returns head position
        updateDirections("Disabled the decoy password\r\nfeature on the PasswordPump")

def getRecord():
    global position
    global group
    global vFavorites
    global vWork
    global vPersonal
    global vHome
    global vSchool
    global vFinancial
    global vMail
    global vCustom
    c.send("pyReadAccountName", calcAcctPositionSend(position))
    try:
        response = c.receive()
        #print(response)
        accountName_list = response[1]
        accountName = accountName_list[0]
    except UnicodeDecodeError:
        accountName = ""
    txt_acct.delete(0,END)
    txt_acct.insert(0,accountName)

    c.send("pyReadUserName", calcAcctPositionSend(position))
    try:
        response = c.receive()
        #print (response)
        userName_list = response[1]
        userName = userName_list[0]
    except UnicodeDecodeError:
        userName = ""
    txt_user.delete(0,END)
    txt_user.insert(0,userName)

    c.send("pyReadPassword", calcAcctPositionSend(position))
    try:
        response = c.receive()
        #print(response)
        password_list = response[1]
        password = password_list[0]
    except UnicodeDecodeError:
        password = ""
    txt_pass.delete(0,END)
    txt_pass.insert(0,password)
    passesComplexityCheck = passwordComplexityCheck(password)

    c.send("pyReadOldPassword", calcAcctPositionSend(position))
    try:
        response = c.receive()
        #print(response)
        old_password_list = response[1]
        old_password = old_password_list[0]
    except UnicodeDecodeError:
        old_password = ""
    txt_old_pass.delete(0,END)
    txt_old_pass.insert(0,old_password)

    c.send("pyReadStyle", calcAcctPositionSend(position))
    try:
        response = c.receive()
        #print(response)
        style_list = response[1]
        style = int(style_list[0])
    except ValueError:                                                          # when style = 255 (i.e. was never written)
        style = 1
    except UnicodeDecodeError:
        style = 1
    cbStyle.current(style)

    c.send("pyReadURL", calcAcctPositionSend(position))
    try:
        response = c.receive()
        #print(response)
        url_list = response[1]
        url = url_list[0]
    except UnicodeDecodeError:
        url = ""
    txt_url.delete(0,END)
    txt_url.insert(0,url)

    c.send("pyReadGroup", calcAcctPositionSend(position))
    try:
        response = c.receive()
        #print(response)
        group_list = response[1]
        group = int(group_list[0])
    except UnicodeDecodeError as ude:
        updateDirections("UnicodeDecodeError during pyReadGroup in getRecord(); " + str(ude))
        group = 0
    except Exception as e:
        updateDirections("Exception encountered after pyReadGroup in getRecord(); Group: " + str(group) + " " + str(e))
        group = 0
    SetGroupCheckBoxes()

def serial_ports():
    return comports()

def on_select(event=None):
    global port
    port_desc = cb.get()
    updateDirections(port_desc)
    port = port_desc[:port_desc.find(":")]                                     # TODO: make this work on all operating systems

def on_style_select(event=None):
    clickedStyle()

def BackupEEprom():
    if tkinter.messagebox.askyesno("Backup", "Backup the primary EEprom?"):
        window.config(cursor="watch")
        updateDirections("Backing up EEprom")
        global selection
        global position
        c.send("pyBackup")
        response = c.receive()
        #print(response)
        response_list = response[1]
        position = calcAcctPositionReceive(response_list[0])                   # returns head position
        getRecord()
        lb.select_clear(selection)                                             # Removes one or more items from the selection.
        selection = 0
        lb.select_set(selection)
        lb.see(selection)
        lb.activate(selection)
        window.config(cursor="")
        updateDirections("Finished backing up EEprom.")

def FactoryReset():
    if tkinter.messagebox.askyesno("Factory Reset", "Factory reset the device and exit?"):
        window.config(cursor="watch")
        updateDirections("Factory resetting...")
        global selection
        global position
        c.send("pyFactoryReset")
        response = c.receive()
        #print(response)
        response_list = response[1]
        position = calcAcctPositionReceive(response_list[0])                   # returns head position
        updateDirections("Finished the factory reset.")
        sys.exit(1)

def RestoreEEprom():
    if tkinter.messagebox.askyesno("Restore", "Restore backup to primary EEprom?"):
        window.config(cursor="watch")
        updateDirections("Restoring EEprom")
        global selection
        global position
        c.send("pyRestore")
        response = c.receive()
        #print(response)
        response_list = response[1]
        position = calcAcctPositionReceive(response_list[0])                   # returns head position
        loadListBox()                                                          # postion is set to head as a side effect
        getRecord()                                                            # get the head record
        lb.select_clear(selection)                                             # Removes one or more items from the selection.
        selection = 0
        lb.select_set(selection)
        lb.see(selection)
        lb.activate(selection)
        window.config(cursor="")
        updateDirections("Finished restoring EEprom.")

def ImportFileChrome():
    global state
    state = "Imorting"
    if (platform.system() == "Windows"):
        name = askopenfilename(initialdir="C:/",                               # TODO: make this work cross platform
                               filetypes =(("CSV File", "*.csv"),("All Files","*.*")),
                               title = "Choose a file."
                              )
    elif (platform.system() == "Darwin"):                                      # Macintosh
        name = askopenfilename(title = "Choose a file."
                              )
    elif (platform.system() == "Linux"):                                       # Linux
        name = askopenfilename(title = "Choose a file."
                              )
    else:
        name = askopenfilename(title = "Choose a file."
                              )
    window.config(cursor="watch")
    updateDirections(name)
    global position
    try:                                                                       # Using try in case user types in unknown file or closes without choosing a file.
        with open(name, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            try:
                for row in reader:
                    txt_acct.delete(0, END)
                    txt_user.delete(0, END)
                    txt_pass.delete(0, END)
                    txt_url.delete(0, END)
                    txt_acct.insert(0,stripBadChars(row['name']))
                    txt_user.insert(0,stripBadChars(row['username']))
                    txt_pass.insert(0,stripBadChars(row['password']))
                    txt_url.insert(0,stripBadChars(row['url']))
                    window.update()
                    time.sleep(0.15)                                           # to eliminate intermittent failure
                    clickedAcct()                                              # sets position = FindAccountPos()
                    time.sleep(0.15)                                           # to eliminate intermittent failure
                    clickedUser()
                    time.sleep(0.15)                                           # to eliminate intermittent failure
                    clickedPass()
                    time.sleep(0.15)                                           # to eliminate intermittent failure
                    clickedStyle()
                    time.sleep(0.15)                                           # to eliminate intermittent failure
                    clickedUrl_New()
                    updateDirections("Record saved.")
                updateDirections("All records saved.")
                loadListBox()
            except Exception as e:
                updateDirections("Error encountered reading file in ImportFileChrome; "+ str(e))
    except Exception as ex:
        updateDirections("Error encountered in ImportFileChrome; " + str(ex))
    window.config(cursor="")
    window.update()
    state = "None"

def ImportFilePasswordPump():
    global state
    state = "Importing"
    if (platform.system() == "Windows"):
        name = askopenfilename(initialdir="C:/",                               # TODO: make this work cross platform
                               filetypes =(("CSV File", "*.csv"),("All Files","*.*")),
                               title = "Choose a file."
                              )
    elif (platform.system() == "Darwin"):                                      # Macintosh
        name = askopenfilename(title = "Choose a file."
                              )
    elif (platform.system() == "Linux"):                                       # Linux
        name = askopenfilename(title = "Choose a file."
                              )
    else:
        name = askopenfilename(title = "Choose a file."
                              )
    window.config(cursor="watch")
    updateDirections (name)
    global position
    global group
    try:                                                                       # Using try in case user types in unknown file or closes without choosing a file.
        with open(name, newline='') as csvfile:
            fieldnames = ['accountname', 'username', 'password', 'oldpassword', 'url', 'style', 'group']
            reader = csv.DictReader(csvfile, fieldnames=fieldnames)
            try:
                for row in reader:
                    txt_acct.delete(0, END)
                    txt_user.delete(0, END)
                    txt_pass.delete(0, END)
                    txt_old_pass.delete(0, END)
                    txt_url.delete(0, END)
                    txt_acct.insert(0,stripBadChars(row['accountname']))
                    if (txt_acct.get() != 'accountname'):                      # to skip the header if there is one
                        txt_user.insert(0,stripBadChars(row['username']))
                        txt_pass.insert(0,stripBadChars(row['password']))
                        txt_old_pass.insert(0,stripBadChars(row['oldpassword']))
                        txt_url.insert(0,stripBadChars(row['url']))
                        group = int(row['group'])
                        SetGroupCheckBoxes()
                        window.update()
                        time.sleep(0.15)                                       # to eliminate intermittent failure
                        clickedAcct()                                          # sets position = FindAccountPos()
                        time.sleep(0.15)                                       # to eliminate intermittent failure
                        clickedUser()
                        time.sleep(0.15)                                       # to eliminate intermittent failure
                        clickedPass()
                        time.sleep(0.15)                                       # to eliminate intermittent failure
                        clickedOldPass()
                        time.sleep(0.15)                                       # to eliminate intermittent failure
                        clickedStyle()
                        time.sleep(0.15)                                       # to eliminate intermittent failure
                        clickedUrl_New()
                        time.sleep(0.15)                                       # to eliminate intermittent failure
                        updateGroup()
                        updateDirections("Record saved.")
                updateDirections("All records saved.")
                loadListBox()
            except Exception as e:
                updateDirections("Error encountered reading file in ImportFilePasswordPump; "+ str(e))
    except Exception as ex:
        updateDirections("Error encountered in ImportFilePasswordPump; " + ex)
    window.config(cursor="")
    window.update()
    state = "None"

def ImportFileKeePass():
    global state
    state = "Importing"
    if (platform.system() == "Windows"):
        name = askopenfilename(initialdir="C:/",                               # TODO: make this work cross platform
                               filetypes =(("CSV File", "*.csv"),("All Files","*.*")),
                               title = "Choose a file."
                              )
    elif (platform.system() == "Darwin"):                                      # Macintosh
        name = askopenfilename(title = "Choose a file."
                              )
    elif (platform.system() == "Linux"):
        name = askopenfilename(title = "Choose a file."                        # Linux
                              )
    else:
        name = askopenfilename(title = "Choose a file."
                              )
    window.config(cursor="watch")
    updateDirections(name)
    global position
    try:                                                                       # Using try in case user types in unknown file or closes without choosing a file.
        with open(name, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            try:
                for row in reader:
                    txt_acct.delete(0, END)
                    txt_user.delete(0, END)
                    txt_pass.delete(0, END)
                    txt_url.delete(0, END)
                    txt_acct.insert(0,stripBadChars(row['Account']))
                    txt_user.insert(0,stripBadChars(row['Login Name']))
                    txt_pass.insert(0,stripBadChars(row['Password']))
                    txt_url.insert(0,stripBadChars(row['Web Site']))
                    window.update()
                    time.sleep(0.15)                                           # to eliminate intermittent failure
                    clickedAcct()                                              # sets position = FindAccountPos()
                    time.sleep(0.15)                                           # to eliminate intermittent failure
                    clickedUser()
                    time.sleep(0.15)                                           # to eliminate intermittent failure
                    clickedPass()
                    time.sleep(0.15)                                           # to eliminate intermittent failure
                    clickedStyle()
                    time.sleep(0.15)                                           # to eliminate intermittent failure
                    clickedUrl_New()
                    updateDirections("Record saved.")
                updateDirections("All records saved.")
                loadListBox()
            except Exception as e:
                updateDirections("Error encountered processing file in ImportFileKeePass; "+ str(e))
    except Exception as ex:
        updateDirections("Error encountered in ImportFileKeePass; " + str(ex))
    window.config(cursor="")
    window.update()
    state = "None"

def ExportFile():
    if (platform.system() == "Windows"):
        name = asksaveasfilename(initialdir="C:/",  # TODO: make this work cross platform
                                 filetypes=(("CSV File", "*.csv"), ("All Files", "*.*")),
                                 initialfile='PasswordPumpExport.csv',
                                 title="Create a file."
                                 )
    elif (platform.system() == "Darwin"):                                      # Macintosh
        name = asksaveasfilename(title="Create a file."
                                 )
    elif (platform.system() == "Linux"):                                       # Linux
        name = asksaveasfilename(initialdir="C:/",
                                 )
    else:
        name = asksaveasfilename(initialdir="C:/",
                                 )
    window.config(cursor="watch")
    updateDirections(name)
    try:                                                                       # Using try in case user types in unknown file or closes without choosing a file.
        with open(name, mode='w') as pp_file:
            pp_writer = csv.writer(pp_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_NONNUMERIC)
            pp_writer.writerow(['accountname', 'username', 'password', 'oldpassword', 'url', 'style', 'group'])
            global position
            global head
            c.send("pyReadHead")  # Get the list head
            try:
                response = c.receive()
                #print(response)
                response_list = response[1]
                head = calcAcctPositionReceive(response_list[0])
                position = head
                while position < 255:  # '<' not supported between instances of 'str' and 'int'
                    c.send("pyReadAccountName", calcAcctPositionSend(position))
                    try:
                        response = c.receive()
                        accountName_list = response[1]
                        accountName = stripBadChars(accountName_list[0])
                    except UnicodeDecodeError as e:
                        updateDirections("UnicodeDecodeError in pyReadAccountName; " + str(e))
                        accountName = "UnicodeDecodeError"
                    except ValueError as ve:
                        updateDirections("ValueError in pyReadAccountName; " + str(ve))
                        accountName = "ValueError"
                    except Exception as e:
                        updateDirections("Exception in pyReadAccountName; " + str(e))
                        accountName = "Exception"

                    c.send("pyReadUserName", calcAcctPositionSend(position))
                    try:
                        response = c.receive()
                        userName_list = response[1]
                        userName = stripBadChars(userName_list[0])
                    except UnicodeDecodeError as e:
                        updateDirections("UnicodeDecodeError in pyReadUserName; " + str(e))
                        userName = "UnicodeDecodeError"
                    except ValueError as ve:
                        updateDirections("ValueError in pyReadUserName; " + str(ve))
                        userName = "ValueError"
                    except Exception as e:
                        updateDirections("Exception in pyReadUserName; " + str(e))
                        userName = "Exception"

                    c.send("pyReadPassword", calcAcctPositionSend(position))
                    try:
                        response = c.receive()
                        password_list = response[1]
                        password = stripBadChars(password_list[0])
                    except UnicodeDecodeError as e:
                        updateDirections("UnicodeDecodeError in pyReadPassword; " + str(e))
                        password = "UnicodeDecodeError"
                    except ValueError as ve:
                        updateDirections("ValueError in pyReadPassword; " + str(ve))
                        password = "ValueError"
                    except Exception as e:
                        updateDirections("Exception in pyReadPassword; " + str(e))
                        password = "Exception"

                    c.send("pyReadOldPassword", calcAcctPositionSend(position))
                    try:
                        response = c.receive()
                        oldpassword_list = response[1]
                        oldpassword = stripBadChars(oldpassword_list[0])
                    except UnicodeDecodeError as e:
                        updateDirections("UnicodeDecodeError in pyReadOldPassword; " + str(e))
                        oldpassword = "UnicodeDecodeError"
                    except ValueError as ve:
                        updateDirections("ValueError in pyReadOldPassword; " + str(ve))
                        oldpassword = "ValueError"
                    except Exception as e:
                        updateDirections("Exception in pyReadOldPassword; " + str(e))
                        oldpassword = "Exception"

                    c.send("pyReadURL", calcAcctPositionSend(position))
                    try:
                        response = c.receive()
                        url_list = response[1]
                        url = stripBadChars(url_list[0])
                    except UnicodeDecodeError as e:
                        updateDirections("UnicodeDecodeError in pyReadURL; " + str(e))
                        url = "UnicodeDecodeError"
                    except ValueError as ve:
                        updateDirections("ValueError in pyReadURL; " + str(ve))
                        url = "ValueError"
                    except Exception as e:
                        updateDirections("Exception in pyReadURL; " + str(e))
                        url = "Exception"

                    c.send("pyReadStyle", calcAcctPositionSend(position))
                    try:
                        response = c.receive()
                        style_list = response[1]
                        style = int(stripBadChars(style_list[0]))
                    except UnicodeDecodeError as e:
                        updateDirections("UnicodeDecodeError in pyReadStyle; " + str(e))
                        style = 1
                    except ValueError as ve:
                        updateDirections("ValueError in pyReadStyle; " + str(ve))
                        style = 1
                    except Exception as e:
                        updateDirections("Exception in pyReadStyle; " + str(e))
                        style = 1

                    c.send("pyReadGroup", calcAcctPositionSend(position))
                    try:
                        response = c.receive()
                        group_list = response[1]
                        group = group_list[0]
                    except UnicodeDecodeError as e:
                        updateDirections("UnicodeDecodeError in pyReadGroup; " + str(e))
                        group = 0
                    except ValueError as ve:
                        updateDirections("ValueError in pyReadGroup; " + str(ve))
                        group = 0
                    except Exception as e:
                        updateDirections("Exception in pyReadGroup; " + str(e))
                        group = 0

                    pp_writer.writerow([accountName, userName, password, oldpassword, url, style, group])

                    c.send("pyGetNextPos", calcAcctPositionSend(position))  # calls getNextPtr(acctPosition) in C program
                    try:
                        response = c.receive()
                        response_list = response[1]
                        position = calcAcctPositionReceive(response_list[0])
                    except ValueError as ve:
                        updateDirections("Error in pyGetNextPos; " + str(ve))
                        raise ve
                    except Exception as e:
                        updateDirections("Exception in pyGetNextPos; " + str(e))
                        raise e
            except ValueError as ve:
                updateDirections("ValueError in pyReadHead, pyReadAccountName or pyGetNextPos; " + str(ve))
                head = 0
            except Exception as e:
                updateDirections("Exception in pyReadHead, pyReadAccountName or pyGetNextPos; " + str(e))
                head = 0
    except:
        updateDirections("No file exists")
    window.config(cursor="")
    window.update()

def OnFavorites():
    global group
    global vFavorites
    if (vFavorites.get() == 1):
        group = group | 1
    else:
        group = group & (~1)
    updateGroup()

def OnWork():
    global group
    global vWork
    if (vWork.get() == 1):
        group = group | 2
    else:
        group = group & (~2)
    updateGroup()

def OnPersonal():
    global group
    global vPersonal
    if (vPersonal.get() == 1):
        group = group | 4
    else:
        group = group & (~4)
    updateGroup()

def OnHome():
    global group
    global vHome
    if (vHome.get() == 1):
        group = group | 8
    else:
        group = group & (~8)
    updateGroup()

def OnSchool():
    global group
    global vSchool
    if (vSchool.get() == 1):
        group = group | 16
    else:
        group = group & (~16)
    updateGroup()

def OnFinancial():
    global group
    global vFinancial
    if (vFinancial.get() == 1):
        group = group | 32
    else:
        group = group & (~32)
    updateGroup()

def OnMail():
    global group
    global vMail
    if (vMail.get() == 1):
        group = group | 64
    else:
        group = group & (~64)
    updateGroup()

def OnCustom():
    global group
    global vCustom
    if (vCustom.get() == 1):
        group = group | 128
    else:
        group = group & (~128)
    updateGroup()

def generatePassword():
    currentOldPass = txt_old_pass.get()
    if (len(currentOldPass) == 0):
        previousPass = txt_pass.get()
        txt_old_pass.delete(0, END)
        txt_old_pass.insert(END, previousPass)
        txt_old_pass.focus()
    characters = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!#$%*()?-_=+:;{}[]" # These chars are not generated on the PasswordPump:  , " @ ` \ & ~ | \\ ^ /
    while True:                                                                # emulate a do while loop in python
        password = "".join(choice(characters) for x in range(31))              # generate passwords until one passes
        if passwordComplexityCheck(password):                                  # the complexity check.
            break
    txt_pass.delete(0, END)
    txt_pass.insert(END, password)
    txt_pass.focus()                                                           # to save the old password
    txt_old_pass.focus()                                                       # to save the password

def checkIfPowned():
    currentPass = txt_pass.get()
    if (len(currentPass) != 0):
        pownedCnt = powned.check(currentPass);
        if (pownedCnt):
            tkinter.messagebox.showinfo('Bad News', 'This password has been seen '+ str(pownedCnt) +' times before.  Do not use it.')
            updateDirections("This password has been recovered in a data breach.  Do not use it.")
        else:
            tkinter.messagebox.showinfo('Good News', 'This password has not been recovered in any data breaches.')
            updateDirections("This password has not been recovered in any data breach.")
        window.update();


# Function to validate the password
def passwordComplexityCheck(passwd):
    # !#$%*()-_+={}[]:;.<>?@
    specialSym = ['!','#','$','%','*','(',')','-','_','+','=','{','}','[',']',':',';','.','<','>','?','@']
    # ,"`\/&~|^
    badSym = [',','"','`','\\','/','&','~','|','^']
    val = True
    rejectReason = 'Password fails complexity\r\ncheck:\r\n'

    if len(passwd) > 31:
        rejectReason += 'The password length should be\r\nnot be greater than 31.\r\n'
        val = False

    if len(passwd) < 10:
        rejectReason += 'The password length should be\r\nat least 10.\r\n'
        val = False

    if not any(char.isdigit() for char in passwd):
        rejectReason += 'The password should have at\r\nleast one numeral.\r\n'
        val = False

    if not any(char.isupper() for char in passwd):
        rejectReason += 'The password should have at\r\nleast one uppercase letter.\r\n'
        val = False

    if not any(char.islower() for char in passwd):
        rejectReason += 'The password should have at\r\nleast one lowercase letter.\r\n'
        val = False

    if  any(char in badSym for char in passwd):
        rejectReason += 'The password has a forbidden\r\nsymbol: ,"`\/&~|^ \r\n'
        val = False

    if not any(char in specialSym for char in passwd):
        rejectReason += 'The password should have at\r\nleast one of these symbols:\r\n!#$%*()-_+={}[]:;.<>?'
        val = False

    if not val:
        updateDirections(rejectReason)
        txt_pass.config({"foreground": "red"})
    else:
        updateDirections('Password passes complexity\r\nvalidation.')
        txt_pass.config({"foreground": "black"})

    window.update()
    return val

def flipPassword():
    global showPassword
    if (showPassword):
        showPassword = False
        txt_pass.config(show="*")
    else:
        showPassword = True
        txt_pass.config(show="")
    window.update()

def SetGroupCheckBoxes():
    global vFavorites
    global vWork
    global vPersonal
    global vHome
    global vSchool
    global vFinancial
    global vMail
    global vCustom
    if ((group & 1) == 1):
        vFavorites.set(1)
    else:
        vFavorites.set(0)
    if ((group & 2) == 2):
        vWork.set(1)
    else:
        vWork.set(0)
    if ((group & 4) == 4):
        vPersonal.set(1)
    else:
        vPersonal.set(0)
    if ((group & 8) == 8):
        vHome.set(1)
    else:
        vHome.set(0)
    if ((group & 16) == 16):
        vSchool.set(1)
    else:
        vSchool.set(0)
    if ((group & 32) == 32):
        vFinancial.set(1)
    else:
        vFinancial.set(0)
    if ((group & 64) == 64):
        vMail.set(1)
    else:
        vMail.set(0)
    if ((group & 128) == 128):
        vCustom.set(1)
    else:
        vCustom.set(0)
    window.update()

def customizeGroup1():
    global groupName1
    groupNameTemp = groupName1
    groupName1 = tkinter.simpledialog.askstring("Customize Group", "Customize Group " + groupName1)
    if not groupName1:
        groupName1 = groupNameTemp
    c.send("pyUpdateCategoryName", 1, groupName1)
    response = c.receive()
    # print(response)
    response_list = response[1]
    position = calcAcctPositionReceive(response_list[0])  # returns head position
    textboxWork.config(text=groupName1)
    groupsMenu.entryconfigure(1, label = groupName1)

def customizeGroup2():
    global groupName2
    groupNameTemp = groupName2
    groupName2 = tkinter.simpledialog.askstring("Customize Group", "Customize Group " + groupName2)
    if not groupName2:
        groupName2 = groupNameTemp
    c.send("pyUpdateCategoryName", 2, groupName2)
    response = c.receive()
    # print(response)
    response_list = response[1]
    position = calcAcctPositionReceive(response_list[0])  # returns head position
    textboxPersonal.config(text=groupName2)
    groupsMenu.entryconfigure(2, label = groupName2)

def customizeGroup3():
    global groupName3
    groupNameTemp = groupName3
    groupName3 = tkinter.simpledialog.askstring("Customize Group", "Customize Group " + groupName3)
    if not groupName3:
        groupName3 = groupNameTemp
    c.send("pyUpdateCategoryName", 3, groupName3)
    response = c.receive()
    # print(response)
    response_list = response[1]
    position = calcAcctPositionReceive(response_list[0])  # returns head position
    textboxHome.config(text=groupName3)
    groupsMenu.entryconfigure(3, label = groupName3)

def customizeGroup4():
    global groupName4
    groupNameTemp = groupName4
    groupName4 = tkinter.simpledialog.askstring("Customize Group", "Customize Group " + groupName4)
    if not groupName4:
        groupName4 = groupNameTemp
    c.send("pyUpdateCategoryName", 4, groupName4)
    response = c.receive()
    # print(response)
    response_list = response[1]
    position = calcAcctPositionReceive(response_list[0])  # returns head position
    textboxSchool.config(text=groupName4)
    groupsMenu.entryconfigure(4, label = groupName4)

def customizeGroup5():
    global groupName5
    groupNameTemp = groupName5
    groupName5 = tkinter.simpledialog.askstring("Customize Group", "Customize Group " + groupName5)
    if not groupName5:
        groupName5 = groupNameTemp
    c.send("pyUpdateCategoryName", 5, groupName5)
    response = c.receive()
    # print(response)
    response_list = response[1]
    position = calcAcctPositionReceive(response_list[0])  # returns head position
    textboxFinancial.config(text=groupName5)
    groupsMenu.entryconfigure(5, label = groupName5)

def customizeGroup6():
    global groupName6
    groupNameTemp = groupName6
    groupName6 = tkinter.simpledialog.askstring("Customize Group", "Customize Group " + groupName6)
    if not groupName6:
        groupName6 = groupNameTemp
    c.send("pyUpdateCategoryName", 6, groupName6)
    response = c.receive()
    # print(response)
    response_list = response[1]
    position = calcAcctPositionReceive(response_list[0])  # returns head position
    textboxMail.config(text=groupName6)
    groupsMenu.entryconfigure(6, label = groupName6)

def customizeGroup7():
    global groupName7
    groupNameTemp = groupName7
    groupName7 = tkinter.simpledialog.askstring("Customize Group", "Customize Group " + groupName7)
    if not groupName7:
        groupName7 = groupNameTemp
    c.send("pyUpdateCategoryName", 7, groupName7)
    response = c.receive()
    # print(response)
    response_list = response[1]
    position = calcAcctPositionReceive(response_list[0])  # returns head position
    textboxCustom.config(text=groupName7)
    groupsMenu.entryconfig(7, label = groupName7)

txt_acct = Entry(window, width=40)
txt_acct.grid(column=2, row=2)

txt_user = Entry(window, width=40)
txt_user.grid(column=2, row=3)

txt_pass = Entry(window, width=40)
txt_pass = Entry(window, width=40)
txt_pass.grid(column=2, row=4)

txt_old_pass = Entry(window, width=40)
txt_old_pass.grid(column=2, row=5)

txt_url = Entry(window, width=40)
txt_url.grid(column=2, row=6)

txt_acct.config(state='normal')
txt_user.config(state='normal')
txt_pass.config(state='normal')
txt_pass.config(show="*")
txt_old_pass.config(state='normal')
txt_url.config(state='normal')

groupName1 = "Group1"
groupName2 = "Group2"
groupName3 = "Group3"
groupName4 = "Group4"
groupName5 = "Group5"
groupName6 = "Group6"
groupName7 = "Group7"

menubar = Menu(window)
window.config(menu=menubar)
file = Menu(menubar)
importMenu = Menu(menubar)
exportMenu = Menu(menubar)
file.add_cascade(label = 'Import', menu=importMenu)
importMenu.add_command(label = 'Import from Chrome', command = ImportFileChrome)
importMenu.add_command(label = 'Import from KeePass', command = ImportFileKeePass)
importMenu.add_command(label = 'Import from PasswordPump', command = ImportFilePasswordPump)
file.add_cascade(label = 'Export', menu=exportMenu)
exportMenu.add_cascade(label = 'Export to PasswordPump', command = ExportFile)
#file.add_command(label = 'Insert', command = clickedInsert)
#file.add_command(label = 'Delete', command = clickedDelete)
file.add_command(label = 'Exit', command = clickedClose)
menubar.add_cascade(label = 'File', menu = file)

backup = Menu(menubar)
backup.add_command(label = 'Backup EEprom', command = BackupEEprom)
backup.add_command(label = 'Restore EEprom', command = RestoreEEprom)
menubar.add_cascade(label = 'Backup/Restore', menu = backup)

settings = Menu(menubar)
groupsMenu = Menu(menubar)
settings.add_command(label = 'Change Master Password', command = clickedChangeMasterPass)
settings.add_command(label = 'Show Password on Device', command = clickedShowPassword)
settings.add_command(label = 'Decoy Password', command = clickedDecoyPassword)
settings.add_cascade(label = 'Customize Groups', menu=groupsMenu)
groupsMenu.add_command(label = groupName1, command = customizeGroup1)
groupsMenu.add_command(label = groupName2, command = customizeGroup2)
groupsMenu.add_command(label = groupName3, command = customizeGroup3)
groupsMenu.add_command(label = groupName4, command = customizeGroup4)
groupsMenu.add_command(label = groupName5, command = customizeGroup5)
groupsMenu.add_command(label = groupName6, command = customizeGroup6)
groupsMenu.add_command(label = groupName7, command = customizeGroup7)
settings.add_command(label = 'Factory Reset', command = FactoryReset)
menubar.add_cascade(label = 'Settings', menu = settings)

menubar.entryconfig('File', state='disabled')
menubar.entryconfig('Backup/Restore', state='disabled')
menubar.entryconfig('Settings', state='disabled')

#styles = ["0 - Return","1 - Tab"]
#cbStyle = Combobox(window, values=styles, justify=LEFT, width=37)
cbStyle = Combobox(window, justify=LEFT, width=37)
cbStyle['values'] = ('Return',
                     'Tab')
cbStyle.current(1)
cbStyle.grid(column=2, row=7)
cbStyle.bind('<<ComboboxSelected>>', on_style_select)

btn_previous = Button(window, text="<<Previous", command=clickedPrevious)
btn_previous.grid(column=1, row=19)
btn_previous.config(state='disabled')

btn_insert = Button(window, text="Insert", command=clickedInsert)
btn_insert.grid(column=1, row=18)
btn_insert.config(state='disabled')

btn_delete = Button(window, text="Delete", command=clickedDelete)
btn_delete.grid(column=4, row=18)
btn_delete.config(state='disabled')

btn_open = Button(window, text="Open Port", command=clickedOpen)
btn_open.grid(column=4, row=0)

lb.bind("<<ListboxSelect>>", clickedLoadDB)
#lb.bind('<FocusOut>', clickedOutOfListBox)

#btn_save = Button(window, text="Save", command=clickedSave)
#btn_save.grid(column=4, row=19)

btn_generate = Button(window, text="Generate", command=generatePassword)
btn_generate.grid(column=4, row=4)
btn_generate.config(state='disabled')

btn_powned = Button(window, text="Pwned?", command=checkIfPowned)
btn_powned.grid(column=4, row=5)
btn_powned.config(state='disabled')

btn_flip_pw = Button(window, text="Password", command=flipPassword)
btn_flip_pw.grid(column=1, row=4)
btn_flip_pw.config(state='disabled')

btn_next = Button(window, text="Next>>", command=clickedNext)
btn_next.grid(column=4, row=19)
btn_next.config(state='disabled')

#btn_close = Button(window, text=" Exit ", command=clickedClose)
#btn_close.grid(column=4, row=20)
#btn_close.config(state='normal')

vFavorites = IntVar()
vWork = IntVar()
vPersonal = IntVar()
vHome = IntVar()
vSchool = IntVar()
vFinancial = IntVar()
vMail = IntVar()
vCustom = IntVar()

textboxFavorites = Checkbutton(window, text="Favorites ", variable=vFavorites, command=OnFavorites, onvalue=1, offvalue=0)
textboxFavorites.var = vFavorites
textboxFavorites.grid(column=1,row=12)

textboxWork = Checkbutton(window, text=groupName1, variable=vWork, command=OnWork, onvalue=1, offvalue=0)
textboxWork.var = vWork
textboxWork.grid(column=1,row=13)

textboxPersonal = Checkbutton(window, text=groupName2, variable=vPersonal, command=OnPersonal, onvalue=1, offvalue=0)
textboxPersonal.var = vPersonal
textboxPersonal.grid(column=1,row=14)

textboxHome = Checkbutton(window, text=groupName3, variable=vHome, command=OnHome, onvalue=1, offvalue=0)
textboxHome.var = vHome
textboxHome.grid(column=1,row=15)

textboxSchool = Checkbutton(window, text=groupName4, variable=vSchool, command=OnSchool, onvalue=1, offvalue=0)
textboxSchool.var = vSchool
textboxSchool.grid(column=2,row=12)

textboxFinancial = Checkbutton(window, text=groupName5, variable=vFinancial, command=OnFinancial, onvalue=1, offvalue=0)
textboxFinancial.var = vFinancial
textboxFinancial.grid(column=2,row=13)

textboxMail = Checkbutton(window, text=groupName6, variable=vMail, command=OnMail, onvalue=1, offvalue=0)
textboxMail.var = vMail
textboxMail.grid(column=2,row=14)

textboxCustom = Checkbutton(window, text=groupName7, variable=vCustom, command=OnCustom, onvalue=1, offvalue=0)
textboxCustom.var = vCustom
textboxCustom.grid(column=2,row=15)

lb.bind("<Down>", OnEntryDown)
lb.bind("<Up>", OnEntryUp)

lbl_help = Label(window, text="Instructions", anchor=W, justify=CENTER, width=11)
lbl_help.grid(column=2, row=16)

txt_dir = Text(window, height=5, width=30, relief=FLAT, background="light grey")
txt_dir.grid(column=2, row=17)
txt_dir.config(state=NORMAL)
txt_dir.delete('1.0', END)
directions = """Select Edit with Computer on
the PasswordPump. After 
selecting the port click on
the Open Port button to open
the port for the PasswordPump."""
txt_dir.insert(END, directions)

ports = []
for n, (port, desc, hwid) in enumerate(sorted(comports()), 1):
    ports.append(port + ": " + desc)

cb = Combobox(window, values=ports, justify=LEFT, width=37, exportselection=False)
cb.grid(column=2, row=0)
cb.bind('<<ComboboxSelected>>', on_select)

position = 0                                                                   # Global variables
head = 0
tail = 0
selection = 0
state = "None"
arduinoAttached = 0
group = 0
showPassword = False

window.mainloop()
