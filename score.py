from gspread import Client


class ScoreCalculator():
    """
    A class module containing methods for the purpose of calculating
    the various scores and leaderboards from the ascent logs.

    Attributes:
    ascent_data (list of dict): A list of ascent logs, where each log is
                                represented as a dictionary.
    """

    def __init__(self, gs_client: Client, ascent_data):
        """
        Initialize the ScoreCalculator class instance.

        Args:
            gs_client (gspread.Client): An authorized gspread client instance.
            ascent_data (list of dict): A list of ascent logs.
        """
        self.ascent_data = ascent_data
        self.gsc = gs_client
        # get the scoring system parameters
        self.base_points_dict, self.master_grade_bonus, self.vol_bonus_incr, \
            self.vol_bonus_points, self.unique_asc_bonus = \
            self.get_scoring_params('scoring_system')

    def get_scoring_params(self, file_name: str):
        """
        Retrieve scoring system parameters from Google Sheets
        and reformat them for easier use.

        Args:
            gs_client (gspread.Client): An authorized gspread client instance.
            file_name (str): The name of the Google Sheets file containing
                                the scoring system parameters.

        Returns:
            tuple: A tuple containing the following elements:
                - base_points_dict (dict): A dictionary mapping grades to base
                                            points.
                - master_grade_bonus (float): A bonus factor for
                                                master grades.
                - vol_bonus_incr (int): The increment value for
                                        volume bonuses.
                - vol_bonus_points (int): The points awarded per
                                            volume bonus increment.
                - unique_asc_bonus (float): A bonus factor for unique ascents.
        """
        # get scoring system parameters
        base_points_data = self.gsc.get_sheet_data(file_name,
                                                   'base_points')
        master_grade_data = self.gsc.get_sheet_data(file_name,
                                                    'master_grade_bonus')
        volume_bonus_data = self.gsc.get_sheet_data(file_name,
                                                    'volume_bonus')
        unique_ascent_data = self.gsc.get_sheet_data(file_name,
                                                     'unique_ascent_bonus')

        # reformat scoring system params into variables for easier use
        base_points_dict = {str(row['Grade']): int(row['Points'])
                            for row in base_points_data}

        master_grade_bonus = float(
            master_grade_data[0].get('Bonus_factor'))

        vol_bonus_incr = int(
            volume_bonus_data[0].get('Bonus_increment'))

        vol_bonus_points = int(
            volume_bonus_data[0].get('Points_per_increment'))

        unique_asc_bonus = float(
            unique_ascent_data[0].get('Bonus_factor'))

        return (base_points_dict,
                master_grade_bonus,
                vol_bonus_incr,
                vol_bonus_points,
                unique_asc_bonus)

    def calc_base_points(self):

        def get_base_points(grade):
            return self.base_points_dict.get(grade, 0)

        scoring_table = self.ascent_data

        scoring_table = scoring_table['Base Points'] = \
            scoring_table['Grade'].apply(get_base_points)

        scoring_table = scoring_table.groupby('Climber Name')[
            'Base Points'].sum().reset_index()

        scoring_table.rename(
            columns={'Base Points': 'Total Base Points'}, inplace=True)

        scoring_table = scoring_table.sort_values(
            by='Total Base Points', ascending=False).reset_index(drop=True)

        return scoring_table
