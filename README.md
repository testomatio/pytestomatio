[![Support Ukraine Badge](https://bit.ly/support-ukraine-now)](https://github.com/support-ukraine/support-ukraine)

# testomat.io plugin for pytest
A powerful pytest plugin that integrates your tests with testomat.io platform for test management, reporting and analytics

## Features
- ✅ Sync tests with testomat.io
- 📊 Real-time test execution reporting
- 🏷️ Test labeling and categorization
- 📁 Test run grouping and environments
- 📎 Artifact management with S3 integration
- 🔍 Advanced filtering and debugging

## uses testomat.io API:

- https://testomatio.github.io/check-tests/ - for sync
- https://testomatio.github.io/reporter/ - for reporting

## Table of Contents
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Advanced Usage](#advanced-usage)
  - [Core commands](#core-commands)
  - [Additional options](#additional-options)
  - [Configuration](#configuration-with-environment-variables)
  - [Test artifacts](#submitting-test-artifacts)
  - [User functions](#user-functions)
  - [Cross-Platform Testing](#cross-platform-testing)
- [Contributing](#contributing)

## Installation
Prerequisites:
 - Python 3.10+
 - Pytest 6.2.5+
 - Active [testomat.io](https://testomat.io) account 

Install via pip:
```bash
pip install pytestomatio
```

## Quick Start

### Get your API token
1. Login to testomat.io
2. Create project or go to existing project
3. Click on "Import Tests from Source Code"
4. Copy your project token(starts with "tstmt_")
### Sync tests
Synchronize tests to testomat.io:
```bash
TESTOMATIO=your_token pytest --testomatio sync
```
### Report tests
Execute tests and send results to testomat.io:
```bash
TESTOMATIO=your_token pytest --testomatio report
```
### Example of test

To make the experience more consistent, it uses standard pytest markers.  
testomat.io test id is a string value that starts with `@T` and has 8 symbols after.

```python
from pytest import mark


@mark.testomatio('@T96c700e6')
def test_example():
    assert 2 + 2 == 4
```

## Advanced usage

### Core commands
#### Synchronization
Synchronize tests to testomat.io and get back test id.

```bash
pytest --testomatio sync
```
Clarification:
- tests will not be executed
- tests can be synced even without `@pytest.mark.testomatio('@T96c700e6')` decorator.
- test title in testomat.io == test name in pytest
- test suit title in testomat.io == test file name in pytest

##### Tagging tests on sync
Since a Python test function name can't contain special characters like `@tag`, tags are
assigned via the built-in `testomatio_tags` marker, and are added to the test title on sync:

```python
import pytest


@pytest.mark.testomatio_tags("smoke", "regression")
def test_example():
    assert 2 + 2 == 4
```

This produces a test titled `Example @smoke @regression` in testomat.io.

You can also reuse plain pytest markers as tags by allowlisting their names via the
`TESTOMATIO_TAG_MARKERS` env var (comma-separated). We don't pick up every `pytest.mark.*`
automatically, since that would also catch pytest/plugin service markers like `parametrize`,
`skip`, `usefixtures`, etc. - only markers explicitly listed are treated as tags:

```bash
export TESTOMATIO_TAG_MARKERS=smoke,regression
```

```python
import pytest


@pytest.mark.smoke
def test_example():
    assert 2 + 2 == 4
```

This produces a test titled `Example @smoke` in testomat.io.


#### Clean up
Remove all test ids from source code. Tests will not be executed

```bash
pytest --testomatio remove
```

#### Report

Run pytest and send test results into testomat.io.  
Test can be sent to testomat.io without ids in your test code. If testomat.io failed to match tests by title, it will create
new tests for the run

```bash
pytest --testomatio report
```

#### Debug

Run pytest with debug parameter to get test data collected in metadata.json file

```bash
pytest --testomatio debug
```

#### Launch
Create empty run and obtain its RUN_ID from testomat.io.

```bash
pytest --testomatio launch
```

#### Finish
Finish running or scheduled run on testomat.io. 
**TESTOMATIO_RUN_ID** environment variable is required.

```bash
TESTOMATIO_RUN_ID=***run_id*** pytest --testomatio finish
```


### Additional options
#### Submitting Test Run Environment
To configure test environment, you can use additional option **testRunEnv**. The configured environment will be added to the test report. Use it with **report** command:

```bash
pytest --testomatio report --testRunEnv "windows11,chrome,1920x1080"
```

Environment values are comma separated, please use double quotation.

#### Clearing empty test suites
To automatically clean empty test suites on testomat.io you can use **no-empty** option. Use it with
**sync** command:
```bash
pytest --testomatio sync --no-empty
```

#### Disable detaching tests
If a test from a previous import was not found on next import it is marked as "detached".
This is done to ensure that deleted tests are not staying in Testomatio while deleted in codebase.
To disable this behaviour and don't mark anything as detached on import use **no-detach** option. Use it with **sync** command:

```bash
pytest --testomatio sync --no-detach
```

#### Keeping original file structure
 By default, when importing tests, testomat.io does not preserve original file structure. Use option **keep-structure** with **sync** command to keep original file structure:
```bash
pytest --testomatio sync --keep-structure
```
#### Import into given directory
By default, tests are imported into the root of the project.
You can use **directory** option to specify directory to use for test file structure. Use this option with **sync** command:
 ```bash
pytest --testomatio sync --directory imported_tests
```
Note: **keep-structure** option takes precedence over **directory** option. If both are used **keep-structure** will be used.
#### Filter tests
You can filter tests that will be reported, using **testomatio-filter** option. Filter format: *filter_type=value*. Use this option with **report** command.

**Note**: Only one filter can be applied at a time 

**Filter types**:
 - **test_id**. Filter test by Testomat.io id. You can pass single or multiple ids for this filter using *|* as separator. Ex: "test_id=@T3h2r432|T2e34e342|b234fr254"
 - **plan**. Filter by plan id.
 - **jira**. Filter by jira issue id.
 - **tag**. Filter by tag name.
 - **label**. Filter by label name or label-id.

**Examples**:

**Filter by test id**
```bash
pytest --testomatio report --testomatio-filter="test_id=Tc0880217|Tfd1c595c"
```
**Filter by tag**

If your test have '@smoke' tag on testomat.io, then value for this filter == smoke
```bash
pytest --testomatio report --testomatio-filter="tag=smoke"
```

**Filter by label**

```bash
# by label name
pytest --testomatio report --testomatio-filter="label=important"

# by label id
pytest --testomatio report --testomatio-filter="label=important-f435-e"

# based on Severity type
pytest --testomatio report --testomatio-filter="label=severity-f124r-3:⚠️ Critical"
```

**Filter by plan**

```bash
pytest --testomatio report --testomatio-filter="plan=ca34gf3t"
```

**Filter by Jira Issue**

```bash
pytest --testomatio report --testomatio-filter="jira=TES1"
```

### Submitting Test Steps

The plugin supports dividing tests into separate, trackable steps. When reporting to testomat.io, you can view detailed information for each step including execution status, duration, and any errors that occurred.

**Important**: This plugin only supports **reporting** test steps to testomat.io during test execution. Test steps cannot be imported to testomat.io using **sync** option. Steps reported for skipped and failed test by default. To enable steps reporting for passed tests use **TESTOMATIO_STEPS_PASSED** env variable.

Test steps can be implemented using either decorators or context managers, giving you flexibility in how you structure your tests.

**Error Handling**: If a step fails, the error is captured and reported to testomat.io while the test execution continues with remaining steps.

**Parameters**:
```
@step_function(
    title = "Step1", # Step name displayed in testomat.io
    category = "user" # Optional: categorize steps(user, system, framework)
)
with step(
    title = "Step1", # Step name displayed in testomat.io
    category = "user" # Optional: categorize steps(user, system, framework)
)

```

**Example**:
```python
import pytest
from pytestomatio.utils.steps import step, step_function

class Book:
    def __init__(self, author, text):
        self.author = author
        self.text = text
        
    def read(self):
        return self.text

# decorator 
@step_function(title='Check author step', category='user')
def check_author(author_name, expected_name):
    assert author_name == expected_name

def test_book_create():
    author_name = 'David Ket'
    # context manager
    with step(title='Book create', category='user'):
        book = Book(author_name, 'text')
        assert book
        check_author(book.author, author_name)

# nested steps also supported
def test_book_read():
    text = 'book text'
    author_name = 'David Ket'
    
    with step(title='Read book'):
        with step(title='Book create', category='user'):
            book = Book(author_name, 'text')
            assert book
            check_author(book.author, author_name)
        assert book.read() == text
```

**Note:** Step is registered when the step code is executed. Therefore, if test mark as skipped(not executed at all) or test code execution stops before step code is executed, step will not be attached to test:
```python
import pytest
from pytestomatio.utils.steps import step

# Step will not be added in report
@pytest.mark.skip
def test_skipped():
    with step('Step1', 'user'):
        assert True

# Step will not be added in report
def test_exception_raised():
    raise ValueError()
    with step('Step1', 'user'):
        assert True

# Step will not be added in report
def test_early_skip():
    pytest.skip()
    with step('Step1', 'user'):
        assert True

# Step1 will be added in report, Step2 will not be
def test_nested_step_skip_or_exception():
    with step('Step1', 'user'):
        with step('Step2', 'user'):
            pytest.skip() # or AttributeError()
```


### Configuration with environment variables
You can use environment variable to control certain features of testomat.io. Environment variables can be either passed inline, or from .env file.

#### Basic configuration
| Env variable             | What it does                                                                                                                                                                                                          | Examples                                                                         |
|--------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| TESTOMATIO               | Provides token for pytestomatio to access and push data to testomat.io. Required for **sync** and **report** commands                                                                                                 | TESTOMATIO=tstmt_***** pytest --testomatio sync                                  |
| TESTOMATIO_SYNC_LABELS   | Assign labels to a test case when you synchronise test from code with testomat.io. Labels must exist in project and their scope must be enabled for tests                                                             | TESTOMATIO_SYNC_LABELS="number:1,list:one,standalone" pytest --testomatio report |
| TESTOMATIO_CODE_STYLE    | Code parsing style for test synchronization. If you are not sure, don't set this variable. Default value is 'default'                                                                                                 | TESTOMATIO_CODE_STYLE=pep8 pytest --testomatio sync                              |
| TESTOMATIO_TAG_MARKERS   | Allowlist of bare pytest marker names to treat as tags and append to the test title on **sync** (comma-separated). See [Tagging tests on sync](#tagging-tests-on-sync)                                               | TESTOMATIO_TAG_MARKERS=smoke,regression pytest --testomatio sync                 |
| TESTOMATIO_CI_DOWNSTREAM | If set, pytestomatio will not set or update build url for a test run. This is useful in scenarios where build url is already set in the test run by Testomat.io for test runs that a created directly on Testomat.io. | TESTOMATIO_CI_DOWNSTREAM=true pytest --testomatio report                         |
 | TESTOMATIO_URL           | Customize testomat.io url                                                                                                                                                                                             | TESTOMATIO_URL=https://custom.com/ pytest --testomatio report                    |
 | BUILD_URL                | Overrides build url run tests                                                                                                                                                                                         | BUILD_URL=http://custom.com/ pytest --testomatio report                          |
 | TESTOMATIO_NO_TIMESTAMP  | Disable automatic timestamp generation for test results. Use this option if you run tests in parallel on different machines where time is not synchronized                                                            | TESTOMATIO_NO_TIMESTAMP=True pytest --testomatio report                          |
 | TESTOMATIO_MAX_REQUEST_FAILURES                | Sets the max number of attempts to send a request to the Testomat.io API. Default is 5 attempts.                                                                                                                      | TESTOMATIO_MAX_REQUEST_FAILURES=10 pytest --testomatio report                    |
 | TESTOMATIO_REQUEST_INTERVAL                | Sets the interval between API requests in seconds. Default is 5 sec.                                                                                                                                                  | TESTOMATIO_REQUEST_INTERVAL=2 pytest --testomatio report                         |


#### Test Run configuration
| Env variable             | What it does                                                                                                                                                                     | Examples                                                                                                    |
|--------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| TESTOMATIO_TITLE         | Name of a test run to create on testomat.io                                                                                                                                      | TESTOMATIO_TITLE="Nightly Smoke Tests" pytest --testomatio report                                           |
| TESTOMATIO_RUN_ID        | Id of existing test run to use for sending test results to                                                                                                                       | TESTOMATIO_RUN_ID=98dfas0 pytest --testomatio report                                                        |
| TESTOMATIO_RUNGROUP_TITLE | Create a group (folder) for a test run. If group already exists, attach test run to it                                                                                           | TESTOMATIO_RUNGROUP_TITLE="Release 2.0" pytest --testomatio report                                          |
| TESTOMATIO_ENV           | Assign environment to a test run, env variant of **testRunEnv** option. Has a lower precedence than **testRunEnv** option.                                                       | TESTOMATIO_ENV="linux,chrome,1920x1080" pytest --testomatio report                                          |
| TESTOMATIO_LABEL         | Assign labels to a test run. Labels must exist in project and their scope must be enabled for runs                                                                               | TESTOMATIO_LABEL="smoke,regression" pytest --testomatio report                                              |
| TESTOMATIO_JIRA_ID        | Assigns Test Run to Jira Issue. Note: Issue must exist on Jira and Jira Integration must be configured for project on Testomat.io | TESTOMATIO_JIRA_ID=TES-1 pytest --testomatio report                |
| TESTOMATIO_UPDATE_CODE         | Send code of your test to Testomat.io on each run. If not enabled(default) assumes the code is pushed using **sync** command                                                     | TESTOMATIO_UPDATE_CODE=True pytest --testomatio report                                                      |
| TESTOMATIO_EXCLUDE_SKIPPED         | Exclude skipped tests from the report                                                                                                                                            | TESTOMATIO_EXCLUDE_SKIPPED=1 pytest --testomatio report                                                     |
| TESTOMATIO_PUBLISH            | Publish run after reporting and provide a public URL                                                                                                                             | TESTOMATIO_PUBLISH=true pytest --testomatio report                                                          |
| TESTOMATIO_PROCEED            | Do not finalize the run                                                                                                                                                          | TESTOMATIO_PROCEED=1 pytest --testomatio report                                                             |
| TESTOMATIO_STACK_PASSED       | Enables logs for passed tests. Disabled by default.                                                                                                                              | TESTOMATIO_STACK_PASSED=true pytest --testomatio report                                                          |
| TESTOMATIO_SHARED_RUN         | Report parallel execution to the same run matching it by title. If the run was created more than 20 minutes ago, a new run will be created instead.                              | TESTOMATIO_TITLE="Run1" TESTOMATIO_SHARED_RUN=1 pytest --testomatio report                                  |
| TESTOMATIO_SHARED_RUN_TIMEOUT | Changes timeout of shared run. After timeout, shared run won`t accept other runs with same name, and new runs will be created. Timeout is set in minutes, default is 20 minutes. | TESTOMATIO_TITLE="Run1" TESTOMATIO_SHARED_RUN=1 TESTOMATIO_SHARED_RUN_TIMEOUT=10 pytest --testomatio report |
| TESTOMATIO_DISABLE_ARTIFACTS  | Disables artifacts uploading during testrun.                                                                                                                                     | TESTOMATIO_DISABLE_ARTIFACTS=1 pytest --testomatio report                                                   |
| TESTOMATIO_EXCLUDE_FILES_FROM_REPORT_GLOB_PATTERN            | Excludes tests from report using glob patterns. You can specify multiple patterns using **;** as separator                                                                       | TESTOMATIO_EXCLUDE_FILES_FROM_REPORT_GLOB_PATTERN="**/*_auth.py;directory" pytest --testomatio report      |
| TESTOMATIO_CREATE             | Create test which are not yet exist in a project                                                                                                                                 | TESTOMATIO_CREATE=1 pytest --testomatio report                                                              |
| TESTOMATIO_WORKDIR            | Specify a custom working directory for relative file paths in test reports. When tests are created with **TESTOMATIO_CREATE=1**, file paths will be relative to this directory.  | TESTOMATIO_WORKDIR=new_dir pytest --testomatio report                                                       |
| TESTOMATIO_DISABLE_BATCH_UPLOAD | Disables batch uploading and uploads each test result one by one.                                                                                                                | TESTOMATIO_DISABLE_BATCH_UPLOAD=True pytest --testomatio report                                             |
| TESTOMATIO_BATCH_SIZE | Changes size of batch for batch uploading. Default is 50. Maximum is 100.                                                                                                        | TESTOMATIO_BATCH_SIZE=15 pytest --testomatio report                                                         |


#### S3 Bucket configuration
| Env variable         | Description                           |
|----------------------|---------------------------------------|
| S3_REGION            | Your S3 region                        |
| S3_ACCESS_KEY_ID     | Your S3 access key ID                 |
| S3_SECRET_ACCESS_KEY | Your S3 secret access key             |
| S3_BUCKET            | Your S3 bucket name                   |
| S3_ENDPOINT          | Your S3 endpoint                      |
| S3_BUCKET_PATH       | Path to your bucket                   |
| TESTOMATIO_PRIVATE_ARTIFACTS       | Store artifacts in a bucket privately |


### pytest.ini
In case you are using private testomat.io service, create `pytest.ini` file in your project root directory. Specify
testomat.io url in it

```ini
[pytest]
testomatio_url = https://app.testomat.io

```

### Submitting Test Artifacts

testomat.io does not store any screenshots, logs or other artifacts.

In order to manage them it is advised to use S3 Buckets (GCP Storage).
https://docs.testomat.io/usage/test-artifacts/

Analyser needs to be aware of the cloud storage credentials.
There are two options:
1. Enable **Share credentials with testomat.io Reporter** option in testomat.io Settings -> Artifacts.
2. Use environment variables   `ACCESS_KEY_ID, SECRET_ACCESS_KEY, ENDPOINT, BUCKET, BUCKET_PATH, REGION`

You would need to decide when you want to upload your test artifacts to cloud storage

1) Upload page screenshot when test fails, using fixtures [reference](https://docs.pytest.org/en/latest/example/simple.html#making-test-result-information-available-in-fixtures)

```python
# content of conftest.py
import pytest
import random
import os
from typing import Dict
from pytest import StashKey, CollectReport
from playwright.sync_api import Page

phase_report_key = StashKey[Dict[str, CollectReport]]()

@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    rep = yield
    item.stash.setdefault(phase_report_key, {})[rep.when] = rep
    return rep


@pytest.fixture(scope="function")
def handle_artifacts(page: Page, request):
    yield
    report = request.node.stash[phase_report_key]
    if ("call" not in report) or report["setup"].failed or report["call"].failed:
        random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        filename = f"{random_string}.png"
        screenshot_path = os.path.join(artifacts_dir, filename)
        page.screenshot(path=screenshot_path)
        # file_path - required, path to file to be uploaded
        # file_bytes - required, bytes of the file to be uploaded
        # key - required, file name in the s3 bucket
        # bucket_name - optional,name of the bucket to upload file to. Default value is taken from testomat.io
        artifact_url = pytest.testomatio.upload_file(screenshot_path, filename)
        # or
        # artifact_url = pytest.testomatio.upload_file_object(file_bytes, key, bucket_name)
        pytest.testomatio.add_artifacts(request.node, [artifact_url])
    page.close()
```

⚠️ Please take into account s3_connector available only after **pytest_collection_modifyitems()** hook is executed.

2) If you prefer to use pytest hooks - add `pytest_runtest_makereport` hook in your `conftest.py` file.
3) Automatically upload artifacts using [add_artifact](#add-artifact) function

```python
def pytest_runtest_makereport(item, call):
    artifact_url = pytest.testomatio.upload_file(screenshot_path, filename)
    pytest.testomatio.add_artifacts([artifact_url])
```

### User functions
This functions gives you more flexibility in reporting and make your reports more powerful

**Available functions**
- [add_artifact](#add-artifact)
- [add_meta](#add-meta)
- [add_label](#add-label)
- [link_jira](#link-jira)
- [link_test](#link-test)

#### Add Artifact
Adds file to the test report. File will be uploaded during test run. 

**Note:** S3 must be configured

```python
from pytestomatio.functions import add_artifact

def test_my_test():
    path_to_file = 'path/to/file/image.png'
    add_artifact(path_to_file)
    assert True
```
#### Add Meta
Adds meta information to test. Meta information is a key:value pair(s), which is used to add additional information to the test report. E.g. browser, environment, etc.

**Note:** Test run metadata have higher priority than test metadata. 
Therefore, if the test metadata and the test run metadata have the same keys, then the values from the test run metadata will be set for these keys

```python
from pytestomatio.functions import add_meta

def test_my_test():
    add_meta({'browser': 'chrome', 'server': 'staging'})
    assert True
```

#### Add Label
Adds a label to the reported test. Unlike *meta* label will be persisted to the test case itself, not just to reported run. If the label
does not exist in Testomat.io, it will be automatically created and linked to the test during the test run.
You can pass also a label value, if the label was created as a custom field

```python
from pytestomatio.functions import add_label

def test_my_test():
    add_label('Browser')
    add_label('Area', 'Auth')
    assert True
```

#### Link Jira
Links JIRA issue IDs to the test report. This creates a connection between your test execution and JIRA issues.

```python
from pytestomatio.functions import link_jira

def test_my_test():
    link_jira('PROJ-456', 'PROJ-564')
    assert True
```

#### Link Test
Links test IDs to the current test in the report. This allows you to associate multiple test cases with the current test execution.

```python
from pytestomatio.functions import link_test

def test_my_test():
    link_test('@T5147babc', '47d31979')
    assert True
```


### Cross-Platform Testing
The plugin supports reporting the same test multiple times in a single run. This is especially useful for Cross-Platform
testing, when you run the same test on different environments. 
To use this feature you need to specify test run environment through 
**TESTOMATIO_ENV** environment variable or by using **--testRunEnv** option.
Example:
```bash
TESTOMATIO=***api_key*** TESTOMATIO_RUN_ID=***run_id*** pytest --testomatio report --testRunEnv "os:ubuntu, integration"
TESTOMATIO=***api_key*** TESTOMATIO_RUN_ID=***run_id*** pytest --testomatio report --testRunEnv "os:windowns, integration"
```
Executing these commands will include the tests in the same run, but as separate instances. Each test will contain metadata with information about the test run environment.

**Note**: Only key:value envs will be passed into tests metadata

### Attach log to test
The plugin supports manual addition of logs from the test source code. If a test has attached logs, they will be shown in Testomat.io.

To attach a log, you need to use **add_log** function from pytestomatio.utils.logging module

**Note**: By default logs are only displayed for failed tests. You can enable logs for passed tests using TESTOMATIO_STACK_PASSED env variable

Example:
```python
from pytestomatio.utils.logging import add_log

def test_addition():
    add_log(message='test started', level='DEBUG')
    value = 2+2
    assert value == 4
```

## Contributing
Use python 3.12

### Manual testing
- Run unit tests
- import into empty project
- updated test - (resync)
- test run
- test run into a folder
- test run labels, tags

1. `pip install ".[dev]"`
1. `python ./smoke.py`
1. Test things manually
1. Verify no regression bugs
1. `cz commit --prerelease beta`
1. `cz bump`
1. `git push remoteName branchName --tags`