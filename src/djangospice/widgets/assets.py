from dataclasses import dataclass, field

@dataclass
class AssetRegistry:
    js: set[str] = field(default_factory=set)
    css: set[str] = field(default_factory=set)

    def add(self, js: list[str] = None, css: list[str] = None):
        if js: self.js.update(js)
        if css: self.css.update(css)