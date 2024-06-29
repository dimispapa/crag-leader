class ScoreCalculator():

    def __init__(self, ascent_data):
        self.ascent_data = ascent_data

    def get_scoring_params(self, gs_client, file_name):
        # get scoring system parameters
        base_points_data = gs_client.get_sheet_data(file_name,
                                                    'base_points')
        master_grade_data = gs_client.get_sheet_data(file_name,
                                                     'master_grade_bonus')
        volume_bonus_data = gs_client.get_sheet_data(file_name,
                                                     'volume_bonus')
        unique_ascent_data = gs_client.get_sheet_data(file_name,
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
