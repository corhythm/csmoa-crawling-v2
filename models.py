import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base

# User*: app_user
# Password*: Password123!
# Host: 127.0.0.1 (localhost)
# Port: 3306
# Default database: company
# engine = sqlalchemy.create_engine("mariadb+mariadbconnector://app_user:Password123!@127.0.0.1:3306/company")
engine = sqlalchemy.create_engine(
    "mariadb+mariadbconnector://dnr2144:1q2w3e4r!@kang-mariadb1.cbqqc9rvr35n.ap-northeast-2.rds.amazonaws.com:3306/csmoa")

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


# class Employee(Base):  # test table
#     __tablename__ = 'employees'
#     id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
#     firstname = sqlalchemy.Column(sqlalchemy.String(length=100))
#     lastname = sqlalchemy.Column(sqlalchemy.String(length=100))
#     active = sqlalchemy.Column(sqlalchemy.Boolean, default=True)
#     created_at = sqlalchemy.Column(sqlalchemy.TIMESTAMP, nullable=False, server_default=sqlalchemy.sql.func.now())


# 메타 데이터에 있는 테이블 생성
Base.metadata.create_all(engine)

# def add_employee(first_name, last_name):
#     newEmployee = Employee(firstname=first_name, lastname=last_name)
#     session.add(newEmployee)  # add하면 flush가 자동으로 됨
#     session.commit()
#
#
# def select_all():
#     employees = session.query(Employee).all()
#     for employee in employees:
#         print(" - " + employee.firstname + ' ' + employee.lastname)
#
#
# def select_by_status(is_active):
#     employees = session.query(Employee).filter_by(active=is_active)
#     for employee in employees:
#         print(" - " + employee.firstname + ' ' + employee.lastname)
#
#
# def update_employee_status(id, is_active):
#     employee = session.query(Employee).get(id)
#     employee.active = is_active
#     session.commit()
#
#
# def delete_employee(id):
#     session.query(Employee).filter(Employee.id == id).delete()
#     session.commit()
#
#
# def temp_test():
#     # Add some new employees
#     add_employee("Bruce", "Wayne")
#     add_employee("Diana", "Prince")
#     add_employee("Clark", "Kent")
#
#     # Show all employees
#     print('All Employees')
#     select_all()
#     print("----------------")
#
#     # Update employee status
#     update_employee_status(2, False)
#
#     # Show active employees
#     print('Active Employees')
#     select_by_status(True)
#     print("----------------")
#
#     # Delete employee
#     delete_employee(1)
#
#     # Show all employees
#     print('All Employees')
#     select_all()
#     print("----------------")
