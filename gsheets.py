"""
Helper module to allow interaction with and writing/fetching data
to/from Google Sheets on a Google Drive location.
"""
import gspread
from google.oauth2.service_account import Credentials


class GoogleSheetsClient:
    """
    A client to interact with Google Sheets using gspread and Google OAuth2.

    Attributes:
        creds_file (str): Path to the JSON file with Google service account
                            credentials.
        scope (list): List of OAuth2 scope for accessing Google Sheets and
                        Drive.
        client (gspread.Client): Authorized gspread client.
    """

    def __init__(self, creds_file, scope):
        """
        Initialize the GoogleSheetsClient with the given credentials file and
        scope.

        Args:
            creds_file (str): Path to the JSON file with Google service
                                account credentials.
            scope (list): List of OAuth2 scope for accessing Google Sheets and
                            Drive.
        """
        self.creds_file = creds_file
        self.scope = scope
        self.client = self._authorize_client()

    def _authorize_client(self):
        """
        Authorize the gspread client using the provided credentials and scope.

        Returns:
            gspread.Client: Authorized gspread client.
        """
        creds = Credentials.from_service_account_file(self.creds_file)
        scoped_creds = creds.with_scopes(self.scope)
        return gspread.authorize(scoped_creds)

    def get_or_create_gsheet(self, gsheet_name: str):
        """
        Open a Google Sheet by its name or create if not exists.

        Args:
            gsheet_name (str): The name of the Google Sheet to open.

        Returns:
            gspread.Spreadsheet: The opened/created Google Sheet.
        """
        try:
            gsheet = self.client.open(gsheet_name)
        except gspread.SpreadsheetNotFound:
            gsheet = self.client.create(gsheet_name)
        return gsheet

    def get_sheet_data(self, gsheet_name: str, worksheet_name: str):
        """
        Retrieve all values from a specific worksheet in a Google Sheet.

        Args:
            gsheet_name (str): The name of the Google Sheet.
            worksheet_name (str): The name of the worksheet within the Google
                                    Sheet.

        Returns:
            list: A list of lists containing the worksheet data.
        """
        try:
            gsheet = self.client.open(gsheet_name)
            worksheet = gsheet.worksheet(worksheet_name)
            return worksheet.get_all_values()

        except gspread.SpreadsheetNotFound:
            return print(f'Error: The Google Sheet "{gsheet_name}" '
                         'does not exist, check the name and try again.')

    def write_data_to_sheet(self,
                            gsheet_name: str, worksheet_name: str,
                            data: list, headers: list):
        """
        Writes data to worksheet in Google Sheet.

        Args:
            gsheet_name (str): The name of the Google Sheet.
            worksheet_name (str): The worksheet of the Google Sheet.
            data (list): The list of dictionaries representing the data.
            headers (list): The list of defined header name strings.
        """

        # first open or create the gsheet
        gsheet = self.get_or_create_gsheet(gsheet_name)
        # access the worksheet
        worksheet = gsheet.worksheet(worksheet_name)
        # clear the worksheet
        worksheet.clear()
        # append the headers
        worksheet.append_row(headers)
        # iterate through the data and append row by row
        for row in data:
            worksheet.append_row(row)
