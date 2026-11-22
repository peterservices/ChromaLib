from pydantic import BaseModel, ConfigDict


class ValidateBaseModel(BaseModel):
    """
    A BaseModel with `validate_assignment` enabled.
    """
    model_config = ConfigDict(validate_assignment=True)
