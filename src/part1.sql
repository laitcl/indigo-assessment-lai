-- ----------------------------
-- Table structure for employees
-- This table is built first since the main qa_tests table reference this table
-- The `employee_` prefix is removed from these fields since that's implied in the table name
-- ----------------------------
CREATE TABLE research.employees (
  id              INT NOT NULL AUTO_INCREMENT, -- Hopefully there will already be an employee system before we import spreadsheets, but in this world, we will auto-increment employee ids as new ones show up 
  name            varchar(255), -- This would by the employee "SR" in our example. Left 255 characters in case employees have long names
  manager         varchar(255), -- This would be "MP" in our example. 
  team            varchar(255), -- This would be "QA lab" in our example.
  PRIMARY KEY (id)
);

-- This line ensures when new employees are pushed to the database, new employee/manager/team combinations are not duplicated
ALTER TABLE research.employees ADD CONSTRAINT employees UNIQUE(name, manager, team);

-- ----------------------------
-- Indexes for employees
-- ----------------------------
CREATE INDEX employee_name_idx ON research.employees (name); -- I index all three columns here since it would conceivable that each of them would be subject to filtering
CREATE INDEX employee_manager_idx ON research.employees (manager); 
CREATE INDEX employee_team_idx ON research.employees (team); 



-- ----------------------------
-- Table structure for sample_seeds
-- Removed the sample_ prefix here since table name implies it.  
-- Sample_crop and sample_seed_variety are abstracted to this table since it would be conceivable that they have a one to one relationship, and this saves space for not including redundant information on the qa_tests table
-- ----------------------------
CREATE TABLE research.sample_seeds (
  id              INT NOT NULL AUTO_INCREMENT, -- Add auto increment logic here so that new samples will have their unique ID
  crop            varchar(255), -- This would by the employee "Wheat" in our example. Left 255 characters in case crops have long names
  seed_variety    varchar(255), -- This would be "Yerks Seed SRWW" and other things in our example. 
  PRIMARY KEY (id)
);

-- This line ensures when new employees are pushed to the database, new employee/manager/team combinations are not duplicated
ALTER TABLE research.sample_seeds ADD CONSTRAINT employees UNIQUE(crop, seed_variety);

-- ----------------------------
-- Indexes for sample_seeds
-- ----------------------------
CREATE INDEX sample_seed_crop_idx ON research.sample_seeds (crop); 
CREATE INDEX sample_seed_variety_idx ON research.sample_seeds (seed_variety); 


-- ----------------------------
-- Table structure for samples
-- Samples are now separted from tests
-- The idea is that multiple tests can be done on one sample (many to one relationship). As a result, samples should be one entity that tests can reference
-- ----------------------------
CREATE TABLE research.samples (
  id                                      VARCHAR(255), -- Hashed String unique to expeirment; hash combination of irp_qa_sample_barcode and date_received_at_qa
  received_by_employee_id                 INT, -- received by employee, reference employee table
  irp_ga_sample_barcode                   VARCHAR(255) NOT NULL, -- identical to .xlsx; must not be null since id depends on this
  sample_taken                            VARCHAR(255), -- identical to .xlsx
  sample_treatment_name                   VARCHAR(255), -- identical to .xlsx
  sample_seeds_id                         INT, -- Foreign key to the sample_seeds table
  date_received_at_qa                     DATE NOT NULL, -- identical to .xlsx; msut not be null since id depends on this
  date_sample_taken                       DATE, -- identical to .xlsx
  date_treated                            DATE, -- "Unknown" values will be converted to NULL
  sample_date_planted                     DATE, -- There are actually two columns called date_planted; so I'm renaming both of them for specificity
  days_between_treatment_and_planting     INT, -- Fields such as "24 days" will be converted to "24"
  is_qa_needed                            BOOLEAN, -- Converted "Yes" and "No" to "True/False"
  PRIMARY KEY (id),
  FOREIGN KEY (received_by_employee_id) REFERENCES research.employees(id),
  FOREIGN KEY (sample_seeds_id) REFERENCES research.sample_seeds(id)
);

