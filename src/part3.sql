-- Imagining the data has been loaded in the tables you have designed and created, write
-- the SQL query to count the total number of samples tested by employee’s team in
-- September 2020 (a sample is considered tested if the column “average_cfu_per_seed”
-- is not NULL).

-- The subquery does the averaging, since I am not saving any of the average values from the original spreadsheet

WITH filtered_cfus as
(
SELECT
count,
qa_test_id
FROM research.colony_forming_units cfu
WHERE cfu.TCTC is false
AND cfu.count > 0
), average_cfu as 
(
SELECT 
    qa.id,
    qa.sample_id,
    qa.sample_tested_by_employee_id,
    qa.testing_date_planted,
    AVG(fcfu.count),
    e.team
    FROM research.qa_tests qa
    JOIN filtered_cfus fcfu
    ON qa.id = fcfu.qa_test_id
    JOIN research.employees e
    ON e.id = qa.sample_tested_by_employee_id
    GROUP BY qa.id
    HAVING e.team = {'testing_employee_team_name'}
    AND qa.testing_date_planted >= '2020-09-01' 
    AND qa.testing_date_planted <= '2020-09-30'
)
SELECT count(acfu.sample_id) as count
FROM average_cfu acfu;