from jira import JIRA
import argparse
import os

'''
  Script Name  : close_jiras_using_jira_query.py
  Purpose      : This utility performs below functions:
                    # List all jira tickets based on input JIRA query
                    # Print JIRA status, JIRA Key etc
                    # Close all such JIRA tickets based on action type provided as input
  Author       : Vivek Dubey(https://github.com/vivekdubeyvkd)
'''

'''
    Test this script in your test environment before using it in your production environment, make changes if required as per your environment setup etc
'''

'''
   pre-requisites:
    1. Install Python3
    2. Install jira Python module, you can use any of the below command based on your python version
         pip install jira
         python -m pip install jira

         or 

         pip3 install jira
         python3 -m pip install jira
'''

'''
    usage: 
    
    python3 close_jiras_using_jira_query.py --jira_query JIRA_QUERY 
                                            --jira_user JIRA_USER 
                                            --jira_user_password JIRA_USER_PASSWORD 
                                            [--action_type ACTION_TYPE]
    ACTION_TYPE allowed values: dryrun or close, dryrun is default action type                                            
'''

def closeJIRA(jira, issue, transitionID, fields):
    jira.transition_issue(issue, transitionID, fields=fields)

def findAndCloseJiraTickets(inputDict):
    # Your JIRA instance URL e.g. https://jira.abc.com
    jira_options = {'server': 'https://jira.abc.com'}

    # Initializing connection using your JIRA account
    jira = JIRA(options=jira_options, basic_auth=(inputDict["jira_user"], inputDict["jira_user_password"]))

    # Get all the open issues
    open_issues = jira.search_issues(inputDict["jira_query"])

    # check action type and print the message
    if inputDict["action_type"] == "close":
        print("\nAs action type is close, so script will try to close JIRA tickets listed as per input JIRA query\n")
    else:
        print("\nAs action type is dryrun, so script will just print the JIRA ticket IDs as per input JIRA query\n")

    # Loop over open issues and transition them to 'closed' status
    # The transition id for 'closed' may vary based on the workflow
    # You should adjust it as per your workflow
    transitionID = 'Closed'  # transition id for "Close"
    for issue in open_issues:
        print(issue.key)
        if inputDict["action_type"] == "close":
            try:
                # Create fields dictionary for additional fields
                # you might need to change these fields attributes as per your workflow
                fields={
                    'resolution': {
                        'name': 'Obsolete',
                    },
                    'fixVersions': [
                        {
                            'name': 'NotNeeded'
                        }
                    ]
                }
                closeJIRA(jira, issue, transitionID, fields)    
            except:
                # Create fields dictionary for additional fields
                # you might need to change these fields attributes as per your workflow
                # You should adjust it as per your workflow
                fields={
                    'resolution': {
                        'name': 'Obsolete',
                    }
                }
                try:
                    try:
                        closeJIRA(jira, issue, transitionID, fields)
                    except:
                        # you might need to change these fields attributes as per your workflow
                        # You should adjust it as per your workflow
                        fields = {}
                        closeJIRA(jira, issue, transitionID, fields)     
                except:
                    # you might need to change transitionID values as per your workflow
                    # You should adjust it as per your workflow
                    transitionID = 'Integration'  # transition id for "Close"
                    closeJIRA(jira, issue, transitionID, fields)

def validateInputs(inputDict):
    if inputDict["action_type"] != "dryrun" and inputDict["action_type"] != "close":
        print("++++++++++++++++ ERROR ++++++++++++++++++++")
        print("Invalid input action_type value " + inputDict["action_type"] + ", allowed values are dryrun||close, please check and rerun exiting ....")
        print("++++++++++++++++ ERROR ++++++++++++++++++++")
        return False
    return True    

def main():
    # Create the parser
    parser = argparse.ArgumentParser(description="List GitHub Repos")

    # Add the arguments
    parser.add_argument('--jira_query', type=str, nargs=1, help='JIRA Query to List JIRA tickets to be closed', required=True)
    parser.add_argument('--jira_user', type=str, nargs=1, help='JIRA User Name', required=True)
    parser.add_argument('--jira_user_password', type=str, nargs=1, help='JIRA User Password', required=True)
    parser.add_argument('--action_type', type=str, nargs=1, help='Action to be performed e.g. by default it is dryrun, close', required=False)

    # Execute the parse_args() method
    args = parser.parse_args()

    # create dict with input to be used for authorization and calling Code Analysis Service for exper AI reviews
    inputDict = {}
    inputDict["jira_query"] = ''.join(args.jira_query)
    inputDict["jira_user"] = ''.join(args.jira_user)
    inputDict["jira_user_password"] = ''.join(args.jira_user_password)
    if args.action_type == None:
        inputDict["action_type"] = "dryrun"
    else:    
        inputDict["action_type"] = ''.join(args.action_type)
    
    # validate input action type    
    if validateInputs(inputDict):
        # call function to list JIRA tickets based on JIRA query and close them
        findAndCloseJiraTickets(inputDict)
    else:
        pass

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("An error occurred: ", str(e))

