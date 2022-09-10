###########################################
#Author: Nguyen Anh Duc (MS/EDA32-XC)
###########################################
import requests
import base64
import json

class JRticket:

    def __init__(self, ticket_id, ticket_type, ticket_status, creator, assignee,
    reporter, labels, created_date, due_date,
    updated_date, resolved_date, project, resolution,
    issue_links, problem_type):

        self.ticket_id = ticket_id
        self.ticket_type = ticket_type
        self.ticket_status = ticket_status
        self.creator = creator
        self.assignee = assignee
        self.reporter = reporter
        self.labels = labels
        self.created_date = created_date
        self.due_date = due_date
        self.updated_date = updated_date
        self.resolved_date = resolved_date
        self.project = project
        self.resolution = resolution
        self.issue_links = issue_links
        self.problem_type = problem_type

    def print_attributes(self):
        attrs = vars(self) #The vars() method returns the __dict__ (dictionary mapping) attribute of the given object.
        for key, value in attrs.items():
            print(f'{key}: {value}')

def is_empty_list(input_list):
    if len(input_list) > 0:
        return False
    else:
        return True

def is_key_valid(input_dict, key_name):
    if key_name in input_dict:
        if input_dict[key_name] != None:
            return True
    return False

#tracker08-x is a test instance (for testing purpose) of tracker08
#password must be your Portal-Password, you can change/reset it via https://rb-im.bosch.com/sim/user/changePassword.jsp
#authentication via Personal Access Token (PAT) available with JIRA release v8.20
#tracker-08 is based on v8.13.22, PAT not yet available

# In order to use basic authentication with Jira, use base64 encode for your username:password
# message = "LeoDicaprio:25???Bye_babe"
# message_bytes = message.encode('ascii')
# base64_bytes = base64.b64encode(message_bytes)
# print(base64_bytes)

def jira_request(issue_index, no_of_issues, tickets, jql):
    headers = {
        'Authorization': 'Basic TGVvRGljYXByaW86MjU/Pz9CeWVfYmFiZQ==', # TGVvRGljYXByaW86MjU/Pz9CeWVfYmFiZQ== is the LeoDicaprio:25???Bye_babe after encoding
        'Accept': 'application/json',
        'Content-type': 'application/json' # The Media type of the body of the request (used with POST and PUT requests)
    }

    query = {
        'jql': jql,
        'startAt': issue_index, # the index of the first issue to return (0-based)
        'maxResults': no_of_issues, # number of items to return per page
        # indicate which data fields you want to extract
        # https://support.atlassian.com/jira-service-management-cloud/docs/advanced-search-reference-jql-fields/#Advancedsearchingfieldsreference-TypeType
        'fields': [
            'status',
            'issuetype',
            'creator',
            'assignee',
            'reporter',
            'labels',
            'created',
            'due',
            'updated',
            'resolutiondate',
            'project',
            'resolution',
            'issuelinks',
            'customfield_26726' # Problem Type field -> this is a custom field
        ]
    }

    # response = requests.get('https://rb-tracker.bosch.com/tracker08-x/rest/api/2/issue/GACFRAXXIX-908/', headers=headers)
    try:
        response = requests.post('https://rb-tracker.bosch.com/tracker08/rest/api/2/search', headers=headers, json=query)
    except Exception as err:
        print(f'Error occurred: {err}')
        return None

    ticket_content = response.json()

    if not is_empty_list(ticket_content['issues']):
        for ticket in ticket_content['issues']:
            # print(ticket['fields']['creator']['displayName'])
            ticket_id = ticket['key']
            ticket_type = ticket['fields']['issuetype']['name']
            status = ticket['fields']['status']['name']
            creator = [ticket['fields']['creator']['name'], ticket['fields']['creator']['displayName']]
            assignee = [ticket['fields']['assignee']['name'], ticket['fields']['assignee']['displayName']]
            reporter = [ticket['fields']['reporter']['name'], ticket['fields']['reporter']['displayName']]

            if not is_empty_list(ticket['fields']['labels']):
                labels = ticket['fields']['labels']
            else:
                labels = None

            created = ticket['fields']['created'][0:10]

            if is_key_valid(ticket['fields'], 'due'):
                due = ticket['fields']['due'][0:10]
            else:
                due = None

            if is_key_valid(ticket['fields'], 'updated'):
                updated = ticket['fields']['updated'][0:10]
            else:
                updated = None

            if is_key_valid(ticket['fields'], 'resolutiondate'):
                resolved = ticket['fields']['resolutiondate'][0:10]
            else:
                resolved = None

            project = [ticket['fields']['project']['key'], ticket['fields']['project']['name']]

            if is_key_valid(ticket['fields'], 'resolution'):
                resolution = ticket['fields']['resolution']['name']
            else:
                resolution = 'Unresolved'

            if not is_empty_list(ticket['fields']['issuelinks']):
                issuelinks = []
                for link in ticket['fields']['issuelinks']:
                    if is_key_valid(link, 'outwardIssue'):
                        if link['type']['outward'] == 'is bug of':
                            issuelinks.append(link['outwardIssue']['key'])
                if is_empty_list(issuelinks):
                    issuelinks = None
            else:
                issuelinks = None

            if is_key_valid(ticket['fields'], 'customfield_26726'):
                problemtype = ticket['fields']['customfield_26726']['value']
            else:
                problemtype = None

            # print(problemtype)
            ticket_obj = JRticket(ticket_id, ticket_type, status, creator, assignee, reporter, labels, created, due, updated, resolved, project, resolution, issuelinks, problemtype)
            tickets.append(ticket_obj)
        jira_request(issue_index+no_of_issues, no_of_issues, tickets, jql)

    # write data in json format so I can open with Notepad++ for checking/debugging
    json_object = json.dumps(ticket_content, indent=4)
    with open("ticket.json", "w") as outfile:
        outfile.write(json_object)

#example
# tickets = []
# jql = 'reporter = UDN1HC and created >= 2022-05-05'
# jira_request(0, 50, tickets, jql)
# print(len(tickets))