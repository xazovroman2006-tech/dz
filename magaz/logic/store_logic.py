from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class ProductCategory(Enum):
    ELECTRONICS = "Электроника"
    CLOTHING = "Одежда"
    FOOD = "Продукты"
    BOOKS = "Книги"
    OTHER = "Другое"

@dataclass
class Product:
    """Класс товара"""
    id: int
    name: str
    category: ProductCategory
    price: float
    quantity: int
    min_stock: int
    barcode: Optional[str] = None
    description: Optional[str] = None
    
    @property
    def status(self) -> str:
        """Статус товара на основе количества"""
        if self.quantity == 0:
            return "Нет в наличии"
        elif self.quantity < self.min_stock:
            return "Низкий запас"
        else:
            return "В наличии"
            
    @property
    def total_value(self) -> float:
        """Общая стоимость товара на складе"""
        return self.price * self.quantity

@dataclass
class Customer:
    """Класс клиента"""
    id: int
    name: str
    phone: str
    email: str
    discount: float = 0.0
    total_purchases: float = 0.0
    
    def apply_discount(self, amount: float) -> float:
        """Применить скидку клиента"""
        return amount * (1 - self.discount / 100)

@dataclass
class Sale:
    """Класс продажи"""
    id: int
    product_id: int
    customer_id: Optional[int]
    quantity: int
    price: float
    date: datetime
    total: float
    
    @classmethod
    def create_sale(cls, product: Product, customer: Optional[Customer], 
                   quantity: int) -> 'Sale':
        """Создать новую продажу"""
        total = product.price * quantity
        if customer:
            total = customer.apply_discount(total)
        
        return cls(
            id=0,
            product_id=product.id,
            customer_id=customer.id if customer else None,
            quantity=quantity,
            price=product.price,
            date=datetime.now(),
            total=total
        )

@dataclass
class Supply:
    """Класс поставки"""
    id: int
    supplier: str
    product_id: int
    quantity: int
    cost: float
    date: datetime

class StoreLogic:
    """Основная логика магазина"""
    
    def __init__(self):
        self.products: Dict[int, Product] = {}
        self.customers: Dict[int, Customer] = {}
        self.sales: List[Sale] = []
        self.supplies: List[Supply] = []
        self.next_product_id = 1
        self.next_customer_id = 1
        self.next_sale_id = 1
        self.next_supply_id = 1
        
    def add_product(self, name: str, category: ProductCategory, 
                   price: float, quantity: int, min_stock: int) -> Product:
        """Добавить новый товар"""
        product = Product(
            id=self.next_product_id,
            name=name,
            category=category,
            price=price,
            quantity=quantity,
            min_stock=min_stock
        )
        self.products[self.next_product_id] = product
        self.next_product_id += 1
        return product
    
    def update_product(self, product_id: int, **kwargs) -> Optional[Product]:
        """Обновить товар"""
        if product_id not in self.products:
            return None
        
        product = self.products[product_id]
        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)
        
        return product
    
    def delete_product(self, product_id: int) -> bool:
        """Удалить товар"""
        if product_id in self.products:
            del self.products[product_id]
            return True
        return False
    
    def add_customer(self, name: str, phone: str, email: str, discount: float = 0) -> Customer:
        """Добавить нового клиента"""
        customer = Customer(
            id=self.next_customer_id,
            name=name,
            phone=phone,
            email=email,
            discount=discount
        )
        self.customers[self.next_customer_id] = customer
        self.next_customer_id += 1
        return customer
    
    def process_sale(self, product_id: int, quantity: int, 
                    customer_id: Optional[int] = None) -> Optional[Sale]:
        """Обработать продажу"""
        if product_id not in self.products:
            return None
        
        product = self.products[product_id]
        
        if product.quantity < quantity:
            return None
        
        customer = self.customers.get(customer_id) if customer_id else None
        
        # Создаем продажу
        sale = Sale.create_sale(product, customer, quantity)
        sale.id = self.next_sale_id
        self.next_sale_id += 1
        
        # Обновляем количество товара
        product.quantity -= quantity
        
        # Обновляем статистику клиента
        if customer:
            customer.total_purchases += sale.total
        
        self.sales.append(sale)
        return sale
    
    def add_supply(self, supplier: str, product_id: int, 
                  quantity: int, cost: float) -> Optional[Supply]:
        """Добавить поставку"""
        if product_id not in self.products:
            return None
        
        supply = Supply(
            id=self.next_supply_id,
            supplier=supplier,
            product_id=product_id,
            quantity=quantity,
            cost=cost,
            date=datetime.now()
        )
        self.next_supply_id += 1
        
        # Обновляем количество товара
        self.products[product_id].quantity += quantity
        
        self.supplies.append(supply)
        return supply
    
    def get_low_stock_products(self) -> List[Product]:
        """Получить товары с низким запасом"""
        return [p for p in self.products.values() 
                if p.quantity < p.min_stock]
    
    def get_total_inventory_value(self) -> float:
        """Получить общую стоимость инвентаря"""
        return sum(p.total_value for p in self.products.values())
    
    def get_sales_by_period(self, start_date: datetime, 
                           end_date: datetime) -> List[Sale]:
        """Получить продажи за период"""
        return [s for s in self.sales 
                if start_date <= s.date <= end_date]
    
    def get_total_sales(self) -> float:
        """Получить общую сумму продаж"""
        return sum(s.total for s in self.sales)
    
    def get_total_profit(self) -> float:
        """Получить общую прибыль"""
        sales_total = self.get_total_sales()
        supply_costs = sum(s.cost for s in self.supplies)
        return sales_total - supply_costs
    
    def search_products(self, query: str) -> List[Product]:
        """Поиск товаров"""
        query = query.lower()
        results = []
        
        for product in self.products.values():
            if (query in product.name.lower() or 
                query in product.category.value.lower()):
                results.append(product)
        
        return results
    
    def get_best_selling_products(self, limit: int = 10) -> List[Tuple[Product, int]]:
        """Получить самые продаваемые товары"""
        product_sales = {}
        
        for sale in self.sales:
            if sale.product_id in self.products:
                product_sales[sale.product_id] = product_sales.get(sale.product_id, 0) + sale.quantity
        
        sorted_products = sorted(
            [(self.products[pid], qty) for pid, qty in product_sales.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_products[:limit]