from typing import Self

from pydantic import field_validator

from .basemodel import ValidateBaseModel


class Color(ValidateBaseModel):
    """
    An RGB float color with added support for RGB integer and BGR decimal colors.

    Supports addition, subtraction, multiplication, and division.
    Please note that float color values are automatically clamped between 0 and 1.
    """
    red: float = 0.0
    green: float = 0.0
    blue: float = 0.0

    def __add__(self: Self, other: "Color") -> "Color":
        try:
            return Color(red=self.red + other.red, green=self.green + other.green, blue=self.blue + other.blue)
        except AttributeError:
            raise NotImplementedError from None

    def __sub__(self: Self, other: "Color") -> "Color":
        try:
            return Color(red=self.red - other.red, green=self.green - other.green, blue=self.blue - other.blue)
        except AttributeError:
            raise NotImplementedError from None

    def __mul__(self: Self, other: "Color") -> "Color":
        try:
            return Color(red=self.red * other.red, green=self.green * other.green, blue=self.blue * other.blue)
        except AttributeError:
            raise NotImplementedError from None

    def __truediv__(self: Self, other: "Color") -> "Color":
        try:
            # Set the color to 1 if division by 0 is attempted
            red = 1 if other.red == 0 else self.red / other.red
            green = 1 if other.green == 0 else self.green / other.green
            blue = 1 if other.blue == 0 else self.blue / other.blue
            return Color(red=red, green=green, blue=blue)
        except AttributeError:
            raise NotImplementedError from None

    @property
    def BGR_decimal(self: Self) -> int:
        """
        The color as a BGR decimal between 0 and 16777215.
        """
        int_color = self.RGB_int
        return int_color[2] * 256 ** 2 + int_color[1] * 256 + int_color[0]

    @property
    def RGB_float(self: Self) -> tuple[float, float, float]:
        """
        The color as RGB floats between 0 and 1.
        """
        return (self.red, self.green, self.blue)

    @property
    def RGB_int(self: Self) -> tuple[int, int, int]:
        """
        The color as RGB integers between 0 and 255.
        """
        return (round(self.red * 255), round(self.green * 255), round(self.blue * 255))

    @BGR_decimal.setter
    def BGR_decimal(self: Self, value: int) -> None:
        self.RGB_int = (value % 256, (value // 256) % 256, (value // 256 ** 2) % 256)

    @RGB_float.setter
    def RGB_float(self: Self, values: tuple[float, float, float]) -> None:
        self.red = values[0]
        self.green = values[1]
        self.blue = values[2]

    @RGB_int.setter
    def RGB_int(self: Self, values: tuple[int, int, int]) -> None:
        self.red = values[0] / 255
        self.green = values[1] / 255
        self.blue = values[2] / 255

    @field_validator("red", "blue", "green", mode="after")
    @classmethod
    def validate_colors(cls, value: float) -> float:
        return max(0.0, min(value, 1.0)) # Clamp color values between 0 and 1
