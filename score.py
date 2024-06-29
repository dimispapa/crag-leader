from gspread import Client
from pandas import DataFrame


class ScoreCalculator():
    """
    A class module containing methods for the purpose of calculating
    the various scores and leaderboards from the ascent logs.

    Attributes:
        ascent_data (pd.DataFrame): A DataFrame containing ascent logs.
        gsc (gspread.Client): An authorized gspread client instance.
        base_points_dict (dict): A dictionary mapping grades to base points.
        master_grade_bonus (float): A bonus factor for master grades.
        vol_bonus_incr (int): The increment value for volume bonuses.
        vol_bonus_points (int): The points awarded per volume bonus increment.
        unique_asc_bonus (float): A bonus factor for unique ascents.
    """

    def __init__(self, gs_client: Client, ascent_data: DataFrame):
        """
        Initialize the ScoreCalculator class instance.

        Args:
            gs_client (gspread.Client): An authorized gspread client instance.
            ascent_data (pandas.DataFrame): A DataFrame containing ascent logs.
        """
        self.scoring_table = ascent_data
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
            file_name (str): The name of the Google Sheets file containing the
                                scoring system parameters.

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
        """
        Calculate the base points for each ascent and group by climber to sum
        the total base points.

        Returns:
            pandas.DataFrame: A DataFrame with climbers and their total base
                                points.
        """
        # define a mappping function to apply on the dataframe
        def get_base_points(grade):
            return self.base_points_dict.get(grade, 0)

        # apply the mapping function to get the base points for each ascent
        self.scoring_table['Base Points'] = self.scoring_table['Grade'].apply(
            get_base_points)

        # scoring_table = scoring_table.groupby('Climber Name')[
        #     'Base Points'].sum().reset_index()

        # scoring_table.rename(
        #     columns={'Base Points': 'Total Base Points'}, inplace=True)

        # scoring_table = scoring_table.sort_values(
        #     by='Total Base Points', ascending=False).reset_index(drop=True)

    def calc_volume_bonus(self):
        # group the scoring table by the climber and count occurences by group
        volume_bonus = self.scoring_table.groupby(
            'Climber Name').size().reset_index(name='Num Ascents')
        # calculate the volume bonus by getting the increments
        # through floor division and multiplying by the bonus points
        volume_bonus['Volume Bonus'] = \
            (volume_bonus['Num Ascents'] //
             self.vol_bonus_incr) * self.vol_bonus_points
        # # merge the volume bonus df on the scoring table
        # # via a left join
        # self.scoring_table = \
        #     self.scoring_table.merge(
        #         volume_bonus[['Climber Name', 'Volume Bonus']],
        #         on='Climber Name', how='left')
        # # fill potential na values with zero to allow summation later
        # self.scoring_table['Volume Bonus'].fillna(0, inplace=True)

    def calculate_scores(self):
        self.calc_base_points()
        self.calc_volume_bonus()

        return self.scoring_table
