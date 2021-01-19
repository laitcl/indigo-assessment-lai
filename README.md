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

(Placeholder)

# General Strategy

## Part 1: MySQL Database design

The four main things that I will be looking to capture are primary keys, datatypes, optimizing redundancy of data, and indices.

/*:
  1. It appears that each experiment cannot be uniquely identified only using one column of data. As mentioned in the prompt, the combination of a barcode and date_received are required to uniquely identify a row. In this implementation, a primary key should be added to enable unique identification of each row. This can be done by adding a serial ID to each row when imported, or by adding a hashed primary key by hasing together the combination of the two unique rows. I will opt to do the latter, since the primary key will hold some significance, and can be reverse hashed into meaningful information.
  2. While there are fields that have very obvious datatypes (such as dates (date) and barcodes (strings)), some are counterintuitive. For example, `Mass Seed Extracted` fields record `3g`, instead of having the units stored in the header, and the field should be a decimal number. Another example would be `CFU/seed 1x`, where normally we would expect a decimal, but TCTC is a possible entry. Here, are choice is to either store these fields as varchars or as decimals, where TCTC would be converted to an arbitrarily large value. The former has the advantage that these values can be kept in their original appearance, and there is no need to store arbitrary values, whereas the latter would be easier to query from (it's hard to query value > 500 for varchars, whereas it would be relatively straightforward for a decimal). In these cases I will opt for the `varchar`, just out of personal preference. In reality, it would be a conversation to have with the end users of this data on what is actually important.
  3. Optimizing redundant data: There are at least two sets of columns where data would be highly redundant. They are the sample received by, employee manager, and employee team (also the tested by counterpart of the same columns). Employee data definitely belongs to another table, and these columns can be reduced to two foreign keys (received_by and tested_by). Another field where this is possible is the `sample_crop` and `Sample seed_variety`; it's not far of a stretch to say one sample_seed_variety should only result in one sample_crop, so I will consolidating these fields too. I will be adding primary keys to both the employee and sample_seeds tables to allow this referencing.
  4. Table indexing should be done to ensure that the data can be easily searched. This is best done by having a conversation with the end users of the data to figure out what are the most common query constraints, but since I am a solo contributor to this, I will making a few examples just to highlight the recommended indicies.
*/

There are also a few general etiquette things to ensure. Plural table names, singular column names, all that stuff. Hopefully I don't miss anything.

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

I will include a standalone .sql file in the src/ directory to show this query, alongside comments if neccesary.

## Part 4: Validation Class

I've thought carefully, and I think this will be done in conjunction with part 2.

The plan is to write a Python class, where a pandas dataframe is an attribute of this class. After the cleaning and manipulations, a generate CSV function will be run, where the saved dataframe will be proceed into CSVs. In this CSV generation function, a few functions that belong to this class will run, including all the validation checks included in this part.

Test suites such as PyTest and miniTest may not be ideal for this because these tests actually involve testing data used for production, whereas these test suites function best when used with dummy data, and testing for specific functions.

# Credits

All code is designed and written by Lawrence Lai, 1/19/2021
