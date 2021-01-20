import pandas as pd
import os
from pathlib import Path
import sys
import re

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
        self.data = pd.read_excel(filename, index_col=None, sheet_name = sheetname)
        self.data.columns = self.columns

    def add_hash(self):
        id_column = pd.Series(self.data['irp_qa_sample_barcode'] + ',' + self.data['date_received_at_qa'].apply(lambda x: x.strftime('%Y-%m-%d')))
        self.data["id"] = id_column.apply(lambda x: hash(x))

    def cleanup_date_fields(self):
        date_fields = ['date_received_at_qa', 'date_sample_taken', 'date_treated', 'sample_date_planted', 'testing_date_plated']
        for date_field in date_fields:
            self.data[date_field] = pd.to_datetime(self.data[date_field], errors='coerce')
    
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
        self.data['mass_seed_extracted_g'] = self.data['mass_seed_extracted_g'].apply(self.convert_mass_seed_extracted_field)
        print(self.data['mass_seed_extracted_g'])
        
    def cleanup(self):
        # Cleanup is not automatically part of create_csvs in case users want the source data
        self.add_hash()
        self.cleanup_date_fields()
        self.cleanup_mass_seed_extracted()

    def create_csvs(self):
        pass

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


    print(assessment.data["testing_date_plated"])


if __name__ == "__main__":
    main()