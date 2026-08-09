from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from django.core.exceptions import PermissionDenied

from djangospice.html.attributes import HTMXAttributes
from djangospice.response.response import Response

from .metaclass import ActionMetaclass
from .context import ActionContext


class Action(ABC, metaclass=ActionMetaclass):
    """
    Base executable widget action.
    """

    # ------------------------------------------------------------------
    # Identity
    # ------------------------------------------------------------------

    name: ClassVar[str | None] = None
    label: ClassVar[str | None] = None

    # ------------------------------------------------------------------
    # Presentation
    # ------------------------------------------------------------------

    icon: ClassVar[str | None] = None
    description: ClassVar[str | None] = None
    css_class: ClassVar[str | None] = None

    order: ClassVar[int] = 100
    groups: ClassVar[str | tuple[str, ...]] = ()

    # ------------------------------------------------------------------
    # Behaviour
    # ------------------------------------------------------------------

    method: ClassVar[str] = "POST"
    permission: ClassVar[str | None] = None
    confirm: ClassVar[str | None] = None

    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def visible(self, context: ActionContext) -> bool:
        return True

    def enabled(self, context: ActionContext) -> bool:
        return True

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def authorize(self, context: ActionContext) -> None:
        """
        Raise PermissionDenied if execution is not allowed.
        """

    def before_execute(self, context: ActionContext) -> None:
        """
        Hook before execute().
        """

    def after_execute(self, context: ActionContext) -> None:
        """
        Hook after execute().
        """

    # ------------------------------------------------------------------
    # HTMX
    # ------------------------------------------------------------------

    def htmx(self, context: ActionContext) -> HTMXAttributes:
        """
        Build HTMX attributes required to invoke this action.
        """

        return (
            HTMXAttributes()
            .request(
                method=self.method,
                url=context.widget.endpoint,
            )
            .with_vals(action=self.name)
        )
        
    def dispatch(self, context: ActionContext) -> Response:

        if not self.enabled(context):
            raise PermissionDenied(
                f"Action '{self.name}' is disabled."
            )

        self.authorize(context)

        self.before_execute(context)

        response = self.execute(context)

        self.after_execute(context)

        return response

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------

    @abstractmethod
    def execute(self, context: ActionContext) -> Response:
        """
        Execute the action and return a Response.
        """
        raise NotImplementedError
    
    