import os
import requests
import logging
import json

from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth
from typing import Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JiraAPIError(Exception):
    pass

class JiraConnectionError(JiraAPIError):
    pass

class JiraNotFoundError(JiraAPIError):
    pass

class JiraClient:
    
    def __init__(
        self,
        email: str,
        api_token: str,
        jira_url: str,
        timeout: int
    ) -> None:
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(email, api_token)
        self.session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        self.jira_url = jira_url
        self.timeout = timeout

    def create_issue(
        self,
        project_key: str,
        summary: str,
        description: str,
        assignee_email: str,
        issue_type: str = "Task",
        priority: str = "Low"
    ) -> str:
        """
        Creates an issue in Jira.

        :param project_key: Jira project key where the issue will be created.
        :param summary: Summary/title of the issue.
        :param description: Detailed description of the issue.
        :param assignee_email: Email of the user to assign the issue to.
        :param issue_type: Type of issue (e.g., Task, Bug, Story).
        :param priority: Priority of the issue.
        :return: The key of the created issue.
        :raises JiraAPIError: If the issue creation fails.
        """
        account_id = self.get_account_id(assignee_email)
        
        if not account_id:
            raise JiraAPIError(f"Assignee '{assignee_email}' not found.")

        issue_payload = json.dumps({
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": description,
                "issuetype": {"name": issue_type},
                "assignee": {"accountId": account_id},
                "priority": {"name": priority}
            }
        })

        url = f"{self.jira_url}/2/issue"
        try:
            response = self.session.post(url,
                                         data=issue_payload,
                                         timeout=self.timeout)
            response.raise_for_status()
            issue_key = response.json().get('key')
            logger.info(f"Issue created successfully. Key: {issue_key}")
            return issue_key
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating issue: {e}")
            raise JiraAPIError(f"Error creating issue: {e}")

    def get_account_id(
        self,
        user_email: str
    ) -> Optional[str]:
        """
        Retrieves the accountId for a given user email.

        :param user_email: Email of the user to search for in Jira.
        :return: accountId of the user, or None if not found.
        :raises JiraAPIError: If the API request fails.
        """
        url = f"{self.jira_url}/3/user/search"
        params = {'query': user_email}
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            user_data = response.json()
            if user_data:
                return user_data[0]['accountId']
            logger.warning(f"No user found with email: {user_email}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching accountId: {e}")
            raise JiraAPIError(f"Error fetching accountId: {e}")

    def get_issue(
        self,
        issue_key: str
    ) -> dict:
        """
        Retrieve details of an issue by issue key.

        :param issue_key: The key of the issue to be retrieved.
        :return: A dictionary with the issue details.
        :raises JiraAPIError: If the API request fails or issue is not found.
        """
        url = f"{self.jira_url}/2/issue/{issue_key}"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            issue_data = response.json()
            logger.info(f"Issue {issue_key} retrieved successfully.")
            return issue_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching issue {issue_key}: {e}")
            raise JiraAPIError(f"Error fetching issue {issue_key}: {e}")
    
    def get_possible_transitions(
        self, 
        issue_key: str
    ) -> List[dict]:
        """
        Retrieves the possible transitions (next statuses) for a given issue.

        :param issue_key: The key of the Jira issue.
        :return: A list of possible transitions with their IDs and names.
        :raises JiraAPIError: If the API request fails.
        """
        url = f"{self.jira_url}/2/issue/{issue_key}/transitions"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            transitions_data = response.json().get('transitions', [])
            
            if not transitions_data:
                logger.info(f"No transitions found for issue {issue_key}.")
            else:
                logger.info(f"Found {len(transitions_data)} transitions for issue {issue_key}.")
            
            # Return the list of transitions with transition ID and name
            return [
                {"id": transition["id"], "name": transition["name"]}
                for transition in transitions_data
            ]
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching transitions for issue {issue_key}: {e}")
            raise JiraAPIError(f"Error fetching transitions for issue {issue_key}: {e}")
    
    def get_user_issues(
        self,
        user_email: str,
        status: Optional[str] = 'To Do',
        max_results: int = 50
    ) -> List[dict]:
        """
        Retrieves all issues assigned to a specific user.

        :param user_email: The email of the user whose issues you want to retrieve.
        :param status: Filter only type of status. (default to 'To Do').
        :param max_results: The maximum number of results to return (default 50).
        :return: A list of dictionaries containing issue details.
        :raises JiraAPIError: If the API request fails.
        """
        account_id = self.get_account_id(user_email)
        
        if not account_id:
            raise JiraAPIError(f"Assignee '{user_email}' not found.")
        
        url = f"{self.jira_url}/2/search"
        
        jql = f"assignee={account_id} ORDER BY created ASC"
        if status:
            jql = f"assignee={account_id} AND status = '{status}' ORDER BY created ASC"
        
        params = {
            'jql': jql,
            'maxResults': max_results,
            'fields': 'key,summary,status,created'
        }

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            issues = response.json().get('issues', [])
            
            if issues:
                logger.info(f"Found {len(issues)} issues assigned to {user_email}.")
                return issues
            else:
                logger.info(f"No issues found for user: {user_email}")
                return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching issues for user {user_email}: {e}")
            raise JiraAPIError(f"Error fetching issues for user {user_email}: {e}")
    
    def get_user_not_done_issues(
        self,
        user_email: str,
        max_results: int = 50
    ) -> List[dict]:
        """
        Retrieves all issues assigned to a specific user that status is not Done.

        :param user_email: The email of the user whose issues you want to retrieve.
        :param max_results: The maximum number of results to return (default 50).
        :return: A list of dictionaries containing issue details.
        :raises JiraAPIError: If the API request fails.
        """
        account_id = self.get_account_id(user_email)
        
        if not account_id:
            raise JiraAPIError(f"Assignee '{user_email}' not found.")
        
        url = f"{self.jira_url}/2/search"
        
        jql = f"assignee={account_id} AND status != 'Done' ORDER BY created ASC"
        
        params = {
            'jql': jql,
            'maxResults': max_results,
            'fields': 'key,summary,status,created'
        }

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            issues = response.json().get('issues', [])
            
            if issues:
                logger.info(f"Found {len(issues)} issues assigned to {user_email}.")
                return issues
            else:
                logger.info(f"No issues found for user: {user_email}")
                return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching issues for user {user_email}: {e}")
            raise JiraAPIError(f"Error fetching issues for user {user_email}: {e}")
    
    def update_issue_status(
        self, 
        issue_key: str, 
        new_status: str = "To Do"
    ) -> None:
        """
        Update the status of an issue.

        :param issue_key: The key of the issue to be updated.
        :param new_status: The new status to transition the issue to.
        :raises JiraAPIError: If the API request fails or transition is not possible.
        """
        # First, get the available transitions for the issue
        transitions_url = f"{self.jira_url}/2/issue/{issue_key}/transitions"
        
        try:
            response = self.session.get(transitions_url, timeout=self.timeout)
            response.raise_for_status()
            transitions = response.json()['transitions']
            
            # Find the transition id for the desired status
            transition_id = None
            for transition in transitions:
                if transition['name'].lower() == new_status.lower():
                    transition_id = transition['id']
                    break
            
            if not transition_id:
                logger.error(f"Transition to status '{new_status}' not found for issue {issue_key}.")
                raise JiraAPIError(f"Transition to status '{new_status}' not found.")

            # Now, perform the transition
            transition_payload = {
                "transition": {
                    "id": transition_id
                }
            }
            response = self.session.post(transitions_url, json=transition_payload, timeout=self.timeout)
            response.raise_for_status()
            logger.info(f"Issue {issue_key} transitioned to '{new_status}' successfully.")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error updating issue status for {issue_key}: {e}")
            raise JiraAPIError(f"Error updating issue status for {issue_key}: {e}")
    
    def close(self):
        self.session.close()

# Example usage:
if __name__ == "__main__":
    
    load_dotenv()
    
    EMAIL = os.getenv("JIRA_EMAIL")
    API_TOKEN = os.getenv("JIRA_API_TOKEN")
    JIRA_URL = os.getenv("JIRA_URL")
    
    jira_client = JiraClient(EMAIL, API_TOKEN, JIRA_URL, 10)
    
    try:
        # issue_key_2 = jira_client.create_issue(
        #     project_key="GEN",
        #     summary="Auto-generated Issue 2",
        #     description="This is an auto-generated issue using Python API created by Phicks",
        #     assignee_email="vi.tran@techxcorp.com"
        # )
        # jira_client.update_issue_status("GEN-351", "In Progress")
        # jira_client.get_issue("GEN-351")
        tasks = jira_client.get_user_not_done_issues("vi.tran@techxcorp.com")
        
            
        for i in tasks:
            for j in jira_client.get_possible_transitions(i["key"]):
                print(j)
                
        for i in tasks:
            jira_client.update_issue_status(i["key"], "In Progress")
        
        for i in tasks:
            jira_client.update_issue_status(i["key"], "Done")
        
    except JiraAPIError as e:
        print(f"An error occurred: {e}")
    finally:
        jira_client.close()
