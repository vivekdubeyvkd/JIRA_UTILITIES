import sys
import os
import json
import requests
import shutil
import datetime

'''
  Script Name : auto_oosla_reminder_for_jira.py
  Purpose     : This utility lists all the OOSLA JIRA tickets based on JIRA ticket priority across a JIRA project
                It works as follows:
                  1. Scans all open issues based across a JIRA project
                  2. Parses scan results to list all JIRAs with priority P0, P1 and P2 at the moment
                  3. Finds JIRA defect Key/ID, JIRA creation date for every JIRA issue found in scan result to compute OOSLA JIRA tickets
                  4. Adds comments to all OOSLA JIRA tickets and to all JIRA tickets approaching to OOSLA
                  5. Stores all OOSLA JIRA tickets along with priority and JIRA assignee in a output files as well for any further use to generate reports etc
                  6. Provides a way to handle priority SLA values for non security and security JIRA types
  Author      : Vivek Dubey(https://github.com/vivekdubeyvkd)
'''
'''
    Test this script in your test environment before using it in your production environment, make changes if required as per your environment setup etc
'''

'''
   pre-reqsuisites:
       1. Python3
       3. Install Python3 requests module, you can below one of the below commands
          python3 -m pip install requests
          or
          python3 -m pip3 install requests
          or
          pip3 install requests
          or
          pip install requests
'''

''' 
    Usage:
       python3 auto_oosla_reminder_for_jira.py [Team Name] [JIRA Username] [JIRA password]
'''  

# update your JIRA server(https://jira.com/) or API URL(https://jira.com/rest/api/2) as per your JIRA instance setup
JIRA_ROOT_API_URL = 'https://jira.com/rest/api/2'
JIRA_API_URL = JIRA_ROOT_API_URL + '/search'

# define a priority list and SLA values for non security JIRA types
# correct the values as per your SLA
NONSEC_OOSLA_TO_PRIORITY_DICT = {
    "P0" : 40,
    "P1" : 160,
    "P2" : 330,
    "P3" : 700
}

# define a priority list and SLA values for non security JIRA types
# correct the values as per your SLA
SEC_OOSLA_TO_PRIORITY_DICT = {
    "P0" : 40,
    "P1" : 160,
    "P2" : 700,
    "P3" : 2060
}

# define security jira types as per your JIRA setup
SECURITY_ISSUE_TYPE_LIST = ['Security Defect', "Attribution Defect", "Privacy"]

def call_jira_api(requestType, apiURL, headers, payloadData, jiraUser, jiraPwd):
    try:
        r = requests.request(requestType, url = apiURL, params = payloadData,  auth=(jiraUser, jiraPwd))
        jsonData = r.json()
        if "errors" in jsonData:
            print(jsonData['errors'])
        else:
            return jsonData
    except Exception as ex:
            print(ex)

def call_jira_post_api(apiURL, payloadData, jiraUser, jiraPwd):
    try:
        r = requests.post(url = apiURL, json = payloadData,  auth=(jiraUser, jiraPwd))
        jsonData = r.json()
        if "errors" in jsonData:
            print(jsonData['errors'])
        else:
            return jsonData
    except Exception as ex:
            print(ex)

def updateJiraComment(jiraComment, jiraIssue, jiraUser, jiraPwd):
    apiURL = JIRA_ROOT_API_URL + "/issue/" + jiraIssue + "/comment"
    #print(jiraComment)
    jsonPayload =  {
        "type":"mention",
        "body": jiraComment
    }
    call_jira_post_api(apiURL, jsonPayload, jiraUser, jiraPwd)

def getJiraPrioritySearchString(inputJiraPrioritytring):
    if inputJiraPrioritytring.lower() == "p0":
        return "P0: Immediate"
    elif inputJiraPrioritytring.lower() == "p1":
        return "P1: High"
    elif inputJiraPrioritytring.lower() == "p2":
        return "P2: Medium"
    elif inputJiraPrioritytring.lower() == "p3":
        return "P3: Low"
    else:
        pass

