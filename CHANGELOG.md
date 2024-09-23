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

### Feat

- Fixed report final handling with pytest-xdist
- Small code refactoring

## 2.5.0 (2024-03-11)

### Feat

- Plugin code refactored
- Introduced ENV variable `TESTOMATIO_CODE_STYLE` to select code style formating **PEP8** or don't format at all
- Updated pytest version supported to 8+
- Set parallel run as default parameter. ENV variable `TESTOMATIO_SHARED_RUN` is not needed
- Introduced sync lock to be used with pytest-xdist. Env variable `TESTOMATIO_TITLE` becomes optional

### Fix

- Fixed NPE when some params not set
- Fixed pytest exception with using **xdist** lib
- Fixed test parameters transfer for DDT tests


## 2.2.0 (2024-03-11)

### Feat

- Add TESTOMATIO_RUN to support test runs created on testomatio
- Add https://www.conventionalcommits.org/en/v1.0.0/ support

### Fix

- Fix syncing local test with testomatio that are imported in a custom folder (on testomatio end)
- Fix test run completion
- Fix to check testomatio session
- Allow all pytest hooks execution when running sync command that run before pytest_runtestloop (actual tests)
- Fix shared run reporting into new test run
- Fix/workarround of the incorreclty processed parameterised test on API
- Fix dot and space in parameterised test, fix project dependency

## 2.1.0 (2024-03-07)

### Feat

- Added support for `TESTOMATIO_TITLE`, `TESTOMATIO_SHARED_RUN` and `TESTOMATIO_LABEL`

## 2.0.0 (2024-03-05)

### Feat

- Align naming with Testomat.io branding
- add --directory option to import test into specific directory in testomat.io

## 1.7 (2024-02-26)

### Fix

- Fixes parameterized test sync and report

### 1.6.0 (2024-02-21)

### Feat

- Add helped to attach test artifacts
- Expose environment variables to provide access to cloud storage
- Update readme

### Fix

- Testomaito not longer supports nested test suites. Suites could be only in a folder.


### 1.5.0 (2024-02-12)

### Fix
- Fixes artifacts in fixtures lifecycle
- Earlier, artifacts added in pytest fixtures where skipped by analyser

### 1.4.0 (2024-02-06)

### Feat

- Adds `--create`, `--no-detached`, `--keep-structure`, `--no-empty`,  for compatibility with original Testomatio check-tests
- Improves file update so it doesn't cause code style changes

### Fix
- Fixes artifacts uploads and test sync with Testomatio
- Fixes test id resolution when syncing local test with Testomatio
- Fixes test id when sending test into test run

### 1.3.0 (2023-12-06)

### Fix

- [issue 5](https://github.com/Ypurek/pytest-analyzer/issues/5) - connection issues not blocking test execution anymore

### 1.2.8 (2023-12-06)

### Fix

- [issue 4](https://github.com/Ypurek/pytest-analyzer/issues/4) - Analyzer's execution order

### 1.2.5 (2023-10-21)

### Feat

- added env variable `TESTOMATIO_RUNGROUP_TITLE` to group test runs

### Fix

- fixed serialization issue for update test status example

### 1.2.4 (2023-09-05)

### Fix

- improved parametrized tests reporting
- now parameters are passed to example attribute in the report

### 1.2.3 (2023-09-03)

### Fix

- fixed issue with test artifacts when no credentials provided, test artifacts will not be uploaded and no issue raised

### 1.2.0 (2023-08-20)

### Fix

- code refactored (Testomatio.io team review)
- simplified authentication. Only API key needed
- moved API key from pytest.ini to environment variable
- S3 credentials now read from testomat.io API, no local configuration needed
- Prettified test names in testomat.io

### 1.1.1 (2023-08-17)

### Feat

- added artifacts support (screenshots, logs) to test report

### 1.0.9 (2023-07-31)

### Feat
- first public release
- test analyzer able to sync tests with testomat.io
- test analyzer able to add test ids to tests
- test analyzer able to submit test results to testomat.io