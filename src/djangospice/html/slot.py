from django.utils.safestring import SafeString

class Slot:
    """A renderable named component slot."""

    def __init__(self, component, name: str):
        from djangospice.html.component import Component
        self.component: Component = component
        self.name = name

    def get_children(self) -> tuple:
        return self.component.get_slot(self.name)

    def render(self) -> SafeString:
        return self.component.render_children(self.get_children())

    def __html__(self) -> SafeString:
        return self.render()

    def __str__(self) -> str:
        return str(self.render())

    def __bool__(self) -> bool:
        return bool(self.get_children())

    def __len__(self) -> int:
        return len(self.get_children())

    def __iter__(self):
        return iter(self.get_children())