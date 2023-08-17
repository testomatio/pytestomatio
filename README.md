# Testomat.io plugin for pytest

## uses Testomat.io API:

- https://testomatio.github.io/check-tests/
- https://testomatio.github.io/reporter/

## Installation

```bash
pip install pytest-analyzer
```

## configuration

create `pytest.ini` file in your project root directory. Set next parameters:

```ini
[pytest]
testomatio_url = https://app.testomat.io ; this one is OPTIONAL
testomatio_project = 70t3da349fte ; project key is mandatory to assing tests to particular project
testomatio_email = example@test.com ; your login in testomat.io
testomatio_password = secure_password ; your password in testimat.io
```

## Usage

Run pytest with analyzer add parameter to analyze your tests, send them to testomat.io and get back test id. Tests will
not be executed

```bash
pytest --analyzer add
```

Run pytest with analyzer remove parameter to remove all test ids from your tests. Tests will not be executed

```bash
pytest --analyzer remove
```

Run pytest with analyzer sync parameter to execute tests and send the execution status to testomat.io.  
Sync can be executed even without marking tests with ids. If testomat.io failed to match tests by title, it will create
new tests for the run

```bash
pytest --analyzer sync
```

Run pytest with analyzer debug parameter to get test data collected in metadata.json file

```bash
pytest --analyzer debug
```

### Submitting Test Run Environment 

to configure test environment, you can use additional option:

```bash
pytest --analyzer sync --testRunEnv windows11,chrome,1920x1080
```

### Submitting Test Artifacts (NEW)
According documentation, Testomat.io does not store any screenshots, 
logs or other artifacts. In order to manage them it is advised to use S3 Buckets. 
https://docs.testomat.io/usage/test-artifacts/  

In order to save artifacts, next optional paramenters can be added to pytest.ini:
```ini
[pytest]
testomatio_s3_access_key_id = <access key>
testomatio_s3_secret_key_id = <secret key>
testomatio_s3_endpoint = <endpoint>
testomatio_s3_bucket = <existing bucket> (optional)
```
To send artifact to s3 bucket, next code should be added to test:
```python
# file_path - path to file to be uploaded
# file_bytes - bytes of the file to be uploaded
# key - file name in the s3 bucket
# bucket_name - name of the bucket to upload file to. If not set, bucket name from pytest.ini will be used, if set, overrides bucket name from pytest.ini
artifact_url = pytest.s3_connector.upload_file(file_path, key, bucket_name)
# or
artifact_url = pytest.s3_connector.upload_file_object(file_bytes, key, bucket_name)
```
In conftest.py file next hook can be added. set attribute testomatio_artifacts. This list will be sent to testomat.io
```python
def pytest_runtest_makereport(item, call):
   artifacts = ['url1', 'url2']
   setattr(item, 'testomatio_artifacts', artifacts)
```

Eny environments used in test run. Should be placed in comma separated list, NO SPACES ALLOWED.

### Clarifications

- tests can be synced even without `@mark.testomatio('@T96c700e6')` decorator.
- test title in testomat.io == test name in pytest
- test suit title in testomat.io == test file name in pytest

## Example of test

To make analyzer experience more consistent, it uses standard pytest markers.  
Testomat.io test id is a string value that starts with `@T` and has 8 symbols after.

```python
from pytest import mark


@mark.testomatio('@T96c700e6')
def test_example():
    assert 2 + 2 == 4
```

## Change log

### 1.1.0 - added artifacts support connector

- there is possibility to add artifacts (screenshots, logs) to test report

### 1.0.9 - first public release

- test analyzer able to sync tests with testomat.io
- test analyzer able to add test ids to tests
- test analyzer able to submit test results to testomat.io

## Roadmap

- get S3 connection details from testomat.io
- handle REST API exceptions
- improve logging

## Delivery hints

1. Do not forget update version in pyproject.toml
2. Do not forget update version in README.md
3. Follow next steps:  
   To install locally (for testing purposes)

```bash
pip install --upgrade .
```

To build package

```bash
py -m build
```

Install twine to upload package to pypi

```bash
py -m pip install --upgrade twine
```

Upload package to pypi

```bash
py -m twine upload --repository pypi dist/* --verbose
```