class TestomatioTest:
    id: str
    title: str
    file_name: str

    def __init__(self, id: str, title: str, file_name: str):
        self.id = id
        self.title = title
        self.file_name = file_name


def parse_test_list(raw_response: dict) -> list[TestomatioTest]:
    suites = set([suite for suite in raw_response['suites'].keys() if '#' not in suite])
    result = dict()
    for key, value in raw_response['tests'].items():
        test = result.get(value)
        if test is None:
            test = {
                'name': None,
                'suite': None,
                'file': None
            }
        parts = [part for part in key.split('#') if part != '']
        if len(parts) == 1:
            test['name'] = parts[0]
        elif len(parts) == 2:
            if parts[0] in suites:
                test['suite'] = parts[0]
            test['name'] = parts[1]
        elif len(parts) == 3:
            test['file'] = parts[0]
            test['name'] = parts[-1]
        result[value] = test
    return [TestomatioTest(id, test['name'], test['file']) for id, test in result.items()]