def parseAndGetDateObject(jiraCreationDate):
    # datetime(year, month, day, hour, minute, second, microsecond)
    dateValue = jiraCreationDate.replace('T', ' ').split('.')[0]
    dateValue = dateValue.replace('-',',').replace(' ', ',').replace(':', ',')
    dateValues = dateValue.split(',')
    jiraCreationDate = datetime.datetime(int(dateValues[0]), int(dateValues[1]), int(dateValues[2]), int(dateValues[3]), int(dateValues[4]), int(dateValues[5]))
    return jiraCreationDate

# validate priority from ENV var and then add OOSLA reminder in the JIRA ticket
def validatePriorityFromEnvAndAddOoslaReminder(jiraKey, jiraComment, jiraPriority, jiraUser, jiraPwd):
    # read ENV variable named JIRA_PRIORITY and get the value
    readJiraPriorityFromEnv = os.environ.get('JIRA_PRIORITY')
    #print("readJiraPriorityFromEnv ", readJiraPriorityFromEnv)
    if readJiraPriorityFromEnv:
        if readJiraPriorityFromEnv.lower() == jiraPriority.lower():
            print(jiraComment)
            updateJiraComment(jiraComment, jiraKey, jiraUser, jiraPwd)
        else:
            pass
            #print("No need to send reminder")
    else:
        print(jiraComment)
        updateJiraComment(jiraComment, jiraKey, jiraUser, jiraPwd)

# create and return OOSLA comment
def getOoslaJiraComment(inputOoslaTime, issueType, jiraPriority, ooslaMsgtype):
    if inputOoslaTime > 48:
        inputOoslaTime = inputOoslaTime / 24
        inputOoslaTime = str(int(inputOoslaTime)) + " days(approx)"
    else:
        inputOoslaTime = str(int(inputOoslaTime)) + " hours(approx)"

    if ooslaMsgtype == "soonToBeOosla":
        jiraComment = "[Auto OOSLA Reminder]\nThis " + jiraPriority + " JIRA will be in OOSLA in the next " + inputOoslaTime + " , kindly check and update the current status"
        if issueType in SECURITY_ISSUE_TYPE_LIST:
            # check for JIRA project starting with JIRAPROJECTSTARTINGSTRING and custom comment message based on the project name
            if "JIRAPROJECTSTARTINGSTRING" in os.environ.get('inputTeamName'):
                jiraComment = "[Auto OOSLA Reminder]\nThis " + jiraPriority + " JIRA is going to be in OOSLA in the next " + inputOoslaTime + " , kindly check and take immediate action to close the JIRA ticket to avoid it going into OOSLA state\nFor any assistance/help, please reach out to #ask-sbseg-security or check with [~averma5]"
            else:
                jiraComment = "[Auto OOSLA Reminder]\nThis " + jiraPriority + " JIRA is going to be in OOSLA in the next " + inputOoslaTime + " , kindly check and take immediate action to close the JIRA ticket to avoid it going into OOSLA state\nFor any assistance/help, please reach out to security team as mentioned in the JIRA"   
    elif ooslaMsgtype == "oosla":
        jiraComment = "[Auto OOSLA Reminder]\nThis " + jiraPriority + " JIRA is OOSLA for " + inputOoslaTime + " , kindly check and update the current status"
        if issueType in SECURITY_ISSUE_TYPE_LIST:
            # check for JIRA project starting with JIRAPROJECTSTARTINGSTRING and custom comment message based on the project name
            if "JIRAPROJECTSTARTINGSTRING" in os.environ.get('inputTeamName'):
                jiraComment = "[Auto OOSLA Reminder]\nThis " + jiraPriority + " JIRA is OOSLA now for " + inputOoslaTime + " , kindly check and provide immediate update/plan for taking this to closure at the earliest\nFor any assistance/help, please reach out to #ask-sbseg-security or check with [~averma5]" 
            else:
                jiraComment = "[Auto OOSLA Reminder]\nThis " + jiraPriority + " JIRA is OOSLA now for " + inputOoslaTime + " , kindly check and provide immediate update/plan for taking this to closure at the earliest\nFor any assistance/help, please reach out to security team as mentioned in the JIRA"    
    else:
        pass
    return jiraComment

