from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DECIMAL, Text, TIMESTAMP
from datetime import datetime
from database import CognovaEntity


class Product(CognovaEntity):
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(DECIMAL(10, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=True)
    brand: Mapped[str] = mapped_column(String(50), nullable=True)
    created_at: Mapped[str] = mapped_column(TIMESTAMP, default=datetime.now)

    @staticmethod
    async def get_all_products():
        products = await Product.get_all()
        return products
