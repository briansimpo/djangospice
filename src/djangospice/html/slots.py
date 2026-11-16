from djangospice.html.slot import Slot


class Slots:
    """Public interface for a component's named slots."""

    def __init__(self, component):
        from djangospice.html.component import Component
        self.component: Component = component

    def __getitem__(self, name: str) -> Slot:
        if name not in self.component._slots:
            raise KeyError(name)

        return Slot(self.component, name)

    def __getattr__(self, name: str) -> Slot:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(
                f"Slot '{name}' does not exist."
            ) from None

    def __contains__(self, name: str) -> bool:
        return name in self.component._slots

    def __iter__(self):
        return iter(self.component._slots)

    def __len__(self) -> int:
        return len(self.component._slots)

    def keys(self):
        return self.component._slots.keys()

    def values(self):
        return (self[name] for name in self)

    def items(self):
        return ((name, self[name]) for name in self)