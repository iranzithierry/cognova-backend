from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm import selectinload, with_polymorphic, contains_eager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc, desc
from typing import Optional
from sqlalchemy.sql.expression import BinaryExpression
from sqlalchemy.dialects.postgresql import insert
from typing import Any
from dataclasses import dataclass
from enum import Enum


class DatabaseQueryOrder(Enum):
    ASC = "asc"
    DESC = "desc"

@dataclass
class JoinExpression:
    model: Any
    condition: Optional[BinaryExpression] = None
    outer: Optional[bool] = False
    join_from: Optional[Any] = None


class BaseRepository:
    def __init__(self, db: AsyncSession):
        self.__db = db

    async def insert_on_conflict_update(self, model, index_elements: list, attributes: list):
        """
            lower level method
        """
        insert_stmt = insert(model).values(
        **attributes)
        do_update_stmt = insert_stmt.on_conflict_do_update(index_elements=index_elements,
                                                           set_=attributes)
        await self.__db.execute(do_update_stmt)

    async def create(self, model_instance, ongoing_transaction=False, return_created_model=False):
        self.__db.add(model_instance)
        if not ongoing_transaction:
            await self.__db.commit()
            if return_created_model:
                await self.__db.refresh(model_instance)
                return model_instance

    async def delete(self, model_instance, ongoing_transaction=False):
        await self.__db.delete(model_instance)
        if not ongoing_transaction:
            await self.__db.commit()

    def __build_query(
        self,
        model,
        polymorphic: bool = False,
        filters: Optional[list[BinaryExpression]] = None,
        load_relationships: Optional[list[InstrumentedAttribute]] = None,
        eager_load_relationships: Optional[list[InstrumentedAttribute]] = None,
        joins: Optional[list[JoinExpression]] = None,
    ):
        filters = filters or []
        load_relationships = load_relationships or []
        eager_load_relationships = eager_load_relationships or []
        if polymorphic:
            model = with_polymorphic(model, "*")
        stmt = (
            select(model)
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

    async def _get_all(
        self,
        model,
        polymorphic: bool = False,
        filters: Optional[list[BinaryExpression]] = None,
        load_relationships: Optional[list[InstrumentedAttribute]] = None,
        eager_load_relationships: Optional[list[InstrumentedAttribute]] = None,
        order_by: Optional[InstrumentedAttribute] = None,
        order: Optional[DatabaseQueryOrder] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        joins: Optional[list[JoinExpression]] = None,
    ):
        order_by = desc(order_by) if order == DatabaseQueryOrder.DESC else asc(order_by)
        stmt = self.__build_query(
            model=model,
            polymorphic=polymorphic,
            filters=filters,
            load_relationships=load_relationships,
            eager_load_relationships=eager_load_relationships,
            joins=joins,
        )
        stmt = stmt.order_by(order_by).limit(limit).offset(offset)
        model_instances = await self.__db.execute(stmt)
        return model_instances.unique().scalars().all()

    async def _get_one(
        self,
        model,
        polymorphic: bool = False,
        filters: Optional[list[BinaryExpression]] = None,
        load_relationships: Optional[list[InstrumentedAttribute]] = None,
        eager_load_relationships: Optional[list[InstrumentedAttribute]] = None,
        joins: Optional[list[JoinExpression]] = None,
    ):
        stmt = self.__build_query(
            model=model,
            polymorphic=polymorphic,
            filters=filters,
            load_relationships=load_relationships,
            eager_load_relationships=eager_load_relationships,
            joins=joins,
        )
        model_instance = await self.__db.execute(stmt)
        return model_instance.scalars().first()