# generic function to handle notification for any priority of JIRA
def checkAndAddOOSLAReminder(issueObject, jiraAge, jiraPriority, jiraUser, jiraPwd, OOSLA_TO_PRIORITY_DICT):
    jiraKey = issueObject["key"]
    print("\nJIRA ID : ", jiraKey)
    if jiraAge <= OOSLA_TO_PRIORITY_DICT[jiraPriority]:
        ooslaTime = OOSLA_TO_PRIORITY_DICT[jiraPriority] - jiraAge
        jiraComment = getOoslaJiraComment(ooslaTime, issueObject["fields"]["issuetype"]["name"], jiraPriority, "soonToBeOosla")
        validatePriorityFromEnvAndAddOoslaReminder(jiraKey, jiraComment, jiraPriority, jiraUser, jiraPwd)
    elif jiraAge > OOSLA_TO_PRIORITY_DICT[jiraPriority]:
        ooslaTime = jiraAge - OOSLA_TO_PRIORITY_DICT[jiraPriority]
        jiraComment = getOoslaJiraComment(ooslaTime, issueObject["fields"]["issuetype"]["name"], jiraPriority, "oosla")
        validatePriorityFromEnvAndAddOoslaReminder(jiraKey, jiraComment, jiraPriority, jiraUser, jiraPwd)
    else:
        pass

# funtion check and remove file
def checkAndCleanFileOrDir(inputFilePath):
    if os.path.isfile(inputFilePath):
        os.remove(inputFilePath)
    elif os.path.isdir(inputFilePath):
        #os.rmdir(inputFilePath)
        shutil.rmtree(inputFilePath)
    else:
        pass

def addWatchersInJira(watcherList, jiraIssue, jiraUser, jiraPwd, OOSLA_TO_PRIORITY_DICT):
    apiURL = JIRA_ROOT_API_URL + "/issue/" + jiraIssue + "/watchers"
    for watcher in watcherList:
        jsonPayload = watcher
        call_jira_post_api(apiURL, jsonPayload, jiraUser, jiraPwd)
        print("Added user " + watcher + " as watcher in " + jiraIssue + " JIRA")

