
from typing import Any, TypeVar

T = TypeVar('T')

class InheritableType:
    """
    Represents an inheritable type being inherited or introduced.
    """
    def __init__(self, name: str, value: Any):
        """
        Initializes an inheritable type with a name and value.

        Args:
            name (str): The name of the type.
            value (Any): The value of the type.
        """
        self.name = name
        self.value = value

    def get_name(self) -> str:
        """
        Gets the name of the type.

        Returns:
            str: The name of the type.
        """
        return self.name

    def get_value(self) -> Any:
        """
        Gets the value of the type.

        Returns:
            Any: The value of the type.
        """
        return self.value

    def set_value(self, value: Any) -> None:
        """
        Sets the value of the type.

        Args:
            value (Any): The new value of the type.
        """
        self.value = value

    def __eq__(self, other: object) -> bool:
        """
        Checks if two InheritableType objects are equal.

        Args:
            other (object): The object to compare with.

        Returns:
            bool: True if the objects are equal, False otherwise.
        """
        if not isinstance(other, InheritableType):
            return False
        return self.name == other.name and self.value == other.value

    def __hash__(self) -> int:
        """
        Gets the hash value of the type.

        Returns:
            int: The hash value of the type.
        """
        return hash((self.name, self.value))

    def __repr__(self) -> str:
        """
        Gets the string representation of the type.

        Returns:
            str: The string representation of the type.
        """
        return f"InheritableType(name={self.name}, value={self.value})"
