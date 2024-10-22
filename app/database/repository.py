from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm import selectinload, with_polymorphic, contains_eager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc, desc
from typing import Optional
from sqlalchemy.sql.expression import BinaryExpression
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Self, TypeVar, Type

T = TypeVar('T', bound='Repository')

class DatabaseQueryOrder(Enum):
    ASC = "asc"
    DESC = "desc"

@dataclass
class JoinExpression:
    model: Type[T]
    condition: Optional[BinaryExpression] = None
    outer: Optional[bool] = False
    join_from: Optional[Type[T]] = None


class Repository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, ongoing_transaction=False, return_created_model=False) -> Optional[Self]:
        self.db.add(self)
        if not ongoing_transaction:
            await self.db.commit()
        if return_created_model:
            await self.db.refresh(self)
            return self 

    async def delete(self, ongoing_transaction=False):
        await self.db.delete(self)
        if not ongoing_transaction:
            await self.db.commit()

    async def update(self, ongoing_transaction=False, **attributes):
        for attribute, value in attributes.items():
            setattr(self, attribute, value)
        if not ongoing_transaction:
            await self.db.commit()

    def build_query(
        self: T,
        polymorphic: bool = False,
        filters: Optional[list[BinaryExpression]] = None,
        load_relationships: Optional[list[InstrumentedAttribute]] = None,
        eager_load_relationships: Optional[list[InstrumentedAttribute]] = None,
        joins: Optional[list[JoinExpression]] = None,
    ) -> str:
        model_cls = type(self)
        filters = filters or []
        load_relationships = load_relationships or []
        eager_load_relationships = eager_load_relationships or []
        model_instances_to_select = with_polymorphic(model_cls, "*") if polymorphic else model_cls
        stmt = (
            select(model_instances_to_select)
            .where(*filters)
            .options(
                *[selectinload(relationship) for relationship in load_relationships],
                *[
                    contains_eager(relationship)
                    for relationship in eager_load_relationships
                ],
            )  # no chaining
        )
        if joins:
            for j in joins:
                if j.join_from:
                    stmt = stmt.join_from(
                        j.join_from, j.model, j.condition, isouter=j.outer
                    )
                else:
                    stmt = stmt.join(j.model, j.condition, isouter=j.outer)
        return stmt

    @classmethod 
    async def get_all(
        cls: Type[T],
        polymorphic: bool = False,
        filters: Optional[list[BinaryExpression]] = None,
        load_relationships: Optional[list[InstrumentedAttribute]] = None,
        eager_load_relationships: Optional[list[InstrumentedAttribute]] = None,
        order_by: Optional[InstrumentedAttribute] = None,
        order: Optional[DatabaseQueryOrder] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        joins: Optional[list[JoinExpression]] = None,
    ) -> list[T]:
        order_by = desc(order_by) if order == DatabaseQueryOrder.DESC else asc(order_by)
        model = cls()
        stmt = model.build_query(
            polymorphic=polymorphic,
            filters=filters,
            load_relationships=load_relationships,
            eager_load_relationships=eager_load_relationships,
            joins=joins,
        )
        stmt = stmt.order_by(order_by).limit(limit).offset(offset)
        selected_model_instances = await model.db.execute(stmt)
        return selected_model_instances.unique().scalars().all()

    @classmethod 
    async def get_one(
        cls: Type[T],
        polymorphic: bool = False,
        filters: Optional[list[BinaryExpression]] = None,
        load_relationships: Optional[list[InstrumentedAttribute]] = None,
        eager_load_relationships: Optional[list[InstrumentedAttribute]] = None,
        joins: Optional[list[JoinExpression]] = None,
    ) -> T:
        model = cls()
        stmt = model.build_query(
            polymorphic=polymorphic,
            filters=filters,
            load_relationships=load_relationships,
            eager_load_relationships=eager_load_relationships,
            joins=joins,
        )
        selected_model_instance = await model.db.execute(stmt)
        return selected_model_instance.scalars().first()
    
    @classmethod
    async def create_many(cls: Type[T], attributes_list: list[dict], ongoing_transaction=False):
        model = cls()
        model_instances_to_create = [cls(**attributes) for attributes in attributes_list]
        model.db.bulk_save_objects(model_instances_to_create)
        if not ongoing_transaction:
            await model.db.commit()

    @classmethod
    async def create_or_update(cls: Type[T], filters: list[BinaryExpression], **attributes):
        selected_model_instance = cls.get_one(filters=filters)
        if selected_model_instance:
            await selected_model_instance.update(**attributes)
        else:
            model_instance_to_create = cls(**attributes)
            await model_instance_to_create.create()

    