def checkOoslaAndWriteToFile(jiraAssignee, jiraIssue, jiraPriority, jiraAgeInHours, jiraCreationDate, inputIssuetype, inputJiraEnv, outputFileObject, OOSLA_TO_PRIORITY_DICT):
    if jiraAgeInHours > 48:
        jiraAge = str(int(jiraAgeInHours / 24)) + " days"
    else:
        jiraAge = str(int(jiraAgeInHours)) + " hours"

    # check if inputJiraEnv is none or valid one
    #print("inputJiraEnv", inputJiraEnv)
    if inputJiraEnv == None:
        inputJiraEnv = "Unknown"

    # define msg types
    # replease https://jira.com and add jira server instance URL as per your JIRA instance
    OOSLA_MSG = "<tr><td><a href=\"https://jira.com/browse/" + jiraIssue + "\">"+ jiraIssue + "</a></td><td>" + inputIssuetype + "</td><td>" +  inputJiraEnv + "</td><td>" +  jiraPriority + "</td><td>" + jiraAssignee + "</td><td>" + "OOSLA" + "</td><td>" + str(jiraCreationDate) +  "</td><td>"  + jiraAge + "</td></tr>\n"
    SOON_TO_BE_OOSLA_MSG = "<tr><td><a href=\"https://jira.com/browse/" + jiraIssue + "\">" + jiraIssue + "</a></td><td>" + inputIssuetype + "</td><td>" +  inputJiraEnv  + "</td><td>" + jiraPriority + "</td><td>" + jiraAssignee + "</td><td>" + "Soon to be OOSLA" + "</td><td>" + str(jiraCreationDate) +  "</td><td>" + jiraAge  + "</td></tr>\n"
    jiraPrioritySLAValue = OOSLA_TO_PRIORITY_DICT[jiraPriority.upper()]

    if jiraPriority.lower() == "p0":
        if jiraAgeInHours > jiraPrioritySLAValue:
            outputFileObject.write(OOSLA_MSG)
        else:
            #outputFileObject.write(jiraIssue + "," + jiraPriority + "," + jiraAssignee["name" ] + "," + "Soon To be OOSLA" + "," + str(jiraAge) + "\n")
            if jiraAgeInHours > 36 and jiraAgeInHours < jiraPrioritySLAValue:
                outputFileObject.write(SOON_TO_BE_OOSLA_MSG)
    elif jiraPriority.lower() == "p1":
        if jiraAgeInHours > jiraPrioritySLAValue:
            outputFileObject.write(OOSLA_MSG)
            #outputFileObject.write("<tr><td>" + jiraIssue + "</td><td>" + jiraPriority + "</td><td>" + jiraAssignee + "</td><td>" + "Y" + "</td><td>" + str(jiraCreationDate) +  "</td><td>" + jiraAge + "</td></tr>\n")
        elif jiraAgeInHours > (jiraPrioritySLAValue - 48) and jiraAgeInHours < jiraPrioritySLAValue:
            outputFileObject.write(SOON_TO_BE_OOSLA_MSG)
            #outputFileObject.write("<tr><td>" + jiraIssue + "</td><td>" + jiraPriority + "</td><td>" + jiraAssignee + "</td><td>" + "Soon To be OOSLA"  + str(jiraCreationDate) +  "</td><td>" + "</td><td>" + jiraAge + "</td></tr>\n")
        else:
            pass
    elif jiraPriority.lower() == "p2":
        if jiraAgeInHours > jiraPrioritySLAValue:
            outputFileObject.write(OOSLA_MSG)
            #outputFileObject.write("<tr><td>" + jiraIssue + "</td><td>" + jiraPriority + "</td><td>" + jiraAssignee + "</td><td>" + "Y" + "</td><td>" + str(jiraCreationDate) +  "</td><td>" + jiraAge + "</td></tr>\n")
        elif jiraAgeInHours > (jiraPrioritySLAValue - 144) and jiraAgeInHours < jiraPrioritySLAValue:
            outputFileObject.write(SOON_TO_BE_OOSLA_MSG)
            #outputFileObject.write("<tr><td>" + jiraIssue + "</td><td>" + jiraPriority + "</td><td>" + jiraAssignee + "</td><td>" + "Soon To be OOSLA"  + str(jiraCreationDate) +  "</td><td>" + "</td><td>" + jiraAge + "</td></tr>\n")
        else:
            pass
    elif jiraPriority.lower() == "p3":
        if jiraAgeInHours > jiraPrioritySLAValue:
            outputFileObject.write(OOSLA_MSG)
            #outputFileObject.write("<tr><td>" + jiraIssue + "</td><td>" + jiraPriority + "</td><td>" + jiraAssignee + "</td><td>" + "Y" + "</td><td>" + str(jiraCreationDate) +  "</td><td>" + jiraAge + "</td></tr>\n")
        elif jiraAgeInHours >  (jiraPrioritySLAValue - 250) and jiraAgeInHours <  jiraPrioritySLAValue:
            outputFileObject.write(SOON_TO_BE_OOSLA_MSG)
            #outputFileObject.write("<tr><td>" + jiraIssue + "</td><td>" + jiraPriority + "</td><td>" + jiraAssignee + "</td><td>" + "Soon To be OOSLA"  + str(jiraCreationDate) +  "</td><td>" + "</td><td>" + jiraAge + "</td></tr>\n")
        else:
            pass
    else:
        pass

