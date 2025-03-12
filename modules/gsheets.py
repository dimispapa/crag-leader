"""
Helper module to allow interaction with and writing/fetching data
to/from Google Sheets on a Google Drive location.
"""
from datetime import datetime
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

    def __init__(self, creds_file: str, scope: list):
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

        gsheet = self.client.open(gsheet_name)
        worksheet = gsheet.worksheet(worksheet_name)
        return worksheet.get_all_records()

    def write_data_to_sheet(self, gsheet_name: str, worksheet_name: str,
                            dataframe: DataFrame):
        """
        Writes data to worksheet in Google Sheet.

        Args:
            gsheet_name (str): The name of the Google Sheet.
            worksheet_name (str): The worksheet of the Google Sheet.
            data (dict): The dictionary representing the data.
        """

        # first open or create the gsheet
        gsheet = self.client.open(gsheet_name)
        # access the worksheet or create if not exists
        try:
            worksheet = gsheet.worksheet(worksheet_name)

        except gspread.WorksheetNotFound:
            worksheet = gsheet.add_worksheet(title=worksheet_name,
                                             rows=1000,
                                             cols=10)

        # clear the worksheet
        worksheet.clear()
        # write the dataframe to the worksheet
        set_with_dataframe(worksheet, dataframe)

    def update_timestamp(self,
                         spreadsheet_name: str,
                         duration_seconds: float = None):
        """
        Update the last_updated timestamp and duration in the spreadsheet.

        Args:
            spreadsheet_name (str): The name of the spreadsheet.
            duration_seconds (float): The duration in seconds.
        """
        try:
            timestamp = datetime.now().strftime("%b %d %Y %H:%M:%S")
            worksheet = self.client.open(spreadsheet_name).worksheet(
                'last_updated')

            # Update timestamp in A1
            worksheet.update('A1', timestamp)

            # Update duration in A2 if provided
            if duration_seconds is not None:
                # Convert to minutes with 1 decimal
                duration_str = f"{duration_seconds/60:.1f}"
                worksheet.update('A2', duration_str)

        except Exception as e:
            print(f"Error updating timestamp: {e}")

    def get_timestamp_and_duration(self, spreadsheet_name: str):
        """Get the last updated timestamp and duration."""
        try:
            worksheet = self.client.open(spreadsheet_name).worksheet(
                'last_updated')
            timestamp = worksheet.acell('A1').value
            duration = worksheet.acell('A2').value

            return timestamp, duration

        except Exception as e:
            raise ValueError(f"Error retrieving timestamp: {e}")
