from typing import Any

from .element import HTMLElement


def create_element_class(
    name: str,
    tag_name: str,
) -> type[HTMLElement]:
    """
    Create an HTMLElement subclass for an HTML tag.
    """
    return type(
        name,
        (HTMLElement,),
        {
            "tag_name": tag_name,
            "__module__": __name__,
        },
    )


def create_element(
    tag_name: str,
    *children: Any,
    **attributes: Any,
) -> HTMLElement:
    """
    Create an HTML element without requiring a predefined class.
    """
    return HTMLElement(
        *children,
        tag_name=tag_name,
        **attributes,
    )