def writeToOutputFile(issueData, jiraPriority, jiraAgeInHours, jiraCreationDate, inputIssueType, outputFileObject, OOSLA_TO_PRIORITY_DICT):
    jiraAssignee = issueData["fields"]["assignee"]
    jiraIssue = issueData["key"]

    # handling a customfield named customfield_123 is the custom field for env used in your JIRA tickets
    if "customfield_123" in issueData["fields"]:
        if issueData["fields"]["customfield_123"] != None:
            jiraEnv = issueData["fields"]["customfield_123"][0]["value"]
        else:
           jiraEnv = "Unknown"
    elif "environment" in issueData["fields"]:
        #print(issueData)
        jiraEnv = issueData["fields"]["environment"]
    else:
        jiraEnv = "Unknown"

    if jiraAssignee != None:
        #outputFileObject.write(jiraIssue + "," + jiraPriority + "," + jiraAssignee["name" ] + "," + "Y" + "," + str(jiraAgeInHours) + "\n")
        checkOoslaAndWriteToFile(jiraAssignee["name"], jiraIssue, jiraPriority, jiraAgeInHours, jiraCreationDate, inputIssueType, jiraEnv, outputFileObject, OOSLA_TO_PRIORITY_DICT)
    else:
        #outputFileObject.write(jiraIssue + "," + jiraPriority + "," + "Unassigned" + "," + "Y" + "," + str(jiraAgeInHours) + "\n")
        checkOoslaAndWriteToFile("Unassigned", jiraIssue, jiraPriority, jiraAgeInHours, jiraCreationDate, inputIssueType, jiraEnv, outputFileObject, OOSLA_TO_PRIORITY_DICT)

def checkAndRemoveEmptyFile(inputFilePath):
    if os.stat(inputFilePath).st_size == 0:  
        os.remove(inputFilePath)
    else:
        pass    

