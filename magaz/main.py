import sys
import os
from PyQt5.QtWidgets import QApplication, QTableWidgetItem, QMessageBox, QTableWidget
from PyQt5.QtCore import Qt
from ui.main_window import ModernMainWindow
from database.db_manager import DatabaseManager
from database.models import ProductCategory
from reports.inventory_reports import InventoryReports

class StoreApp:
    """Главный класс приложения магазина"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Store Management System")
        
        # Инициализация компонентов
        self.db = DatabaseManager()
        self.reports = InventoryReports(self.db)
        
        # Создание главного окна
        self.main_window = ModernMainWindow()
        
        # переменная для отслеживания режима редактирования
        self.editing_product_id = None
        
        # Подключение сигналов
        self.connect_signals()
        
        # Загрузка начальных данных
        self.load_initial_data()
        
    def connect_signals(self):
        """Подключение сигналов к слотам"""
        # Товары
        self.main_window.add_product_btn.clicked.connect(self.add_product)
        self.main_window.edit_product_btn.clicked.connect(self.edit_product)
        self.main_window.delete_product_btn.clicked.connect(self.delete_product)
        self.main_window.refresh_products_btn.clicked.connect(self.refresh_products)
        
        # Двойной клик по таблице для редактирования
        self.main_window.products_table.itemDoubleClicked.connect(self.on_product_double_clicked)
        # Настройка выбора строк вместо ячеек
        self.main_window.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Продажи
        self.main_window.process_sale_btn.clicked.connect(self.process_sale)
        
        # Поставки
        self.main_window.add_supply_btn.clicked.connect(self.add_supply)
        
        # Клиенты
        self.main_window.add_customer_btn.clicked.connect(self.add_customer)
        
        # Отчеты
        self.main_window.sales_report_btn.clicked.connect(self.show_sales_report)
        self.main_window.inventory_report_btn.clicked.connect(self.show_inventory_report)
        self.main_window.financial_report_btn.clicked.connect(self.show_financial_report)
        self.main_window.export_excel_btn.clicked.connect(self.export_to_excel)
        
    def load_initial_data(self):
        """Загрузка начальных данных"""
        # Загрузка товаров
        self.refresh_products()
        
        # Загрузка клиентов
        self.refresh_customers()
        
        # Заполнение списков для продаж и поставок
        self.refresh_sales_combos()
        self.refresh_supplies_combos()
        
        # Загрузка истории продаж и поставок
        self.refresh_sales_history()
        self.refresh_supplies_history()
        
        # Обновление статистики
        self.update_statistics()
        
    def add_product(self):
        """Добавление товара"""
        try:
            name = self.main_window.product_name_input.text().strip()
            category_text = self.main_window.product_category_input.currentText()
            price = self.main_window.product_price_input.value()
            quantity = self.main_window.product_quantity_input.value()
            min_stock = self.main_window.product_min_stock_input.value()
            
            if not name:
                self.main_window.show_message("Ошибка", "Введите название товара")
                return
            
            # Преобразуем строку категории в Enum
            category_map = {
                "Электроника": ProductCategory.ELECTRONICS,
                "Одежда": ProductCategory.CLOTHING,
                "Продукты": ProductCategory.FOOD,
                "Книги": ProductCategory.BOOKS,
                "Другое": ProductCategory.OTHER
            }
            
            category = category_map.get(category_text)
            if category is None:
                self.main_window.show_message("Ошибка", "Неверная категория товара")
                return
            
            # Если редактируем товар
            if self.editing_product_id is not None:
                product = self.db.update_product(
                    product_id=self.editing_product_id,
                    name=name,
                    category=category,
                    price=price,
                    quantity=quantity,
                    min_stock=min_stock
                )
                if product:
                    self.main_window.show_message("Успех", f"Товар '{name}' обновлен!")
                    self.editing_product_id = None
                    self.main_window.add_product_btn.setText("➕ Добавить товар")
            else:
                # Сохраняем в БД
                product = self.db.add_product(
                    name=name,
                    category=category,
                    price=price,
                    quantity=quantity,
                    min_stock=min_stock
                )
                if product:
                    self.main_window.show_message("Успех", f"Товар '{name}' добавлен!")
            
            if product:
                self.refresh_products()
                self.clear_product_form()
            else:
                self.main_window.show_message("Ошибка", "Не удалось сохранить товар")
            
        except Exception as e:
            self.main_window.show_message("Ошибка", f"Ошибка при сохранении товара: {str(e)}")
    
    def refresh_products(self):
        """Обновление списка товаров"""
        products = self.db.get_all_products()
        
        table = self.main_window.products_table
        table.setRowCount(len(products))
        
        for row, product in enumerate(products):
            table.setItem(row, 0, QTableWidgetItem(str(product.id)))
            table.setItem(row, 1, QTableWidgetItem(product.name))
            table.setItem(row, 2, QTableWidgetItem(product.category.value))
            table.setItem(row, 3, QTableWidgetItem(f"{product.price:.2f} ₽"))
            table.setItem(row, 4, QTableWidgetItem(str(product.quantity)))
            table.setItem(row, 5, QTableWidgetItem(str(product.min_stock)))
            
            # Статус
            status = "✅ В наличии"
            if product.quantity == 0:
                status = "❌ Нет в наличии"
            elif product.quantity < product.min_stock:
                status = "⚠️ Низкий запас"
            
            table.setItem(row, 6, QTableWidgetItem(status))
        
        table.resizeColumnsToContents()
        
        # Обновляем списки товаров в продажах и поставках
        self.refresh_sales_combos()
        self.refresh_supplies_combos()
    
    def clear_product_form(self):
        """Очистка формы товара"""
        self.main_window.product_name_input.clear()
        self.main_window.product_category_input.setCurrentIndex(0)
        self.main_window.product_price_input.setValue(0)
        self.main_window.product_quantity_input.setValue(0)
        self.main_window.product_min_stock_input.setValue(10)
        self.editing_product_id = None
        self.main_window.add_product_btn.setText("➕ Добавить товар")
    
    def on_product_double_clicked(self, item):
        """Обработка двойного клика по товару в таблице"""
        row = item.row()
        product_id_item = self.main_window.products_table.item(row, 0)
        if product_id_item:
            product_id = int(product_id_item.text())
            self.load_product_for_edit(product_id)
    
    def load_product_for_edit(self, product_id):
        """Загрузка товара в форму для редактирования"""
        product = self.db.get_product_by_id(product_id)
        if not product:
            self.main_window.show_message("Ошибка", "Товар не найден")
            return
        
        # Заполняем форму данными товара
        self.main_window.product_name_input.setText(product.name)
        
        # Устанавливаем категорию
        category_map = {
            ProductCategory.ELECTRONICS: "Электроника",
            ProductCategory.CLOTHING: "Одежда",
            ProductCategory.FOOD: "Продукты",
            ProductCategory.BOOKS: "Книги",
            ProductCategory.OTHER: "Другое"
        }
        category_text = category_map.get(product.category, "Другое")
        index = self.main_window.product_category_input.findText(category_text)
        if index >= 0:
            self.main_window.product_category_input.setCurrentIndex(index)
        
        self.main_window.product_price_input.setValue(product.price)
        self.main_window.product_quantity_input.setValue(product.quantity)
        self.main_window.product_min_stock_input.setValue(product.min_stock)
        
        # Устанавливаем режим редактирования
        self.editing_product_id = product_id
        self.main_window.add_product_btn.setText("💾 Сохранить изменения")
    
    def get_selected_product_id(self):
        """Получить ID выбранного товара"""
        selected_rows = self.main_window.products_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        
        row = selected_rows[0].row()
        product_id_item = self.main_window.products_table.item(row, 0)
        if product_id_item:
            return int(product_id_item.text())
        return None
    
    def edit_product(self):
        """Редактирование товара"""
        product_id = self.get_selected_product_id()
        if product_id is None:
            self.main_window.show_message("Ошибка", "Выберите товар для редактирования")
            return
        
        self.load_product_for_edit(product_id)
    
    def delete_product(self):
        """Удаление товара"""
        product_id = self.get_selected_product_id()
        if product_id is None:
            self.main_window.show_message("Ошибка", "Выберите товар для удаления")
            return
        
        # Получаем информацию о товаре для подтверждения
        product = self.db.get_product_by_id(product_id)
        if not product:
            self.main_window.show_message("Ошибка", "Товар не найден")
            return
        
        # Получаем количество связанных записей
        related_counts = self.db.get_product_related_counts(product_id)
        
        # Формируем сообщение с информацией о связанных записях
        message = f'Вы уверены, что хотите удалить товар "{product.name}"?'
        if related_counts['sales'] > 0 or related_counts['supplies'] > 0 or related_counts['inventory_checks'] > 0:
            message += '\n\nВместе с товаром будут удалены:'
            if related_counts['sales'] > 0:
                message += f'\n• {related_counts["sales"]} продаж'
            if related_counts['supplies'] > 0:
                message += f'\n• {related_counts["supplies"]} поставок'
            if related_counts['inventory_checks'] > 0:
                message += f'\n• {related_counts["inventory_checks"]} проверок инвентаря'
        
        # Подтверждение удаления
        reply = QMessageBox.question(
            self.main_window,
            'Подтверждение удаления',
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                success = self.db.delete_product(product_id)
                if success:
                    self.main_window.show_message("Успех", f"Товар '{product.name}' удален!")
                    self.refresh_products()
                    self.clear_product_form()
                    self.update_statistics()
                else:
                    self.main_window.show_message("Ошибка", "Не удалось удалить товар")
            except Exception as e:
                self.main_window.show_message("Ошибка", f"Ошибка при удалении товара: {str(e)}")
    
    def refresh_sales_combos(self):
        """Обновление списков товаров и клиентов для продаж"""
        # Заполняем список товаров
        products = self.db.get_all_products()
        combo = self.main_window.sale_product_combo
        combo.clear()
        combo.addItem("Выберите товар")
        combo.setItemData(0, None)
        for product in products:
            index = combo.count()
            combo.addItem(f"{product.name} (ID: {product.id}, в наличии: {product.quantity})")
            combo.setItemData(index, product.id)
        
        # Заполняем список клиентов
        customers = self.db.get_all_customers()
        combo = self.main_window.sale_customer_combo
        combo.clear()
        combo.addItem("Без клиента")
        combo.setItemData(0, None)
        for customer in customers:
            index = combo.count()
            combo.addItem(f"{customer.name} (ID: {customer.id})")
            combo.setItemData(index, customer.id)
    
    def refresh_supplies_combos(self):
        """Обновление списка товаров для поставок"""
        products = self.db.get_all_products()
        combo = self.main_window.supply_product_combo
        combo.clear()
        combo.addItem("Выберите товар")
        combo.setItemData(0, None)
        for product in products:
            index = combo.count()
            combo.addItem(f"{product.name} (ID: {product.id})")
            combo.setItemData(index, product.id)
    
    def refresh_sales_history(self):
        """Обновление истории продаж"""
        from datetime import datetime, timedelta
        # Получаем все продажи за последние 30 дней
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # Показываем за последний год
        
        sales = self.db.get_sales_by_date_range(start_date, end_date)
        
        table = self.main_window.sales_history_table
        table.setRowCount(len(sales))
        
        for row, sale in enumerate(sales):
            product = self.db.get_product_by_id(sale.product_id)
            customer = self.db.get_customer_by_id(sale.customer_id) if sale.customer_id else None
            
            table.setItem(row, 0, QTableWidgetItem(str(sale.id)))
            table.setItem(row, 1, QTableWidgetItem(sale.date.strftime("%d.%m.%Y %H:%M")))
            table.setItem(row, 2, QTableWidgetItem(product.name if product else "Неизвестно"))
            table.setItem(row, 3, QTableWidgetItem(str(sale.quantity)))
            table.setItem(row, 4, QTableWidgetItem(f"{sale.total:.2f} ₽"))
            table.setItem(row, 5, QTableWidgetItem(customer.name if customer else "—"))
        
        table.resizeColumnsToContents()
    
    def refresh_supplies_history(self):
        """Обновление истории поставок"""
        supplies = self.db.get_all_supplies()
        
        table = self.main_window.supplies_table
        table.setRowCount(len(supplies))
        
        for row, supply in enumerate(supplies):
            product = self.db.get_product_by_id(supply.product_id)
            
            table.setItem(row, 0, QTableWidgetItem(str(supply.id)))
            table.setItem(row, 1, QTableWidgetItem(supply.date.strftime("%d.%m.%Y %H:%M")))
            table.setItem(row, 2, QTableWidgetItem(supply.supplier))
            table.setItem(row, 3, QTableWidgetItem(product.name if product else "Неизвестно"))
            table.setItem(row, 4, QTableWidgetItem(str(supply.quantity)))
            table.setItem(row, 5, QTableWidgetItem(f"{supply.cost:.2f} ₽"))
        
        table.resizeColumnsToContents()
    
    def process_sale(self):
        """Обработка продажи"""
        try:
            # Получаем выбранный товар
            product_id = self.main_window.sale_product_combo.currentData()
            if product_id is None:
                self.main_window.show_message("Ошибка", "Выберите товар для продажи")
                return
            
            # Получаем выбранного клиента (может быть None)
            customer_id = self.main_window.sale_customer_combo.currentData()
            
            # Получаем количество
            quantity = self.main_window.sale_quantity_spin.value()
            if quantity <= 0:
                self.main_window.show_message("Ошибка", "Количество должно быть больше 0")
                return
            
            # Проверяем наличие товара
            product = self.db.get_product_by_id(product_id)
            if not product:
                self.main_window.show_message("Ошибка", "Товар не найден")
                return
            
            if product.quantity < quantity:
                self.main_window.show_message("Ошибка", 
                    f"Недостаточно товара на складе. Доступно: {product.quantity}")
                return
            
            # Оформляем продажу
            sale = self.db.record_sale(product_id, quantity, customer_id)
            
            if sale:
                self.main_window.show_message("Успех", f"Продажа оформлена на сумму {sale.total:.2f} ₽")
                self.refresh_products()
                self.refresh_sales_history()
                self.update_statistics()
                # Сбрасываем форму
                self.main_window.sale_quantity_spin.setValue(1)
            else:
                self.main_window.show_message("Ошибка", "Не удалось оформить продажу")
                
        except Exception as e:
            self.main_window.show_message("Ошибка", f"Ошибка при оформлении продажи: {str(e)}")
    
    def add_supply(self):
        """Добавление поставки"""
        try:
            supplier = self.main_window.supplier_input.text().strip()
            if not supplier:
                self.main_window.show_message("Ошибка", "Введите поставщика")
                return
            
            # Получаем выбранный товар
            product_id = self.main_window.supply_product_combo.currentData()
            if product_id is None:
                self.main_window.show_message("Ошибка", "Выберите товар для поставки")
                return
            
            quantity = self.main_window.supply_quantity_spin.value()
            if quantity <= 0:
                self.main_window.show_message("Ошибка", "Количество должно быть больше 0")
                return
            
            cost = self.main_window.supply_cost_input.value()
            if cost < 0:
                self.main_window.show_message("Ошибка", "Стоимость не может быть отрицательной")
                return
            
            supply = self.db.add_supply(supplier, product_id, quantity, cost)
            
            if supply:
                self.main_window.show_message("Успех", f"Поставка добавлена!")
                self.refresh_products()
                self.refresh_supplies_history()
                self.update_statistics()
                # Очищаем форму
                self.main_window.supplier_input.clear()
                self.main_window.supply_quantity_spin.setValue(1)
                self.main_window.supply_cost_input.setValue(0)
            else:
                self.main_window.show_message("Ошибка", "Не удалось добавить поставку")
                
        except Exception as e:
            self.main_window.show_message("Ошибка", f"Ошибка при добавлении поставки: {str(e)}")
    
    def add_customer(self):
        """Добавление клиента"""
        try:
            name = self.main_window.customer_name_input.text().strip()
            phone = self.main_window.customer_phone_input.text().strip()
            email = self.main_window.customer_email_input.text().strip()
            discount = self.main_window.customer_discount_spin.value()
            
            if not name or not phone:
                self.main_window.show_message("Ошибка", "Заполните обязательные поля (Имя и Телефон)")
                return
            
            # Если email пустой, передаем None
            email = email if email else None
            
            customer = self.db.add_customer(name, phone, email, discount)
            
            if customer:
                self.main_window.show_message("Успех", f"Клиент '{name}' добавлен!")
                self.refresh_customers()
                self.clear_customer_form()
                
        except Exception as e:
            self.main_window.show_message("Ошибка", f"Ошибка при добавлении клиента: {str(e)}")
    
    def refresh_customers(self):
        """Обновление списка клиентов"""
        customers = self.db.get_all_customers()
        
        table = self.main_window.customers_table
        table.setRowCount(len(customers))
        
        for row, customer in enumerate(customers):
            table.setItem(row, 0, QTableWidgetItem(str(customer.id)))
            table.setItem(row, 1, QTableWidgetItem(customer.name))
            table.setItem(row, 2, QTableWidgetItem(customer.phone or ""))
            table.setItem(row, 3, QTableWidgetItem(customer.email or "—"))
            table.setItem(row, 4, QTableWidgetItem(f"{customer.discount:.1f}%"))
        
        table.resizeColumnsToContents()
        
        # Обновляем список клиентов в продажах
        self.refresh_sales_combos()
    
    def clear_customer_form(self):
        """Очистка формы клиента"""
        self.main_window.customer_name_input.clear()
        self.main_window.customer_phone_input.clear()
        self.main_window.customer_email_input.clear()
        self.main_window.customer_discount_spin.setValue(0)
    
    def update_statistics(self):
        """Обновление статистики"""
        try:
            # Общие продажи
            total_sales = self.db.get_total_sales_amount()
            self.main_window.total_sales_label.setText(f"Общие продажи: {total_sales:.2f} ₽")

            # Прибыль
            try:
                total_profit = self.db.get_total_profit()
            except Exception:
                # на случай, если метод ещё не добавлен или возникла ошибка — не ломаем весь UI
                total_profit = 0
            self.main_window.total_profit_label.setText(f"Прибыль: {total_profit:.2f} ₽")

            # Товары на складе
            products = self.db.get_all_products()
            total_products = sum(p.quantity for p in products)
            self.main_window.total_products_label.setText(f"Товаров на складе: {total_products}")

            # Товары с низким запасом
            low_stock = len(self.db.get_low_stock_products())
            self.main_window.low_stock_label.setText(f"Товаров с низким запасом: {low_stock}")

        except Exception as e:
            print(f"Ошибка обновления статистики: {e}")
    
    def show_sales_report(self):
        """Показать отчет по продажам"""
        report = self.reports.generate_sales_report()
        self.main_window.report_text.setPlainText(report)
    
    def show_inventory_report(self):
        """Показать отчет по инвентарю"""
        report = self.reports.generate_inventory_report()
        self.main_window.report_text.setPlainText(report)
    
    def show_financial_report(self):
        """Показать финансовый отчет"""
        report = self.reports.generate_financial_report()
        self.main_window.report_text.setPlainText(report)
    
    def export_to_excel(self):
        """Экспорт в Excel"""
        try:
            filename = self.reports.export_to_excel()
            self.main_window.show_message("Успех", f"Данные экспортированы в {filename}")
        except Exception as e:
            self.main_window.show_message("Ошибка", f"Ошибка экспорта: {str(e)}")
    
    def run(self):
        """Запуск приложения"""
        self.main_window.show()
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    # Создаем необходимые директории
    os.makedirs('exports', exist_ok=True)
    
    # Запускаем приложение
    store_app = StoreApp()
    store_app.run()