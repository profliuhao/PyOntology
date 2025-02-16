class InheritableProperty:
    def __init__(self, name: str):
        self.name = name

    def get_name(self) -> str:
        return self.name

    def equals_including_inheritance(self, other: 'InheritableProperty') -> bool:
        return self.name == other.name
