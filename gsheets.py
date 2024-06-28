"""
Helper module to allow interaction with and writing/fetching data
to/from Google Sheets on a Google Drive location.
"""
import gspread
from google.oauth2.service_account import Credentials
from gspread_dataframe import set_with_dataframe
from pandas import DataFrame


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
            return print(f'Error: The Google Sheet "{gsheet_name}" '
                         'does not exist, please create a Google sheet file'
                         f' with the name "{gsheet_name}" and then choose '
                         'to "scrape".\n')
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
            return worksheet.get_all_records()

        except gspread.WorksheetNotFound:
            return print(f'Error: The worksheet {worksheet_name} does '
                         'not exist. Please choose the "scrape" option to '
                         'retrieve data from 27crags.\n')

        except gspread.SpreadsheetNotFound:
            return print(f'Error: The Google Sheet "{gsheet_name}" '
                         'does not exist, please create a Google sheet file'
                         f' with name "{gsheet_name}" and then choose '
                         'to "scrape".\n')

    def write_data_to_sheet(self,
                            gsheet_name: str,
                            worksheet_name: str,
                            dataframe: DataFrame):
        """
        Writes data to worksheet in Google Sheet.

        Args:
            gsheet_name (str): The name of the Google Sheet.
            worksheet_name (str): The worksheet of the Google Sheet.
            data (dict): The dictionary representing the data.
        """

        # first open or create the gsheet
        gsheet = self.get_or_create_gsheet(gsheet_name)
        # access the worksheet or create if not exists
        try:
            worksheet = gsheet.worksheet(worksheet_name)

        except gspread.WorksheetNotFound:
            worksheet = gsheet.add_worksheet(
                title=worksheet_name, rows=1000, cols=10)

        # clear the worksheet
        worksheet.clear()
        # write the dataframe to the worksheet
        set_with_dataframe(worksheet, dataframe)