def get_all_open_jiras_in_last12_months(jiraProject, jiraPriority, inputTeamJsonObject, inputTeamName, jiraUser, jiraPwd):
    # temp JIRA issue list
    jiraIssueCheckList = []
    # get JIRA priority search string in JIRA query format
    jiraPrioritySearchString = getJiraPrioritySearchString(jiraPriority)
    # read watchers
    jiraWatchersList = inputTeamJsonObject["watchers"]
    # read jira issuetype
    jiraIssueType = inputTeamJsonObject["JIRA_TYPE"]
    # read exception issue list
    exceptionIssueList = inputTeamJsonObject["exception_jira_list"]
    # security and bug kind of jira issue types
    nonSecJiraTypeList = ["Bug", "Task"]
    # JIRA query to find open JIRAs
    if jiraIssueType:
        queryString = "project = " + jiraProject + " AND issuetype in (" + ",".join(jiraIssueType) + ") AND status in (Open, \"In Progress\") AND priority in (\"" + jiraPrioritySearchString + "\") AND created >= -365d"
    else:    
        queryString = "project = " + jiraProject + " AND status in (Open, \"In Progress\") AND priority in (\"" + jiraPrioritySearchString + "\") AND created >= -365d"
    headers = {
        "Accept": "application/json"
    }
    print("\nInput JIRA Query: " + queryString + "\n")
    startAt = 0
    total = 1
    maxResults = 100
    allJiraJsonData = []
    query = {
        'jql': queryString,
        'startAt' : startAt,
        'maxResults': maxResults
    }
    while startAt <= total:
        jsonData = call_jira_api('GET', JIRA_API_URL, headers, query, jiraUser, jiraPwd)
        allJiraJsonData += jsonData['issues']
        startAt += maxResults
        total = jsonData['total']

    # output file priority wise
    outputFile = inputTeamName + "_" + jiraProject + "_" + jiraPriority.lower() + "_output.html"

    # check and remove output files
    checkAndCleanFileOrDir(outputFile)

    # open output files for writing
    outputTextFileContent = open(outputFile, "a")

    for issue in allJiraJsonData:
        # set OOSLA_TO_PRIORITY_DICT to point to default dict with defect priorities
        OOSLA_TO_PRIORITY_DICT = NONSEC_OOSLA_TO_PRIORITY_DICT 

        # if jira id is in exception list, then do noting and check next JIRA ticket
        if issue["key"] in exceptionIssueList:
            continue

        # store and check to filter out duplicate JIRA
        if issue["key"] in jiraIssueCheckList:
            continue
        else:    
            jiraIssueCheckList.append(issue["key"])

        # define variables    
        jiraSummary = issue["fields"]["summary"]
        jiraCreatedDate = issue["fields"]["created"]
        currentDate = datetime.datetime.now()
        jiraCreationDate = parseAndGetDateObject(jiraCreatedDate)
        #jiraAgeInHours = abs(jiraCreationDate - currentDate).total_seconds() / 3600 - 13.5
        jiraAgeInHours = abs(jiraCreationDate - currentDate).total_seconds() / 3600 + 8
        #print(issue["key"], jiraSummary, jiraCreatedDate, jiraAgeInHours)
        issueType = issue["fields"]["issuetype"]["name"]
        #print(issue)



        # check issue type and age
        # list security and bug kind of JIRAs for last 1 year and others till last 6 months
        if issueType not in SECURITY_ISSUE_TYPE_LIST and issueType not in nonSecJiraTypeList:
            # if other kind of jira age is less than 6 months that is 4380 hours, then do nothing and check next JIRA ticket
            if jiraAgeInHours < 4380:
                #print("No need to do anything for this JIRA ", issueType, issue["key"], jiraAgeInHours)
                continue

        # set OOSLA_TO_PRIORITY_DICT as applicable to security JIRAs that is unchanged and is like earlier time
        if issueType in SECURITY_ISSUE_TYPE_LIST:
            OOSLA_TO_PRIORITY_DICT = SEC_OOSLA_TO_PRIORITY_DICT

        # call update JIRA comment function to add custom comments
        if "P0" in jiraPrioritySearchString:
            jiraPriority = "P0"
            # start sending OOSLA reminder if it is open after 6 hours from time of creation
            if jiraAgeInHours > OOSLA_TO_PRIORITY_DICT["P0"]:
                today = datetime.datetime.today().strftime('%A')
                if today.lower() == 'tuesday':
                    checkAndAddOOSLAReminder(issue, jiraAgeInHours, jiraPriority, jiraUser, jiraPwd, OOSLA_TO_PRIORITY_DICT)
                    addWatchersInJira(jiraWatchersList, issue["key"], jiraUser, jiraPwd, OOSLA_TO_PRIORITY_DICT)
                    writeToOutputFile(issue, jiraPriority, int(jiraAgeInHours), jiraCreatedDate, issueType, outputTextFileContent, OOSLA_TO_PRIORITY_DICT)
                else:
                    pass       
            elif jiraAgeInHours > 6 and jiraAgeInHours < OOSLA_TO_PRIORITY_DICT["P0"]:
                checkAndAddOOSLAReminder(issue, jiraAgeInHours, jiraPriority, jiraUser, jiraPwd, OOSLA_TO_PRIORITY_DICT)
                addWatchersInJira(jiraWatchersList, issue["key"], jiraUser, jiraPwd, OOSLA_TO_PRIORITY_DICT)
                writeToOutputFile(issue, jiraPriority, int(jiraAgeInHours), jiraCreatedDate, issueType, outputTextFileContent, OOSLA_TO_PRIORITY_DICT)                  
                #checkAndAddOOSLAReminderForP0(issue["key"], jiraAgeInHours, jiraUser, jiraPwd)
            else:
                pass
        elif "P1" in jiraPrioritySearchString:
            jiraPriority = "P1"
            # start sending OOSLA reminder if it is open after 4 days from date of creation
            if jiraAgeInHours > OOSLA_TO_PRIORITY_DICT["P1"]:
                today = datetime.datetime.today().strftime('%A')
                if today.lower() == 'tuesday':
                    checkAndAddOOSLAReminder(issue, jiraAgeInHours, jiraPriority, jiraUser, jiraPwd, OOSLA_TO_PRIORITY_DICT)
                    addWatchersInJira(jiraWatchersList, issue["key"], jiraUser, jiraPwd, OOSLA_TO_PRIORITY_DICT)
                    writeToOutputFile(issue, jiraPriority, int(jiraAgeInHours), jiraCreatedDate, issueType, outputTextFileContent, OOSLA_TO_PRIORITY_DICT)
                else:
                    pass
            elif jiraAgeInHours > 48 and jiraAgeInHours < OOSLA_TO_PRIORITY_DICT["P1"]:
                checkAndAddOOSLAReminder(issue, jiraAgeInHours, jiraPriority, jiraUser, jiraPwd, OOSLA_TO_PRIORITY_DICT)
                addWatchersInJira(jiraWatchersList, issue["key"], jiraUser, jiraPwd, OOSLA_TO_PRIORITY_DICT)
                writeToOutputFile(issue, jiraPriority, int(jiraAgeInHours), jiraCreatedDate, issueType, outputTextFileContent, OOSLA_TO_PRIORITY_DICT)       
            else:
                pass
        elif "P2" in jiraPrioritySearchString:
            jiraPriority = "P2"
            customAgeLimit = 168
            if issueType in SECURITY_ISSUE_TYPE_LIST:
                customAgeLimit = 480
            # start sending OOSLA reminder if it is open after 10 days from date of creation
            if jiraAgeInHours > OOSLA_TO_PRIORITY_DICT["P2"]:
                today = datetime.datetime.today().strftime('%A')
                if today.lower() == 'tuesday':
                    checkAndAddOOSLAReminder(issue, jiraAgeInHours, jiraPriority, jiraUser, jiraPwd, OOSLA_TO_PRIORITY_DICT)
                    addWatchersInJira(jiraWatchersList, issue["key"], jiraUser, jiraPwd, OOSLA_TO_PRIORITY_DICT)
                    writeToOutputFile(issue, jiraPriority, int(jiraAgeInHours), jiraCreatedDate, issueType, outputTextFileContent, OOSLA_TO_PRIORITY_DICT)
                else:
                    pass               
            elif jiraAgeInHours > customAgeLimit and jiraAgeInHours < OOSLA_TO_PRIORITY_DICT["P2"]:
                checkAndAddOOSLAReminder(issue, jiraAgeInHours, jiraPriority, jiraUser, jiraPwd, OOSLA_TO_PRIORITY_DICT)
                addWatchersInJira(jiraWatchersList, issue["key"], jiraUser, jiraPwd, OOSLA_TO_PRIORITY_DICT)
                writeToOutputFile(issue, jiraPriority, int(jiraAgeInHours), jiraCreatedDate, issueType, outputTextFileContent, OOSLA_TO_PRIORITY_DICT) 
            else:
                pass
        elif "P3" in jiraPrioritySearchString:
            jiraPriority = "P3"
            customAgeLimit = 480
            if issueType in SECURITY_ISSUE_TYPE_LIST:
                customAgeLimit = 1800      
            # start sending OOSLA reminder if it is open after 60 days from date of creation
            if jiraAgeInHours > OOSLA_TO_PRIORITY_DICT["P3"]:
                today = datetime.datetime.today().strftime('%A')
                if today.lower() == 'tuesday':
                    checkAndAddOOSLAReminder(issue, jiraAgeInHours, jiraPriority, jiraUser, jiraPwd, OOSLA_TO_PRIORITY_DICT)
                    addWatchersInJira(jiraWatchersList, issue["key"], jiraUser, jiraPwd, OOSLA_TO_PRIORITY_DICT)
                    writeToOutputFile(issue, jiraPriority, int(jiraAgeInHours), jiraCreatedDate, issueType, outputTextFileContent, OOSLA_TO_PRIORITY_DICT)
                else:
                    pass               
            elif jiraAgeInHours > customAgeLimit and jiraAgeInHours < OOSLA_TO_PRIORITY_DICT["P3"]:
                checkAndAddOOSLAReminder(issue, jiraAgeInHours, jiraPriority, jiraUser, jiraPwd, OOSLA_TO_PRIORITY_DICT)
                addWatchersInJira(jiraWatchersList, issue["key"], jiraUser, jiraPwd, OOSLA_TO_PRIORITY_DICT)
                writeToOutputFile(issue, jiraPriority, int(jiraAgeInHours), jiraCreatedDate, issueType, outputTextFileContent, OOSLA_TO_PRIORITY_DICT) 
            else:
                pass
        else:
            pass

    # close open output files
    outputTextFileContent.close()

    # check and remove empty outfil with records
    checkAndRemoveEmptyFile(outputFile) 

