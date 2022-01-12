import os

import sqlalchemy
from sqlalchemy.orm import declarative_base

import secret

engine = sqlalchemy.create_engine(secret.DB_INFO if os.path.isfile('secret.py') else os.environ['DB_INFO'])
Base = declarative_base()


class EventItems(Base):
    __tablename__ = 'event_items'
    event_item_id = sqlalchemy.Column(sqlalchemy.BigInteger, primary_key=True, autoincrement=True)
    item_name = sqlalchemy.Column(sqlalchemy.String(length=100), nullable=False)
    item_price = sqlalchemy.Column(sqlalchemy.Integer)
    item_actual_price = sqlalchemy.Column(sqlalchemy.Integer)
    depth = sqlalchemy.Column(sqlalchemy.String(length=1))
    bundle_id = sqlalchemy.Column(sqlalchemy.BigInteger)
    image_url = sqlalchemy.Column(sqlalchemy.String(length=255))
    category = sqlalchemy.Column(sqlalchemy.String(length=50))
    cs_brand = sqlalchemy.Column(sqlalchemy.String(length=50), nullable=False)
    event_type = sqlalchemy.Column(sqlalchemy.String(length=50), nullable=False)
    created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP(timezone=True), nullable=False,
                                   default=sqlalchemy.sql.func.current_timestamp())
    updated_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP(timezone=True))
    status = sqlalchemy.Column(sqlalchemy.CHAR(length=1), nullable=False, default=True)

    def __str__(self):
        return f'{{event_item_id: {self.event_item_id}, item_name: {self.item_name}, price: {self.item_price}, ' \
               f'actual_price: {self.item_actual_price}, depth: {self.depth}, ' \
               f'bundle_id: {self.bundle_id}, image_url: {self.image_url}, ' \
               f'category: {self.category}, brand: {self.cs_brand}, ' \
               f'event_type: {self.event_type}, created_at: {self.created_at}, ' \
               f'updated_at: {self.updated_at}, status: {self.status}}}'


# Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

