from __future__ import annotations

from dataclasses import dataclass

from django.db import models


@dataclass(frozen=True)
class InlineRelation:
    name: str
    parent_model: type[models.Model]
    model: type[models.Model]
    foreign_key: models.ForeignKey
    relation: object

    @property
    def fk_name(self) -> str:
        return self.foreign_key.name

    @property
    def is_one_to_one(self) -> bool:
        return self.relation.one_to_one


def get_inline_relations(parent_model: type[models.Model]) -> list[InlineRelation]:
    if not isinstance(parent_model, type) or not issubclass(
        parent_model, models.Model
    ):
        raise TypeError("parent_model must be a Django model class.")

    relations = []

    for relation in parent_model._meta.get_fields():
        if not relation.auto_created or relation.concrete:
            continue

        if relation.hidden:
            continue

        if not (relation.one_to_many or relation.one_to_one):
            continue

        relations.append(
            InlineRelation(
                name=relation.get_accessor_name(),
                parent_model=parent_model,
                model=relation.related_model,
                foreign_key=relation.field,
                relation=relation,
            )
        )

    return relations