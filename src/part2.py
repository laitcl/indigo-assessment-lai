import pandas as pd
import numpy as np
import os
from pathlib import Path
import sys
import re
import warnings
import math

SRC_DIR = Path(os.path.dirname(os.path.realpath(__file__)))
PROJECT_DIR = Path(os.path.dirname(os.path.realpath(__file__))).parent


class qa_test:

    def __init__(self, filename, sheetname):
        self.columns = [
            'sample_received_by',
            'sample_received_by_employee_manager',
            'sample_received_by_employee_team',
            'irp_qa_sample_barcode',
            'sample_taken_from_farm',
            'sample_treatment_name',
            'sample_crop',
            'sample_seed_variety',
            'date_received_at_qa',
            'date_sample_taken',
            'date_treated',
            'sample_date_planted',
            'days_between_treatment_and_planting',
            'is_qa_needed',
            'sample_tested_by',
            'sample_tested_by_employee_manager',
            'sample_tested_by_employee_team',
            'chemical_treatment_visible',
            'testing_date_plated',
            'plating_code',
            'seeds_g',
            'mass_seed_extracted_g',
            'plated_volume_mL',
            'cfu_seed_1x',
            'cfu_seed_10x',
            'cfu_seed_100x',
            'cfu_seed_1000x',
            'average_cfu_per_seed',
            'comment',
        ]
        self.read_xlsx_files(filename, sheetname)

    def read_xlsx_files(self, filename, sheetname):
        self.data = pd.read_excel(
            filename, index_col=None, sheet_name=sheetname)
        self.data.columns = self.columns

    def add_hash(self):
        id_column = pd.Series(self.data['irp_qa_sample_barcode'] + ',' +
                              self.data['date_received_at_qa'].apply(lambda x: x.strftime('%Y-%m-%d')))
        self.data["id"] = id_column.apply(lambda x: hash(x))

    def cleanup_date_fields(self):
        date_fields = ['date_received_at_qa', 'date_sample_taken',
                       'date_treated', 'sample_date_planted', 'testing_date_plated']
        for date_field in date_fields:
            self.data[date_field] = pd.to_datetime(
                self.data[date_field], errors='coerce')

    def convert_mass_seed_extracted_field(self, mass_string):
        # For the purposes of this exercise I will include a limited number of possible units to convert.
        # In a real deal, the bigger this dictionary, the better
        if pd.isnull(mass_string):
            return mass_string

        unit_dict = {
            'g': 1,
            'mg': 0.0001,
            'ug': 0.0000001,
            'kg': 1000,
            'lb': 454,
        }

        template = re.compile("([0-9]+)([a-zA-Z\s]+)")
        split_mass = template.match(mass_string).groups()
        mass_g = float(split_mass[0])*unit_dict[split_mass[1].strip()]
        return mass_g

    def cleanup_mass_seed_extracted(self):
        self.data['mass_seed_extracted_g'] = self.data['mass_seed_extracted_g'].apply(
            self.convert_mass_seed_extracted_field)

    def cleanup(self):
        # Cleanup is not automatically part of create_csvs in case users want the source data
        self.add_hash()
        self.cleanup_date_fields()
        self.cleanup_mass_seed_extracted()

    def ensure_correct_columns(self):
        expected_columns = set([
            'sample_received_by',
            'sample_received_by_employee_manager',
            'sample_received_by_employee_team',
            'irp_qa_sample_barcode',
            'sample_taken_from_farm',
            'sample_treatment_name',
            'sample_crop',
            'sample_seed_variety',
            'date_received_at_qa',
            'date_sample_taken',
            'date_treated',
            'sample_date_planted',
            'days_between_treatment_and_planting',
            'is_qa_needed',
            'sample_tested_by',
            'sample_tested_by_employee_manager',
            'sample_tested_by_employee_team',
            'chemical_treatment_visible',
            'testing_date_plated',
            'plating_code',
            'seeds_g',
            'mass_seed_extracted_g',
            'plated_volume_mL',
            'cfu_seed_1x',
            'cfu_seed_10x',
            'cfu_seed_100x',
            'cfu_seed_1000x',
            'average_cfu_per_seed',
            'comment',
            'id'])
        current_columns = set(self.data.columns)
        if current_columns != expected_columns:
            if expected_columns.difference(current_columns):
                warnings.warn("Expected columns {0} missing".format(
                    expected_columns.difference(current_columns)))
            if current_columns.difference(expected_columns):
                warnings.warn("Unexpected columns {0} included".format(
                    current_columns.difference(expected_columns)))

    def ensure_populated_columns(self):
        # It might seem that this check is overly complicated
        # Turns out NAT values do not pass the .empty function, so I have to do a few things to play around it here
        for column in self.data.columns:
            if pd.isna(self.data[column]).all():
                warnings.warn("Column {0} is completely empty!".format(column))

    def t_interval_to_string(self, value):
        value = str(value)
        if value == 'NaT':
            return np.nan
        else:
            value = value.strip().split()[0]
            return float(value)

    def warning_on_row(self, index, warning_message):
        warnings.warn(warning_message.format(
            self.data['irp_qa_sample_barcode'].iloc[index], self.data['date_received_at_qa'].iloc[index]))

    def ensure_accurate_days_between_treatment_and_planting(self):
        calculated = (self.data['sample_date_planted'] -
                      self.data['date_treated']).apply(self.t_interval_to_string)
        actual = (self.data['days_between_treatment_and_planting']).apply(
            lambda x: float(x.split()[0]) if isinstance(x, str) else x)
        comparison = ((calculated == actual) | (
            calculated.isnull() & actual.isnull()))
        for i in range(0, len(comparison)):
            if comparison.iloc[i] == False:
                self.warning_on_row(
                    i, "Data at barcode: {0}, date_received: {1} has mismatching days_between_treatment_and_planting")

    def ensure_accurate_average_cfu(self):
        raw_cfu_columns = ['cfu_seed_1x', 'cfu_seed_10x',
                           'cfu_seed_100x', 'cfu_seed_1000x']
        # 'average_cfu_per_seed'
        for i, row in self.data.iterrows():
            average = 0
            count = 0
            for column in raw_cfu_columns:
                try:
                    value = float(row[column])
                    if value != 0 and not math.isnan(value):
                        average += value
                        count += 1
                except:
                    continue
            if count > 0:
                average = average/count

            if isinstance(row['average_cfu_per_seed'], float) and (not math.isclose(average, row['average_cfu_per_seed'], rel_tol=1e-2, abs_tol=1.0)):
                if (math.isnan(average) or average == 0) and math.isnan(row['average_cfu_per_seed']):
                    continue
                self.warning_on_row(
                    i, "Data at barcode: {0}, date_received: {1} has mismatching average_cfu_per_seed")

    def validate_columns(self):
        self.ensure_correct_columns()
        self.ensure_populated_columns()
        self.ensure_accurate_days_between_treatment_and_planting()
        self.ensure_accurate_average_cfu()

    def output_csv(self, dataframe, filename):
        dataframe.to_csv(self.csv_path+filename, index=False)

    def generate_employees_csv(self):
        new_columns = ['name', 'manager', 'team']
        sample_employees = self.data[[
            'sample_received_by', 'sample_received_by_employee_manager', 'sample_received_by_employee_team']]
        sample_employees.columns = new_columns
        testing_employees = self.data[[
            'sample_tested_by', 'sample_tested_by_employee_manager', 'sample_tested_by_employee_team']]
        testing_employees.columns = new_columns
        employees_table = sample_employees.append(
            testing_employees).drop_duplicates()
        # print(employees_table)
        self.output_csv(employees_table, 'employees.csv')

    def generate_sample_seeds_csv(self):
        new_columns = ['crop', 'seed_variety']
        sample_seeds_table = self.data[[
            'sample_crop', 'sample_seed_variety']].drop_duplicates()
        sample_seeds_table.columns = new_columns
        # print(sample_seeds_table)
        self.output_csv(sample_seeds_table, 'sample_seeds.csv')

    def generate_samples_csv(self):
        new_columns = [
            'sample_received_by',
            'sample_received_by_employee_manager',
            'sample_received_by_employee_team',
            'irp_qa_sample_barcode',
            'sample_taken_from_farm',
            'sample_treatment_name',
            'sample_crop',
            'sample_seed_variety',
            'date_received_at_qa',
            'date_sample_taken',
            'date_treated',
            'sample_date_planted',
            'days_between_treatment_and_planting',
            'is_qa_needed',
            'id'
        ]

        samples_table = self.data[new_columns]
        self.output_csv(samples_table, 'samples.csv')

    def generate_qa_tests_csv(self):
        new_columns = [
            'sample_tested_by',
            'sample_tested_by_employee_manager',
            'sample_tested_by_employee_team',
            'chemical_treatment_visible',
            'testing_date_plated',
            'plating_code',
            'seeds_g',
            'mass_seed_extracted_g',
            'plated_volume_mL',
            'comment',
            'id']

        qa_tests_table = self.data[new_columns]
        qa_tests_table = qa_tests_table.rename(columns={'id': 'sample_id'})
        self.output_csv(qa_tests_table, 'qa_tests.csv')

    def generate_colony_forming_units_csv(self):
        columns = [
            'cfu_seed_1x',
            'cfu_seed_10x',
            'cfu_seed_100x',
            'cfu_seed_1000x',
            'average_cfu_per_seed',
            'id']

        new_columns = [
            'count',
            'TCTC',
            'count_type',
            'sample_id'
        ]

        new_cfu_table = []

        for index, row in self.data.iterrows():
            for i, c in enumerate(['cfu_seed_1x', 'cfu_seed_10x', 'cfu_seed_100x', 'cfu_seed_1000x']):
                if isinstance(row[c], int) or isinstance(row[c], float):
                    if math.isnan(row[c]):
                        new_row = ["", False, c, row['id']]
                    else:
                        new_row = [int(row[c]), False, c, row['id']]
                else:
                    new_row = ["", True, c, row['id']]
                new_cfu_table.append(new_row)
        cfu_table = pd.DataFrame(new_cfu_table, columns=new_columns)
        # print(cfu_table)
        self.output_csv(cfu_table, 'colony_forming_units.csv')

    def create_csvs(self):
        self.validate_columns()
        self.csv_path = str(PROJECT_DIR) + '/csv_outputs/'
        self.generate_employees_csv()
        self.generate_sample_seeds_csv()
        self.generate_samples_csv()
        self.generate_qa_tests_csv()
        self.generate_colony_forming_units_csv()


def main():
    # Input order is filename, sheet name
    if len(sys.argv) == 1:
        filename = str(PROJECT_DIR) + "/assets/seed_qa_tests.xlsx"
        sheetname = 'irp_qa_samples'
    elif len(sys.argv) == 2:
        filename = str(PROJECT_DIR) + sys.argv[1]
        sheetname = 'irp_qa_samples'
    elif len(sys.argv) == 3:
        filename = str(PROJECT_DIR) + sys.argv[1]
        sheetname = sys.argv[2]
    assessment = qa_test(filename, sheetname)
    assessment.cleanup()
    assessment.create_csvs()


if __name__ == "__main__":
    main()
