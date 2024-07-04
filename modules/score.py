"""
A module containg classes and method used for calculating the scores, bonuses,
based on the ascent log and aggregating the scores in a leaderboard.
"""
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
        self.base_points_dict, self.vol_bonus_incr, \
            self.vol_bonus_points, self.unique_asc_bonus = \
            self.get_scoring_params('scoring_system')
        # init empty agg table df
        self.aggregate_table = DataFrame()

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
                - vol_bonus_incr (int): The increment value for
                                        volume bonuses.
                - vol_bonus_points (int): The points awarded per
                                            volume bonus increment.
                - unique_asc_bonus (float): A bonus factor for unique ascents.
        """
        # get scoring system parameters
        base_points_data = self.gsc.get_sheet_data(file_name,
                                                   'base_points')
        volume_bonus_data = self.gsc.get_sheet_data(file_name,
                                                    'volume_bonus')
        unique_ascent_data = self.gsc.get_sheet_data(file_name,
                                                     'unique_ascent_bonus')

        # reformat scoring system params into variables for easier use
        base_points_dict = {str(row['Grade']): int(row['Points'])
                            for row in base_points_data}

        vol_bonus_incr = int(
            volume_bonus_data[0].get('Bonus_increment'))

        vol_bonus_points = int(
            volume_bonus_data[0].get('Points_per_increment'))

        unique_asc_bonus = float(
            unique_ascent_data[0].get('Bonus_factor'))

        return (base_points_dict,
                vol_bonus_incr,
                vol_bonus_points,
                unique_asc_bonus)

    def calc_base_points(self):
        """
        Calculate the base points for each ascent and add it to the DataFrame.
        If the ascent type is "flash", the base points are doubled.
        """
        # define a mappping function to apply on the dataframe
        def get_base_points(row):
            base_points = self.base_points_dict.get(row['Grade'], 0)
            if row['Ascent Type'] == 'flash':
                base_points *= 2
            return base_points

        # apply the mapping function to get the base points for each ascent
        self.scoring_table['Base Points'] = self.scoring_table.apply(
            get_base_points, axis=1).astype(int)

    def calc_volume_bonus(self):
        """
        Calculate the volume bonus for each climber based on the number of
        ascents.
        """
        # group the scoring table by the climber and count numbers of ascents
        volume_bonus = self.scoring_table.groupby(
            'Climber Name').size().reset_index(name='Num Ascents')
        # calculate the volume bonus by getting the increments
        # through floor division and multiplying by the bonus points
        volume_bonus['Volume Score'] = \
            (volume_bonus['Num Ascents'] //
             self.vol_bonus_incr) * self.vol_bonus_points
        # merge the volume bonus df on the scoring table
        # via a left join
        self.scoring_table = \
            self.scoring_table.merge(
                volume_bonus[['Climber Name', 'Volume Score']],
                on='Climber Name', how='left')
        # fill potential na values with zero to allow summation later
        self.scoring_table['Volume Score'] = \
            self.scoring_table['Volume Score'].fillna(0).astype(int)

    def calc_unique_ascent(self):
        """
        Calculate the unique ascent bonus for each ascent if applicable.
        """
        # Group by route name and count the number of unique ascents
        ascent_counts = self.scoring_table.groupby(
            'Route Name').size().reset_index(name='Ascent Count')

        # Merge the ascent counts with the scoring table
        self.scoring_table = self.scoring_table.merge(
            ascent_counts, on='Route Name', how='left')

        # Calculate the unique ascent bonus
        self.scoring_table['Unique Ascent Score'] = self.scoring_table.apply(
            lambda row: row['Base Points'] +
            (row['Base Points'] * self.unique_asc_bonus)
            if row['Ascent Count'] == 1 else 0,
            axis=1
        ).astype(int)

    def aggregate_scores(self):
        """
        Aggregates the scoring columns by Climber Name, summing the
        Base Points and Unique Ascent while getting the max of Volume Bonus.

        Returns:
            pandas.DataFrame: The aggregated scoring table.
        """
        # group by climber and aggregate the scoring columns
        self.aggregate_table = self.scoring_table.groupby('Climber Name').agg({
            'Base Points': 'sum',
            'Volume Score': 'max',
            'Unique Ascent Score': 'sum'
        })
        # get the total tally based on the various scoring components
        self.aggregate_table['Total Score'] = \
            self.aggregate_table['Base Points'] + \
            self.aggregate_table['Volume Score'] + \
            self.aggregate_table['Unique Ascent Score']

        return self.aggregate_table

    def calc_master_grade(self, grade: str):
        """
        Calculates the master grade table (on demand) by filtering
        for the supplied grade and counting number of ascents.

        Args:
            grade (str): The supplied grade to filter on.

        Returns:
            pandas.Dataframe: A table with the count of ascents for the
                                applicable grade grouped by climber.
        """
        # filter the scoring table based on that grade
        master_grade_table = \
            self.scoring_table.loc[
                self.scoring_table['Grade'] == grade]
        # group by the climber and count the ascents per that grade
        master_grade_table = master_grade_table.groupby(
            'Climber Name').size().reset_index(
                name=f'Num of {grade} Ascents'
        ).set_index('Climber Name')

        return master_grade_table

    def calculate_scores(self):
        """
        Calculate all scores and bonuses for each climber.

        Returns:
            pandas.DataFrame: An aggregate DataFrame with the scores
                                for each climber.
        """
        self.calc_base_points()
        self.calc_volume_bonus()
        self.calc_unique_ascent()
        aggregate_table = self.aggregate_scores()

        return aggregate_table
