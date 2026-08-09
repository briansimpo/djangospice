from dataclasses import dataclass

from djangospice.core.serializable import Serializable


@dataclass(slots=True, kw_only=True)
class Document(Serializable):

    filename: str | None = None

    content_type: str | None = None

    disposition: str = "inline"

    title: str | None = None