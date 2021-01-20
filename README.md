# Indigo Code Challenge for Lawrence Lai
This repository hosues the Indigo Ag Code challenge for Lawrence Lai.

The objective of this respository is to:
/*:
  1. Design a MySQL database structure to house the provided data from the .xlsx file. In addition, any future files of similar format should be compatible with the existing database structure.
  2. Design Python code to process the .xlsx data into .csv files, which can be inserted into the aforementioned MySQL database structure. This Python code should be capable of ingestion, reformatting, cleaning, but not the loading of the csv files into the MySQL database.
  3. Include SQL query to query for the count of the total number of samples tested by employee’s team in September 2020
  4. Write a Python class used to validate a given Pandas dataframe that meets the following criteria:
    a. Contains all expected columns from the .xlsx files
    b. Ensures that a column is not completely empty
    c. Raises a warning when the dataframe is invalid
 */

# Installation

Create a virtual environment using:

`python -m venv <environment-name>`

Activate the virtual environment using:

`source <environment-name>/bin/activate`

Install the required packages

`pip install -r requirements.txt`

And you are ready to run the code!

# Running the code

The code can be run by using:

`python src/part2.py <excel file name> <sheet name>`

For example:

`python src/part2.py assets/seed_qa_tests.xlsx irp_qa_samples`

If an excel file name is not supplied, the default file and sheet names will be assumed to be `assets/seed_qa_tests.xlsx` and `irp_qa_samples`

Running the script will output csv files in the directory `csv_outputs/`

# How to upload csvs into database

The two tables employees and sample_seeds are very straightforward. I'm unfortunately PostgreSQL native and not MySQL native, so I will do this in PostgreSQL terms. One can apply the same logic to other databases.

`employees` and `sample_seeds`:

```
CREATE TEMP TABLE tmp_{table_name}_table
(LIKE {table_name} INCLUDING DEFAULTS)
ON COMMIT DROP;

COPY tmp_{table_name}_table ({columns}) FROM '{filename}' CSV;

INSERT INTO {table_name} ({columns})
SELECT {columns} FROM tmp_{table_name}_table 
ON CONFLICT DO NOTHING;
```

The reason why this is done in three steps is because the copy command doesn't support conflict conditions. For example, we want any new employees to be pushed to the database, whereas if conflicts occur, no pushes take place, and the old employees are retained.


The other tables involve dealing with foreign keys. This is slightly more complicated, but not impossible. I will do qa_tests as an example:


```
CREATE TEMP TABLE tmp_qa_tests_table
  ('sample_tested_by', 
  'sample_tested_by_employee_manager',
  'sample_tested_by_employee_team', 
  'chemical_treatment_visible',
  'testing_date_plated', 
  'plating_code', 
  'seeds_g',
  'mass_seed_extracted_g', 
  'plated_volume_mL',  
  'comment', 
  'id')
ON COMMIT DROP;

COPY tmp_qa_tests_table 
('sample_tested_by', 
  'sample_tested_by_employee_manager',
  'sample_tested_by_employee_team', 
  'chemical_treatment_visible',
  'testing_date_plated', 
  'plating_code', 
  'seeds_g',
  'mass_seed_extracted_g', 
  'plated_volume_mL',  
  'comment', 
  'id') 
FROM 'qa_tests.csv' CSV;

-- At this point, we have a temp table that contains all the information on the csv.

WITH joined_table as 
(
SELECT 
  e.id as employee_id
  chemical_treatment_visible,
  testing_date_plated,
  plating_code,
  seeds_g,
  mass_seed_extracted_g,
  plated_volume_mL,
  comment,
  sample_id
  FROM tmp_qa_tests_table qa
  JOIN employees
    ON qa.sample_tested_by = e.name
    AND qa.sample_tested_by_employee_manager = e.manager
    AND qa.sample_tested_by_employee_team e.team
)
INSERT INTO qa_tests
(employee_id, 
chemical_treatment_visible,
testing_date_plated, 
plating_code, 
seeds_g,
mass_seed_extracted_g, 
plated_volume_mL,  
comment, 
sample_id)
SELECT 
(employee_id, 
  chemical_treatment_visible,
  testing_date_plated, 
  plating_code, 
  seeds_g,
  mass_seed_extracted_g, 
  plated_volume_mL,  
  comment, 
  sample_id)  
FROM joined_table;
```

In this last step, we do a little bit of pre-joining before the insertion to make sure that the employee_ids and the qa_tests match up. There is no need to join the samples_id currently, because that is figured out during the python code. In a world where we may be rerunning a qa_test for the same sample, we would just allow a second entry with the same sample_id to be pushed to create the many_to_one relationship between qa_tests and samples.


On the note of the colony_forming_units table: this table's been restructured from its original appearance. See my explanation on src/part1.sql why this took place. These changes should have been reflected in the csv file, and a normal push similar to the qa_tests table should suffice.

# General Strategy

