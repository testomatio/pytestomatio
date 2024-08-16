## 2.8.2.dev4 (2024-08-16)

### Fix

- Fix option check

## 2.8.2.dev3 (2024-08-16)

### Fix

- Fix shared run

## 2.8.2.dev2 (2024-08-16)

## 2.8.2.dev1 (2024-08-16)

### Fix

- Parallel run must be True all the time so that testomatio doesn't create new test runs when update test status

## 2.8.1 (2024-08-14)

## 2.8.1rc2 (2024-08-12)

### Feat

- Provide an option to not update build URL in a test run

### Fix

- process test id that might start with @

## 2.8.1rc1 (2024-08-11)

### Fix

- Accept testid provided by testomatio before test starts

## 2.8.1rc0 (2024-08-11)

### Feat

- Pytestomatio sends test executor url to Testomatio test run (on CI)
- Allow user to asign label at test synchronisation
- Allow filtering tests by ids when running test execution

### Fix

- Handle pytest.skip() so that test status on testomatio is valid
- fix dependencies and gitignore

## 2.6.1 (2024-08-05)

## 2.5.0 (2024-05-08)

## 2.2.0 (2024-04-03)

### Fix

- fix regex
- disable label and env parameters when updating test run due to 500 error from API
- Fix dot and space in parameterised test, fix project dependency

## 2.3.1 (2024-03-13)

### Fix

- Fix shared run reporting into new test run
- Fix/workarround of the incorreclty processed parameterised test on API

## 2.3.0 (2024-03-11)

### Feat

- Add TESTOMATIO_RUN to support test runs created on testomatio
- Add https://www.conventionalcommits.org/en/v1.0.0/ support

### Fix

- Fix to check testomatio session
- Allow all pytest hooks execution when running sync command that run before pytest_runtestloop (actual tests)
- Fix syncing local test with testomatio that are imported in a custom folder (on testomatio end)

## 2.1.0 (2024-03-07)

## 2.0.0 (2024-03-05)

## 1.7.0 (2024-02-26)

## 1.6.0 (2024-02-21)

## 1.5.0 (2024-02-12)

## 1.4.0 (2024-02-06)

## 1.3.0 (2023-12-06)

## 1.2.8 (2023-12-06)

## 1.2.5 (2023-10-21)

## 1.2.4 (2023-09-05)

## 1.2.3 (2023-09-03)

## 1.2.0 (2023-08-20)

## 1.1.1 (2023-08-17)

## 1.0.9 (2023-07-31)
