import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from io import BytesIO
import base64
from sqlalchemy import func, desc
from database.models import Sale, Product, Customer, Supply


class InventoryReports:
    """Система отчетов и инвентаризации"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def generate_sales_report(self, start_date=None, end_date=None):
        """Сгенерировать отчет по продажам"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        session = self.db.Session()
        try:
            # Получаем данные о продажах
            sales = session.query(Sale).filter(
                Sale.date.between(start_date, end_date)
            ).all()
            
            if not sales:
                return "Нет данных о продажах за выбранный период."
            
            # Создаем DataFrame
            data = []
            for sale in sales:
                product = session.query(Product).get(sale.product_id)
                customer = session.query(Customer).get(sale.customer_id) if sale.customer_id else None
                
                data.append({
                    'Дата': sale.date.strftime('%d.%m.%Y %H:%M'),
                    'Товар': product.name if product else 'Неизвестно',
                    'Категория': product.category.value if product else '',
                    'Количество': sale.quantity,
                    'Цена за единицу': sale.price,
                    'Сумма': sale.total,
                    'Клиент': customer.name if customer else 'Гость',
                    'Скидка': f"{customer.discount}%" if customer else '0%'
                })
            
            df = pd.DataFrame(data)
            
            # Генерируем отчет
            report = f"Отчет по продажам с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}\n"
            report += "=" * 80 + "\n\n"
            
            report += f"Всего продаж: {len(sales)}\n"
            report += f"Общая сумма: {df['Сумма'].sum():.2f} ₽\n"
            report += f"Средний чек: {df['Сумма'].mean():.2f} ₽\n\n"
            
            # Продажи по категориям
            category_sales = df.groupby('Категория')['Сумма'].sum()
            report += "Продажи по категориям:\n"
            for category, amount in category_sales.items():
                report += f"  {category}: {amount:.2f} ₽\n"
            
            report += "\nДетализация продаж:\n"
            for idx, row in df.iterrows():
                report += f"{row['Дата']} - {row['Товар']} x{row['Количество']} = {row['Сумма']:.2f} ₽\n"
            
            return report
            
        finally:
            session.close()
    
    def generate_inventory_report(self):
        """Сгенерировать отчет по инвентарю"""
        session = self.db.Session()
        try:
            products = session.query(Product).all()
            
            report = "Отчет по инвентарю\n"
            report += "=" * 80 + "\n\n"
            
            total_value = 0
            low_stock_count = 0
            out_of_stock_count = 0
            
            for product in products:
                status = "✅ В наличии"
                if product.quantity == 0:
                    status = "❌ Нет в наличии"
                    out_of_stock_count += 1
                elif product.quantity < product.min_stock:
                    status = "⚠️ Низкий запас"
                    low_stock_count += 1
                
                product_value = product.price * product.quantity
                total_value += product_value
                
                report += f"{product.name} ({product.category.value})\n"
                report += f"  Количество: {product.quantity} (мин: {product.min_stock})\n"
                report += f"  Цена: {product.price:.2f} ₽ | Стоимость: {product_value:.2f} ₽\n"
                report += f"  Статус: {status}\n"
                report += "-" * 40 + "\n"
            
            report += f"\nИтого:\n"
            report += f"Всего товаров: {len(products)}\n"
            report += f"Общая стоимость инвентаря: {total_value:.2f} ₽\n"
            report += f"Товаров с низким запасом: {low_stock_count}\n"
            report += f"Товаров нет в наличии: {out_of_stock_count}\n"
            
            return report
            
        finally:
            session.close()
    
    def generate_financial_report(self, start_date=None, end_date=None):
        """Сгенерировать финансовый отчет"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        session = self.db.Session()
        try:
            # Продажи за период
            sales = session.query(func.sum(Sale.total)).filter(
                Sale.date.between(start_date, end_date)
            ).scalar() or 0
            
            # Поставки за период
            supplies = session.query(func.sum(Supply.cost)).filter(
                Supply.date.between(start_date, end_date)
            ).scalar() or 0
            
            # Текущий инвентарь
            inventory_value = session.query(
                func.sum(Product.price * Product.quantity)
            ).scalar() or 0
            
            # Лучшие товары
            best_sellers = session.query(
                Product.name,
                func.sum(Sale.quantity).label('total_sold'),
                func.sum(Sale.total).label('revenue')
            ).join(Sale).filter(
                Sale.date.between(start_date, end_date)
            ).group_by(Product.id).order_by(
                desc('revenue')
            ).limit(5).all()
            
            report = f"Финансовый отчет с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}\n"
            report += "=" * 80 + "\n\n"
            
            report += f"Выручка от продаж: {sales:.2f} ₽\n"
            report += f"Затраты на поставки: {supplies:.2f} ₽\n"
            report += f"Валовая прибыль: {sales - supplies:.2f} ₽\n"
            report += f"Стоимость инвентаря: {inventory_value:.2f} ₽\n\n"
            
            report += "Топ-5 товаров по выручке:\n"
            for i, (name, sold, revenue) in enumerate(best_sellers, 1):
                report += f"{i}. {name}: продано {sold} на сумму {revenue:.2f} ₽\n"
            
            # Маржинальность (примерная)
            if supplies > 0:
                margin = ((sales - supplies) / sales) * 100 if sales > 0 else 0
                report += f"\nМаржинальность: {margin:.1f}%\n"
            
            return report
            
        finally:
            session.close()
    
    def generate_stock_chart(self):
        """Сгенерировать график запасов"""
        session = self.db.Session()
        try:
            products = session.query(Product).order_by(Product.quantity).limit(15).all()
            
            if not products:
                return None
            
            # Создаем график
            plt.figure(figsize=(12, 6))
            
            names = [p.name[:20] + '...' if len(p.name) > 20 else p.name for p in products]
            quantities = [p.quantity for p in products]
            min_stocks = [p.min_stock for p in products]
            
            x = range(len(products))
            
            bars = plt.bar(x, quantities, alpha=0.7, label='Текущий запас')
            plt.plot(x, min_stocks, 'r--', label='Минимальный запас', linewidth=2)
            
            # Добавляем значения на столбцы
            for i, (qty, min_q) in enumerate(zip(quantities, min_stocks)):
                color = 'red' if qty < min_q else 'green'
                plt.text(i, qty + max(quantities)*0.01, str(qty), 
                        ha='center', va='bottom', color=color, fontweight='bold')
            
            plt.xlabel('Товары')
            plt.ylabel('Количество')
            plt.title('Запасы товаров')
            plt.xticks(x, names, rotation=45, ha='right')
            plt.legend()
            plt.tight_layout()
            
            # Сохраняем график в base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=100)
            buffer.seek(0)
            plt.close()
            
            return base64.b64encode(buffer.read()).decode('utf-8')
            
        finally:
            session.close()
    
    def export_to_excel(self, filename='store_report.xlsx'):
        """Экспортировать данные в Excel"""
        session = self.db.Session()
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                # Экспорт товаров
                products_data = []
                for product in session.query(Product).all():
                    products_data.append({
                        'ID': product.id,
                        'Название': product.name,
                        'Категория': product.category.value,
                        'Цена': product.price,
                        'Количество': product.quantity,
                        'Мин. запас': product.min_stock,
                        'Статус': 'Низкий запас' if product.quantity < product.min_stock else 'OK',
                        'Стоимость': product.price * product.quantity
                    })
                
                if products_data:
                    pd.DataFrame(products_data).to_excel(writer, sheet_name='Товары', index=False)
                
                # Экспорт продаж (последние 100)
                sales_data = []
                for sale in session.query(Sale).order_by(desc(Sale.date)).limit(100).all():
                    product = session.query(Product).get(sale.product_id)
                    customer = session.query(Customer).get(sale.customer_id) if sale.customer_id else None
                    
                    sales_data.append({
                        'Дата': sale.date,
                        'Товар': product.name if product else '',
                        'Количество': sale.quantity,
                        'Цена': sale.price,
                        'Сумма': sale.total,
                        'Клиент': customer.name if customer else 'Гость',
                        'Скидка': f"{customer.discount}%" if customer else '0%'
                    })
                
                if sales_data:
                    pd.DataFrame(sales_data).to_excel(writer, sheet_name='Продажи', index=False)
                
                # Экспорт клиентов
                customers_data = []
                for customer in session.query(Customer).all():
                    customers_data.append({
                        'ID': customer.id,
                        'Имя': customer.name,
                        'Телефон': customer.phone,
                        'Email': customer.email,
                        'Скидка': customer.discount,
                        'Всего покупок': customer.total_purchases
                    })
                
                if customers_data:
                    pd.DataFrame(customers_data).to_excel(writer, sheet_name='Клиенты', index=False)
                
                # Сводный отчет
                summary_data = {
                    'Показатель': [
                        'Всего товаров',
                        'Общая стоимость инвентаря',
                        'Товаров с низким запасом',
                        'Всего клиентов',
                        'Общая выручка'
                    ],
                    'Значение': [
                        len(products_data),
                        sum(p['Стоимость'] for p in products_data),
                        sum(1 for p in products_data if p['Количество'] < p['Мин. запас']),
                        len(customers_data),
                        sum(s['Сумма'] for s in sales_data)
                    ]
                }
                
                pd.DataFrame(summary_data).to_excel(writer, sheet_name='Сводка', index=False)
            
            return filename
            
        finally:
            session.close()