There are notes written prior to tackling the problems. Any particular decisions made while solving the problem are directly in the code as comments

## Part 1: MySQL Database design

The four main things that I will be looking to capture are primary keys, datatypes, abstraction of data types, and indices.

/*:
  1. It appears that each experiment cannot be uniquely identified only using one column of data. As mentioned in the prompt, the combination of a barcode and date_received are required to uniquely identify a row. In this implementation, a primary key should be added to enable unique identification of each row. This can be done by adding a serial ID to each row when imported, or by adding a hashed primary key by hasing together the combination of the two unique rows. I will opt to do the latter, since the primary key will hold some significance, and can be reverse hashed into meaningful information.
  
  2. While there are fields that have very obvious datatypes (such as dates (date) and barcodes (strings)), some are counterintuitive. For example, `Mass Seed Extracted` fields record `3g`, instead of having the units stored in the header, and the field should be a decimal number. Another example would be `CFU/seed 1x`, where normally we would expect a decimal, but TCTC is a possible entry. Here, are choice is to either store these fields as varchars or as decimals, where TCTC would be converted to an arbitrarily large value. The former has the advantage that these values can be kept in their original appearance, and there is no need to store arbitrary values, whereas the latter would be easier to query from (it's hard to query value > 500 for varchars, whereas it would be relatively straightforward for a decimal). In these cases I will opt for the `varchar`, just out of personal preference. In reality, it would be a conversation to have with the end users of this data on what is actually important.
  
  3. There are a few classes of columns, the most obvious one being the employee columns, should belong to a separate table. The general sign for columns that could be abstracted into new tables is that there is a many-to-one relationship between a column's data and a row. In this example, there are only a few employees involved in this qa_testing, but their names are repeatedly duplicated across all the rows. By abstracting employees to a separate table, the employee's information does not have to be duplicated across all the rows. In this project, I also account for things that can become many-to-one relationships in the future; for example, a multiple qa tests can be done on one sample, and therefore I've separated qa_tests and samples into two distinct tables. CFU counts can be done multiple times for one qa test, and therefore I've chosen to abstract CFU's to its own table. Special note on CFUs is that I now choose to store them in a transactional table, where each row is one count, and the row has information as to what type of count (e.g. 1x vs 1000x); this also allows CFU counts to be done different number of times for each different method; this could save up on many empty rows.

  4. Table indexing should be done to ensure that the data can be easily searched. This is best done by having a conversation with the end users of the data to figure out what are the most common query constraints, but since I am a solo contributor to this, I will making a few examples just to highlight the recommended indicies.
*/

There are also a few general etiquette things to ensure. Plural table names, singular column names, foreign keys should be in {table_name_id}, etc. Hopefully I don't miss anything.

## Part 2: Python Script

It's heavily implied, if not explicitly stated that Pandas is the preferred method of data analysis here. 

There are some columns that contain pretty messy data. To name a few:
/*:
1. `Days between treatment and planting` sometimes has integers, sometimes has integers + 'days'. On top of all this, Pandas does not support support null values for integers. I will be splitting these strings, and only taking the integer components. I will also ensure the data type stays as strings to ensure there are no none type errors.
2. `date_plated_on` has a distinct date format from the other columns. I believe this should resolve itself on the database insert, but this is something that I should make sure.
3. Mentioned previously, `Mass Seed Extracted` incorrectly has units in the fields. I will be converting these all to one unit (grams), and moving the gram unit to the header
4. Also previously mentioned, it is ambiguous how `Plated volume` and other similar fields should be treated. Given my database implementation, I will be keeping the original string if they show up as `TCTC`; 
*/

Another previously mentioned thing is that I will be hashing together `irp_qa_sample_barcode` and `date_received_at_qa` to make a unique identifier to make things possibly easier down the road.

## Part 3: Querying for information

I will include a standalone .sql file in the src/ directory to show this query.

The method that I have chosen to use is to use subqueries to isolate the average CFU counts in the correct month and employee team, and then use a final query to count the number of rows that result from these subqueries.

## Part 4: Validation Class

I've thought carefully, and I think this will be done in conjunction with part 2.

The plan is to write a Python class, where a pandas dataframe is an attribute of this class. After the cleaning and manipulations, a generate CSV function will be run, where the saved dataframe will be proceed into CSVs. In this CSV generation function, a few functions that belong to this class will run, including all the validation checks included in this part.

Test suites such as PyTest and miniTest may not be ideal for this because these tests actually involve testing data used for production, whereas these test suites function best when used with dummy data, and testing for specific functions.

I've chosen to do additional validation checks for two columns: they are the days_between_treatment_and_planting, and average_cfus. These columns are technically derived from other columns in the spreadsheet, and they should be checked for consistency. Granted, the average cfus no longer get recorded to the database, but I think this is a good check for the spreadsheet integrity.

# Credits

All code is designed and written by Lawrence Lai, 1/19/2021
