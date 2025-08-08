from typing import get_type_hints

from pydantic import BaseModel, create_model


def create_deep_partial(model: type[BaseModel]) -> type[BaseModel]:
    """Recursively create a deep partial Pydantic model."""
    fields = {}
    for name, field_type in get_type_hints(model, include_extras=True).items():
        # origin = getattr(field_type, "__origin__", None)

        if isinstance(field_type, type) and issubclass(field_type, BaseModel):
            # Recurse for nested models
            partial_field_type = create_deep_partial(field_type)
            fields[name] = (partial_field_type | None, None)
        else:
            fields[name] = (field_type | None, None)

    return create_model(f"Partial{model.__name__}", **fields)
