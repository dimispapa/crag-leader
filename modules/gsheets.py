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
        Handles both file-based credentials and dict/JSON credentials.

        Returns:
            gspread.Client: Authorized gspread client.
        """
        # Check if creds_file is a dictionary (from environment variable)
        if isinstance(self.creds_file, dict):
            creds = Credentials.from_service_account_info(self.creds_file)
        # If it's a string, assume it's a file path
        else:
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
                            dataframe: DataFrame, rows: int = 1000,
                            cols: int = 10):
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
                                             rows=rows,
                                             cols=cols)

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

            # Update timestamp in B1
            worksheet.update('B1', [[timestamp]])

            # Update duration in B2 if provided
            if duration_seconds is not None:
                # Convert to minutes with 1 decimal
                duration_str = f"{duration_seconds/60:.1f}"
                worksheet.update('B2', [[duration_str]])

        except Exception as e:
            print(f"Error updating timestamp: {e}")

    def get_timestamp_and_duration(self, spreadsheet_name: str):
        """Get the last updated timestamp and duration."""
        try:
            worksheet = self.client.open(spreadsheet_name).worksheet(
                'last_updated')
            timestamp = worksheet.acell('B1').value
            duration = worksheet.acell('B2').value

            return timestamp, duration

        except Exception as e:
            raise ValueError(f"Error retrieving timestamp: {e}")

    def update_scrape_reason(self, spreadsheet_name: str, reason: str):
        """
        Update the reason why a scrape was performed.

        Args:
            spreadsheet_name (str): The name of the spreadsheet.
            reason (str): The reason for the scrape.
        """
        try:
            # Try to access last_updated worksheet first
            try:
                worksheet = self.client.open(spreadsheet_name).worksheet(
                    'last_updated')

                # Update reason
                worksheet.update('A3:B3', [['Reason', reason]])

            except gspread.WorksheetNotFound:
                # Create the worksheet if it doesn't exist
                gsheet = self.client.open(spreadsheet_name)
                worksheet = gsheet.add_worksheet(title='last_updated',
                                                 rows=5,
                                                 cols=2)
                worksheet.update('A1:B3', [[
                    'Last Update',
                    [
                        'Timestamp',
                        datetime.now().strftime("%b %d %Y %H:%M:%S")
                    ], ['Duration (mins)', ''], ['Reason', reason]
                ]])

        except Exception as e:
            print(f"Error updating scrape reason: {e}")

    def get_scrape_reason(self, spreadsheet_name: str):
        """
        Get the reason for the last scrape.

        Args:
            spreadsheet_name (str): The name of the spreadsheet.

        Returns:
            str: The reason for the last scrape or a default message.
        """
        try:
            worksheet = self.client.open(spreadsheet_name).worksheet(
                'last_updated')
            reason = worksheet.acell('B3').value

            # If cell exists but is empty or doesn't exist
            if not reason:
                return "No scrape reason recorded"
            else:
                return reason
        except Exception:
            return "Error retrieving scrape reason"
