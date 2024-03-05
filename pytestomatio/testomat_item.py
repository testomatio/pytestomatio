class TestomatItem:
    id: str
    title: str
    file_name: str

    def __init__(self, id: str, title: str, file_name: str):
        self.id = id
        self.title = title
        self.file_name = file_name

    def __str__(self) -> str:
        return f'TestomatItem: {self.id} - {self.title} - {self.file_name}'

    def __repr__(self):
        return f'TestomatItem: {self.id} - {self.title} - {self.file_name}'