-- ----------------------------
-- Indexes for samples
-- ----------------------------
CREATE INDEX date_received_idx ON research.samples (date_received_at_qa); -- couple examples of single idnexes
CREATE INDEX days_between_treatment_and_planting_idx ON research.samples (days_between_treatment_and_planting);
CREATE INDEX barcode_date_received_idx ON research.samples (irp_ga_sample_barcode, date_received_at_qa); -- example of a composite index since these two might be searched together frequently


-- ----------------------------
-- Table structure for qa_tests
-- The CFU/seed columns are missing here since they are relocated to another table
-- ----------------------------
CREATE TABLE research.qa_tests (
  id                            INT NOT NULL AUTO_INCREMENT, -- Add auto increment logic here so that new tests will have their unique ID sample_tested_by_employee_id            INT, -- Foreign Key to employees table once again
  sample_id                     VARCHAR(255), -- references to the samples table
  sample_tested_by_employee_id  INT, -- received by employee, reference employee table
  chemical_treatment_visible    VARCHAR(255), -- identical to .xlsx
  testing_date_planted          DATE, -- There are actually two columns called date_planted; so I'm renaming both of them for specificity
  planting_code                 VARCHAR(16), -- identical to .xlsx; features a shorter character length since these don't seem to contain many characters
  seeds_g                       DECIMAL, -- identical to .xlsx
  mass_seed_extracted_g         DECIMAL, -- Unit moved to the column; values will be converted to DECIMALS
  plated_volume_mL              DECIMAL,-- .xlsx file misses a unit. Here, the unit is assumed to be mL, but need to contact SME for this
  comment                       TEXT, -- Identical to .xlsx
  PRIMARY KEY (id),
  FOREIGN KEY (sample_id) REFERENCES research.samples(id),
  FOREIGN KEY (sample_tested_by_employee_id) REFERENCES research.employees(id)
);

-- ----------------------------
-- Indexes for qa_tests
-- ----------------------------
CREATE INDEX testing_date_planted_idx ON research.qa_tests (testing_date_planted); -- couple more examples of single idnexes
CREATE INDEX seeds_g_idx ON research.qa_tests (seeds_g);


-- ----------------------------
-- Table structure for colony_forming_units
-- The CFU/seed columns are abstracted into a new table.
-- The idea here is that a scientist should be able to make their counts multiple times
-- For example, a research scientist can choose to count CFU/seed 1000x five times, and store them as five rows here
-- The averaging can take place while querying for the data. This adds a lot more flexibility on how experiments can be conducted while maintainig integrity for the data
-- I do notice some rows such as row 24 have TCTC, TCTC, TCTC, and 0 average into TCTC; not sure how that logic works. I might have to speak with the person that generated this spreadsheet
-- But the averaging will now be done while queryng (or during an ETL), and not input as a database column since subsequent counts will change the average
-- ----------------------------
CREATE TABLE research.colony_forming_units (
  id              INT NOT NULL AUTO_INCREMENT, -- I choose to include an ID in case there needs to be further referencing (such as an average count table)
  count           INT, -- This is the number found in the .xlsx file, which does not support TCTC
  TCTC            BOOLEAN, -- TCTC is now handled by this Boolean instead. This can be true, with a null count, denoting that there is too much to count. This can also be False, indicating there is either a count, or there is no count for the sample at all.
  count_type      varchar(255), -- This denotes the dilution for the count. Can hold values at "1x", "10x", etc, or any arbitrary value 
  qa_test_id      INT, -- This is a foreign key reference to the correct qa_test experiment
  PRIMARY KEY (id),
  FOREIGN KEY (qa_test_id) REFERENCES research.qa_tests(id)
);

-- ----------------------------
-- Indexes for qa_tests
-- ----------------------------
CREATE INDEX qa_test_id_idx ON research.colony_forming_units (qa_test_id);
