from __future__ import annotations

from django.utils.safestring import SafeString

from djangospice.widgets.exceptions import WidgetNotVisible

from .builder import WidgetBuilder
from .cache import WidgetCache
from .widget import Widget
from .placeholder import Placeholder



class WidgetRenderer:


    def __init__(self, widget: Widget) -> None:
        """
        Initialize the WidgetExecutor.

        Args:
            widget: The widget instance to execute.
        """
        self.widget = widget

    def render(self) -> SafeString:
        self.check_visibility()
        
        if self.widget.lazy and not self.widget.is_lazy_fetch:
            return self.placeholder()

        cached_content = self.get_cached()

        if cached_content is not None:
            return cached_content

        content = self.compile()
        self.cache(content)

        return content
    
    def placeholder(self) -> SafeString:
        """Spawns an internal wrapper loop executing the placeholder state framework."""
        placeholder = Placeholder(
            request=self.widget.request,
            target_id=self.widget.id,
            target_url=self.widget.endpoint,
            target_title=self.widget.title,
        )
        # Recursively run via fresh processing instance
        return WidgetRenderer(placeholder).render()

    def compile(self) -> SafeString:
        """
        Delegate the widget rendering to the WidgetBuilder.

        Returns:
            The rendered HTML SafeString.
        """
        return WidgetBuilder(self.widget).build()

    def check_visibility(self) -> None:
        """
        Ensure the widget is visible to the current user/context.

        Raises:
            WidgetNotVisible: If `widget.visible()` evaluates to False.
        """
        if not self.widget.visible():
            raise WidgetNotVisible(
                f"Widget '{self.widget.name}' (`{self.widget.__class__.__name__}`) "
                "is not visible in the current context."
            )

    def get_cached(self) -> SafeString | None:
        """
        Retrieve cached widget content.

        Returns:
            The cached SafeString HTML if it exists, None otherwise.
        """
        return WidgetCache.get(self.widget)

    def cache(self, content: SafeString) -> None:
        """
        Store the rendered widget content in the cache.

        Args:
            content: The rendered HTML SafeString to store.
        """
        WidgetCache.set(self.widget, content)

    def invalidate_cache(self) -> None:
        """
        Remove the current widget's cached response.
        """
        WidgetCache.delete(self.widget)
