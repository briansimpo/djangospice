from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ClassIdentity:
    """Canonical identity of a registered class."""

    app_name: str
    class_name: str

    def __post_init__(self) -> None:
        app_name = str(self.app_name).strip().casefold()
        class_name = str(self.class_name).strip().casefold()

        if not app_name:
            raise ValueError("app_name cannot be empty.")

        if not class_name:
            raise ValueError("class_name cannot be empty.")

        object.__setattr__(self, "app_name", app_name)
        object.__setattr__(self, "class_name", class_name)

    def __str__(self) -> str:
        return f"{self.app_name}.{self.class_name}"

    def to_string(self) -> str:
        return str(self)

    @classmethod
    def build(cls, app_name: str, class_name: str) -> "ClassIdentity":
        return cls(
            app_name=app_name,
            class_name=class_name,
        )

    @classmethod
    def from_object(cls, obj: object) -> "ClassIdentity":
        return cls.build(
            app_name=obj.app_name,
            class_name=obj.class_name,
        )

    @classmethod
    def from_class(cls, klass: type) -> "ClassIdentity":
        return cls.from_object(klass)

    @classmethod
    def from_model(cls, model: type) -> "ClassIdentity":
        meta = model._meta

        return cls.build(
            app_name=meta.app_label,
            class_name=meta.model_name,
        )