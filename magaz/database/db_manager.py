from sqlalchemy import create_engine, func, desc, and_
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from .models import Base, Product, Customer, Sale, Supply, Employee, InventoryCheck, ProductCategory
import pandas as pd

class DatabaseManager:
    """Менеджер базы данных магазина"""
    
    def __init__(self, db_url="sqlite:///store.db"):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.create_tables()
    
    def create_tables(self):
        """Создать таблицы в базе данных"""
        Base.metadata.create_all(self.engine)
    
    def add_product(self, name, category, price, quantity=0, min_stock=10, 
                   barcode=None, description=None):
        """Добавить товар"""
        session = self.Session()
        try:
            product = Product(
                name=name,
                category=category,
                price=price,
                quantity=quantity,
                min_stock=min_stock,
                barcode=barcode,
                description=description
            )
            session.add(product)
            session.commit()
            return product
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_all_products(self):
        """Получить все товары"""
        session = self.Session()
        try:
            return session.query(Product).all()
        finally:
            session.close()
    
    def get_product_by_id(self, product_id):
        """Получить товар по ID"""
        session = self.Session()
        try:
            return session.query(Product).get(product_id)
        finally:
            session.close()
    
    def update_product_quantity(self, product_id, quantity_change):
        """Обновить количество товара"""
        session = self.Session()
        try:
            product = session.query(Product).get(product_id)
            if product:
                product.quantity += quantity_change
                session.commit()
                return product
            return None
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def update_product(self, product_id, name=None, category=None, price=None, 
                      quantity=None, min_stock=None, barcode=None, description=None):
        """Обновить товар"""
        session = self.Session()
        try:
            product = session.query(Product).get(product_id)
            if not product:
                return None
            
            if name is not None:
                product.name = name
            if category is not None:
                product.category = category
            if price is not None:
                product.price = price
            if quantity is not None:
                product.quantity = quantity
            if min_stock is not None:
                product.min_stock = min_stock
            if barcode is not None:
                product.barcode = barcode
            if description is not None:
                product.description = description
            
            session.commit()
            return product
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_product_related_counts(self, product_id):
        """Получить количество связанных записей для товара"""
        session = self.Session()
        try:
            sales_count = session.query(Sale).filter(Sale.product_id == product_id).count()
            supplies_count = session.query(Supply).filter(Supply.product_id == product_id).count()
            inventory_checks_count = session.query(InventoryCheck).filter(
                InventoryCheck.product_id == product_id
            ).count()
            return {
                'sales': sales_count,
                'supplies': supplies_count,
                'inventory_checks': inventory_checks_count
            }
        finally:
            session.close()
    
    def delete_product(self, product_id):
        """Удалить товар"""
        session = self.Session()
        try:
            product = session.query(Product).get(product_id)
            if not product:
                return False
            
            # Удаляем все связанные записи перед удалением товара
            
            # Удаляем все продажи, связанные с товаром
            sales = session.query(Sale).filter(Sale.product_id == product_id).all()
            for sale in sales:
                session.delete(sale)
            
            # Удаляем все поставки, связанные с товаром
            supplies = session.query(Supply).filter(Supply.product_id == product_id).all()
            for supply in supplies:
                session.delete(supply)
            
            # Удаляем все проверки инвентаря, связанные с товаром
            inventory_checks = session.query(InventoryCheck).filter(
                InventoryCheck.product_id == product_id
            ).all()
            for check in inventory_checks:
                session.delete(check)
            
            # Теперь можно безопасно удалить товар
            session.delete(product)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def add_customer(self, name, phone, email, discount=0.0):
        """Добавить клиента"""
        session = self.Session()
        try:
            # пустые строки в None
            if phone and isinstance(phone, str):
                phone = phone.strip() or None
            if email and isinstance(email, str):
                email = email.strip() or None
            
            customer = Customer(
                name=name,
                phone=phone,
                email=email,
                discount=discount
            )
            session.add(customer)
            session.commit()
            return customer
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_all_customers(self):
        """Получить всех клиентов"""
        session = self.Session()
        try:
            return session.query(Customer).all()
        finally:
            session.close()
    
    def get_customer_by_id(self, customer_id):
        """Получить клиента по ID"""
        session = self.Session()
        try:
            return session.query(Customer).get(customer_id)
        finally:
            session.close()
    
    def record_sale(self, product_id, quantity, customer_id=None):
        """Записать продажу"""
        session = self.Session()
        try:
            product = session.query(Product).get(product_id)
            if not product or product.quantity < quantity:
                return None
            
            # Получаем клиента если указан
            customer = None
            if customer_id:
                customer = session.query(Customer).get(customer_id)
            
            # Рассчитываем итоговую сумму
            total = product.price * quantity
            if customer and customer.discount > 0:
                total = total * (1 - customer.discount / 100)
            
            # Создаем запись о продаже
            sale = Sale(
                product_id=product_id,
                customer_id=customer_id,
                quantity=quantity,
                price=product.price,
                total=total,
                date=datetime.now()
            )
            
            # Обновляем количество товара
            product.quantity -= quantity
            
            # Обновляем статистику клиента
            if customer:
                customer.total_purchases += total
            
            session.add(sale)
            session.commit()
           
            session.refresh(sale)  
            session.expunge(sale)  
            return sale
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_sales_by_date_range(self, start_date, end_date):
        """Получить продажи за период"""
        session = self.Session()
        try:
            sales = session.query(Sale).filter(
                and_(
                    Sale.date >= start_date,
                    Sale.date <= end_date
                )
            ).all()
            # Отсоединяем все объекты от сессии
            for sale in sales:
                session.expunge(sale)
            return sales
        finally:
            session.close()
    
    def add_supply(self, supplier, product_id, quantity, cost):
        """Добавить поставку"""
        session = self.Session()
        try:
            supply = Supply(
                supplier=supplier,
                product_id=product_id,
                quantity=quantity,
                cost=cost,
                date=datetime.now()
            )
            
            # Обновляем количество товара
            product = session.query(Product).get(product_id)
            if product:
                product.quantity += quantity
            
            session.add(supply)
            session.commit()
            # Отсоединяем объект от сессии перед возвратом
            session.refresh(supply)  # Загружаем все атрибуты
            session.expunge(supply)  # Отсоединяем от сессии
            return supply
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_all_supplies(self):
        """Получить все поставки"""
        session = self.Session()
        try:
            supplies = session.query(Supply).order_by(desc(Supply.date)).all()
            # Отсоединяем все объекты от сессии
            for supply in supplies:
                session.expunge(supply)
            return supplies
        finally:
            session.close()
    
    def get_low_stock_products(self):
        """Получить товары с низким запасом"""
        session = self.Session()
        try:
            return session.query(Product).filter(
                Product.quantity < Product.min_stock
            ).all()
        finally:
            session.close()
    
    def get_total_sales_amount(self, start_date=None, end_date=None):
        """Получить общую сумму продаж"""
        session = self.Session()
        try:
            query = session.query(func.sum(Sale.total))
            
            if start_date and end_date:
                query = query.filter(
                    and_(
                        Sale.date >= start_date,
                        Sale.date <= end_date
                    )
                )
            
            return query.scalar() or 0
        finally:
            session.close()

    def get_total_profit(self, start_date=None, end_date=None):
        """Получить общую прибыль: выручка от продаж минус затраты на поставки.
        Если передан период (start_date, end_date) — посчитать за период."""
        session = self.Session()
        try:
            # Сумма продаж
            sales_query = session.query(func.sum(Sale.total))
            # Сумма затрат на поставки
            supplies_query = session.query(func.sum(Supply.cost))

            if start_date and end_date:
                sales_query = sales_query.filter(
                    and_(
                        Sale.date >= start_date,
                        Sale.date <= end_date
                    )
                )
                supplies_query = supplies_query.filter(
                    and_(
                        Supply.date >= start_date,
                        Supply.date <= end_date
                    )
                )

            sales_total = sales_query.scalar() or 0
            supplies_total = supplies_query.scalar() or 0

            return sales_total - supplies_total
        finally:
            session.close()
    
    def get_best_selling_products(self, limit=10):
        """Получить самые продаваемые товары"""
        session = self.Session()
        try:
            return session.query(
                Product,
                func.sum(Sale.quantity).label('total_sold')
            ).join(Sale).group_by(Product.id).order_by(
                desc('total_sold')
            ).limit(limit).all()
        finally:
            session.close()
    
    def get_customer_purchases(self, customer_id):
        """Получить покупки клиента"""
        session = self.Session()
        try:
            return session.query(Sale).filter(
                Sale.customer_id == customer_id
            ).order_by(desc(Sale.date)).all()
        finally:
            session.close()