def validateScriptArgs(scriptArgs):
    if scriptArgs and len(scriptArgs) == 3:
        return "valid"
    else:
        return

def main(scriptArgs):
    if validateScriptArgs(scriptArgs):
        inputTeamName = scriptArgs[0]
        jiraUser = scriptArgs[1]
        jiraPwd = scriptArgs[2]

        # set env variable with the team name
        # do define a team name with using a inputTeamName envrionement variables, ensure that you have a folder name with team name with the onboarding JSON as onboard/myteam.json if inputTeamName has value as myteam
        # e.g.
        # export inputTeamName=myteam 
        # set inputTeamName=myteam
        os.environ['inputTeamName'] = inputTeamName

        # read input onboarding team json to get jira project and applicable priority details for the team
        inputTeamJsonFile = "onboard/" + inputTeamName + ".json"
        if os.path.isfile(inputTeamJsonFile):
            with open(inputTeamJsonFile) as teamJsonFile:
                inputTeamJsonObject = json.load(teamJsonFile)
        else:
            print("++++++++++++++++++++++++++++++++++++ ERROR ++++++++++++++++++++++++++++++++++++")
            print("Team input JSON file " + inputTeamJsonFile +" nout found on the GitHub repo, kindly check and rerun ..... exiting ....") 
            print("++++++++++++++++++++++++++++++++++++ ERROR ++++++++++++++++++++++++++++++++++++")
            sys.exit(1)

        # read ENV variable named JIRA_PRIORITY and get the value
        readJiraPriorityFromEnv = os.environ.get('JIRA_PRIORITY')
        # read watchers
        #inputJiraWatchers = inputTeamJsonObject["watchers"]
        # read jira issuetype
        #inputJiraIssueType = inputTeamJsonObject["JIRA_TYPE"]
        # get all the open jiras based on input project and inpur jira priority
        for inputJiraProject in inputTeamJsonObject["JIRA_PROJECTS"]:
            if readJiraPriorityFromEnv:
                get_all_open_jiras_in_last12_months(inputJiraProject, readJiraPriorityFromEnv.upper(), inputTeamJsonObject, inputTeamName, jiraUser, jiraPwd)    
            else:
                for inpurJiraPriority in inputTeamJsonObject["JIRA_PRIORITIES"]:
                    get_all_open_jiras_in_last12_months(inputJiraProject, inpurJiraPriority, inputTeamJsonObject, inputTeamName, jiraUser, jiraPwd)        
    else:
        print("++++++++++++++++++++++++++++++++++++ ERROR ++++++++++++++++++++++++++++++++++++")
        print("Invalid input parameters passed , kindly check and rerun ..... exiting ....") 
        print("Script to be run as:")
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("      python3 auto_oosla_reminder_for_jira.py [Team Name] [JIRA Username] [JIRA password]")
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++") 

if __name__ == "__main__":
    scriptArgs = sys.argv[1:]
    main(scriptArgs)
