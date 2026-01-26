from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

Base = declarative_base()

class ProductCategory(enum.Enum):
    ELECTRONICS = "Электроника"
    CLOTHING = "Одежда"
    FOOD = "Продукты"
    BOOKS = "Книги"
    OTHER = "Другое"

class Product(Base):
    """Модель товара"""
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    category = Column(Enum(ProductCategory), nullable=False)
    price = Column(Float, nullable=False)
    quantity = Column(Integer, default=0)
    min_stock = Column(Integer, default=10)
    barcode = Column(String(100), unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    
    sales = relationship("Sale", back_populates="product")
    supplies = relationship("Supply", back_populates="product")

class Customer(Base):
    """Модель клиента"""
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, nullable=True)
    email = Column(String(100), unique=True, nullable=True)
    discount = Column(Float, default=0.0)
    total_purchases = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)
    
    sales = relationship("Sale", back_populates="customer")

class Sale(Base):
    """Модель продажи"""
    __tablename__ = 'sales'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.now)
    
    product = relationship("Product", back_populates="sales")
    customer = relationship("Customer", back_populates="sales")

class Supply(Base):
    """Модель поставки"""
    __tablename__ = 'supplies'
    
    id = Column(Integer, primary_key=True)
    supplier = Column(String(200), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)
    date = Column(DateTime, default=datetime.now)
    
    product = relationship("Product", back_populates="supplies")

class Employee(Base):
    """Модель сотрудника"""
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    position = Column(String(100))
    salary = Column(Float)
    hire_date = Column(DateTime, default=datetime.now)
    phone = Column(String(20))
    email = Column(String(100))

class InventoryCheck(Base):
    """Модель проверки инвентаря"""
    __tablename__ = 'inventory_checks'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    expected_quantity = Column(Integer)
    actual_quantity = Column(Integer)
    difference = Column(Integer)
    checked_by = Column(String(100))
    date = Column(DateTime, default=datetime.now)
    notes = Column(Text)
    
    product = relationship("Product")