"""Utilities for building LLM prompts from Pydantic schema definitions."""

import inspect
from typing import Any, get_args, get_origin
from pydantic import BaseModel
from pydantic.fields import FieldInfo


def _type_name(annotation: Any) -> str:
    """Return a human-readable type string for a field annotation."""
    origin = get_origin(annotation)
    if origin is list:
        args = get_args(annotation)
        inner = _type_name(args[0]) if args else "any"
        return f"List[{inner}]"
    if origin is type(None):
        return "null"
    # Handle Optional (Union[X, None])
    try:
        from typing import Union
        if origin is Union:
            args = [a for a in get_args(annotation) if a is not type(None)]
            return f"Optional[{_type_name(args[0])}]" if args else "Optional"
    except ImportError:
        pass
    if inspect.isclass(annotation) and issubclass(annotation, BaseModel):
        return annotation.__name__
    name = getattr(annotation, "__name__", None)
    return name if name else str(annotation)


def _field_required(field_info: FieldInfo) -> bool:
    """Return True if the field has no default (i.e. it is required)."""
    return field_info.default is None and field_info.default_factory is None  # type: ignore[misc]


def schema_to_prompt(models: list[type[BaseModel]]) -> str:
    """Generate a human-readable schema description from a list of Pydantic model classes.

    Each model is rendered as a markdown section with one bullet per field, including
    the field type, whether it is required, and its description string.

    Args:
        models: Ordered list of Pydantic BaseModel subclasses to document.
            Dependency order matters — reference types should appear before the
            models that use them so the reader understands the structure.

    Returns:
        A markdown-formatted string describing the schema.
    """
    sections: list[str] = []

    for model in models:
        lines: list[str] = [f"### {model.__name__}"]
        for field_name, field_info in model.model_fields.items():
            annotation = model.__annotations__.get(field_name, Any)
            type_str = _type_name(annotation)
            description = field_info.description or "(no description)"
            required_tag = " *(required)*" if _field_required(field_info) else ""
            lines.append(f"- **`{field_name}`** `{type_str}`{required_tag}: {description}")
        sections.append("\n".join(lines))

    return "\n\n".join(sections)
