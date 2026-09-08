import sqlite3
# ~ import hashlib
import json
import os
from kivy.app import App
from datetime import datetime

from kivy.lang import Builder
from kivy.properties import StringProperty
# ~ from kivy.animation import Animation
from kivy.clock import Clock

from kivymd.uix.textfield import MDTextField

from kivymd.app import MDApp
# ~ from kivymd.uix.card import MDCard
# ~ from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
# ~ from kivymd.uix.button import MDFlatButton
from kivymd.uix.label import MDLabel
from kivy.uix.boxlayout import BoxLayout
# ~ from kivymd.uix.menu import MDDropdownMenu
# ~ from kivymd.uix.list import OneLineListItem 
# ~ from kivymd.uix.list import IconLeftWidget
# ~ from kivy.metrics import dp
from kivymd.uix.pickers import MDDatePicker
# ~ from kivymd.uix.chip import MDChip
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivy.uix.scrollview import ScrollView

from pathlib import Path


from androidstorage4kivy import Chooser, SharedStorage
from kivy.clock import Clock
from kivy.app import App


from kivy_config.screens import SalesScreen, AdminScreen, HistoryScreen, ReportScreen, AnalyticsScreen, LoadingScreen
from kivy_config.widgets import ProductCard, AdminItem, CustomerCard
from kivy_config.helpers import init_db, get_products, add_product, update_product, delete_product_db, check_password, update_password, get_theme_path

from kivy.core.window import Window

# ~ from kivy.config import Config
# Config.set('kivy', 'window_icon', 'icon.png')

Window.softinput_mode = "below_target"

class SalesApp(MDApp):
    total_text = StringProperty("Total ETB: 0.00")
    selected_price_type = StringProperty("retail")
    
    selected_from_date = None
    selected_to_date = None

    
    analytics_selected_price_types = ["All"]
    analytics_price_types = ['All', 'retail', 'wholesale', 'subd']
    


    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.material_style = "M2"
        self.fab_actions = {
            "save": ["Save Sale", "white", "on_release", lambda x: self.save_sale()],
            "clear": ["Clear All", "white", "on_release", lambda x: self.clear_sales()],
        }
        
        self.screen_history = []
        root = Builder.load_file('kivy_config/ui.kv')
        
        root.current = "loading"
        
        Window.bind(on_keyboard=self.on_back_button)

        # Loading the UI from the 'ui.kv' file
        return root

    def safe_int(self, value):
        try:
            return int(value)
        except:
            return 0

    def safe_float(self, value):
        try:
            return float(value)
        except:
            return 0.0

    def on_start(self):

        self.root.current = "loading"

        Clock.schedule_once(lambda dt: self.init_app(), 0.5)
        
        

    def init_app(self):

        self.load_theme()

        Clock.schedule_once(self._load_database, 0.1)
        
        if not hasattr(self, 'selected_price_type'):
            self.selected_price_type = "retail" 


    def _load_database(self, dt):

        init_db()

        Clock.schedule_once(self._load_sales_screen, 0.1)


    def _load_sales_screen(self, dt):

        self.load_sales()

        Clock.schedule_once(self._load_admin_screen, 0.1)


    def _load_admin_screen(self, dt):

        self.load_admin()

        Clock.schedule_once(self._finish_loading, 0.1)


    def _finish_loading(self, dt):
        self.switch_screen("sales")
        
    def switch_screen(self, screen_name):
        current = self.root.current
        # Don't save loading in history
        if current != screen_name and current != "loading":
            self.screen_history.append(current)
        self.root.current = screen_name
        
        
    def on_back_button(self, window, key, *arg):
        if key == 27:
            if self.screen_history:
                previous = self.screen_history.pop()
                # Never go back to loading
                if previous == "loading":
                    return self.on_back_button(window, key, *arg)
                if previous == "admin":
                    self.ask_password()
                else:
                    self.root.current = previous
                return True
            # No history -> allow Android to close the app
            return False

        return False
        
        
    def switch_to_previous_screen(self):
        """Navigate to the previous screen in the history stack."""
        if self.screen_history:
            previous_screen = self.screen_history.pop()
            if previous_screen == "admin":
                # Going back to AdminScreen requires password
                self.ask_password()
            else:
                self.root.current = previous_screen
        else:
            self.root.current = "sales"

    def _daily_json_path(self):
        date_str = datetime.now().strftime("%d_%m_%Y")
        filename = f".bk_{date_str}.json"
        base = App.get_running_app().user_data_dir
        return os.path.join(base, filename)

    def _read_daily_sales(self):
        path = self._daily_json_path()
        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
        except Exception as e:
            print(f"Error reading sales data: {e}")

        return []

    def ask_password(self):
        from kivymd.uix.textfield import MDTextField
        self.pf = MDTextField(password=True)  # Create a password field
        self.dialog = MDDialog(
            title="Enter Password",
            type="custom",
            content_cls=self.pf,
            buttons=[
                MDFlatButton(text="OK", on_release=lambda x: self.check_password())
            ]
        )
        self.dialog.open()

    def check_password(self):
        if check_password(self.pf.text):
            self.dialog.dismiss()
            self.switch_admin()
        else:
            self.show_error("Incorrect password!", is_error=True)

    def switch_admin(self):
        self.switch_screen("admin")
        
        
    def get_today_report(self):
        sales = self._read_daily_sales()  # Read data from the file

        # If no data exists, it will return an empty dictionary
        if not sales:
            return {}

        report = {}

        for sale in sales:
            for p in sale.get("products", []):
                name = p["name"]
                pieces = p["pieces"]
                price = p["price"]
                case_size = p["case_size"]

                if name not in report:
                    report[name] = {
                        "pieces": 0,
                        "case_size": case_size,
                        "total_birr": 0
                    }

                report[name]["pieces"] += pieces
                report[name]["total_birr"] += pieces * price

        return report
        
    def format_quantity(self, pieces, case_size):
        case = pieces // case_size
        rem = pieces % case_size
        dozen = rem // 12
        pcs = rem % 12

        parts = []
        if case > 0:
            parts.append(f"{case} CZ")
        if dozen > 0:
            parts.append(f"{dozen} DZ")
        if pcs > 0:
            parts.append(f"{pcs} PCS")

        return ", ".join(parts) if parts else "0"


        
    def load_report(self):

        screen = self.root.get_screen('report')  # Access the ReportScreen
        container = screen.ids.get('report_list')  # Access the report_list widget within the screen
        if container is None:
            print("Error: 'report_list' widget not found.")
            return

        container.clear_widgets()

        # If no data, show a "No data available" message
        if not self.get_today_report():  
            container.add_widget(
                MDLabel(
                    text="No sales data available for today.",
                    size_hint_y=None,
                    height=30
                )
            )
            return

        # Process and display the report data
        report = self.get_today_report()
        total_all = 0

        for name, data in report.items():
            pieces = data["pieces"]
            case_size = data["case_size"]
            total_birr = data["total_birr"]

            qty_text = self.format_quantity(pieces, case_size)

            text = f"{name} : {qty_text} = {total_birr:.2f} ETB"

            container.add_widget(
                MDLabel(
                    text=text,
                    size_hint_y=None,
                    height=30
                )
            )

            total_all += total_birr

        # Show grand total
        container.add_widget(
            MDLabel(
                text=f"[b]TOTAL: {total_all:.2f} ETB[/b]",
                markup=True,
                size_hint_y=None,
                height=40
            )
        )
    
    def open_report(self):
        self.switch_screen("report")  
        self.load_report() 
           
    # def open_report(self):
        # self.switch_screen("report")
        # self.load_report()
        
        
    def open_history(self):
        self.switch_screen("history")

        # default = today
        today = datetime.now().strftime("%d_%m_%Y")
        self.selected_history_date = today

        screen = self.root.get_screen("history")
        screen.ids.history_date_label.text = today.replace("_", "/")

        self.load_history(today)
        
        

    def load_history(self, date_str=None):

        if not date_str:
            date_str = datetime.now().strftime("%d_%m_%Y")

        container = self.root.get_screen("history").ids.history_list
        container.clear_widgets()

        sales = self._read_sales_by_date(date_str)

        if not sales:
            container.add_widget(
                MDLabel(
                    text="No sales found for selected date.",
                    size_hint_y=None,
                    height=30
                )
            )
            return

        for sale_index, sale in enumerate(reversed(sales)):

            customer = sale.get("customer_name", "Unknown")
            price_type = sale.get("price_type", "Not set")
            products = sale.get("products", [])

            total = 0

            card = CustomerCard(
                customer_name=f"{customer} ({price_type.capitalize()})",
                total_text="",
                sale_index=sale_index,
                edit_callback=self.edit_sale,
                delete_callback=self.delete_sale
            )

            product_box = card.ids.product_box

            # ✅ Create ONE text block instead of many labels
            product_lines = []

            for p in products:

                name = p["name"]
                pieces = p["pieces"]
                price = p["price"]
                case_size = p["case_size"]

                case = pieces // case_size
                rem = pieces % case_size
                dozen = rem // 12
                pcs = rem % 12

                subtotal = pieces * price
                total += subtotal

                parts = []

                if case > 0:
                    parts.append(f"{case} CZ")

                if dozen > 0:
                    parts.append(f"{dozen} DZ")

                if pcs > 0:
                    parts.append(f"{pcs} PCS")

                qty_text = ", ".join(parts) if parts else "0"

                product_lines.append(
                    f"• {name} — {qty_text} = {subtotal:.2f} ETB"
                )

            # ✅ Only ONE widget added
            product_box.add_widget(
                MDLabel(
                    text="\n".join(product_lines),
                    adaptive_height=True,
                    theme_text_color="Secondary"
                )
            )

            card.total_text = f"Total: {total:.2f} ETB"

            container.add_widget(card)



    def open_history_date_picker(self):
        date_dialog = MDDatePicker()
        date_dialog.bind(on_save=self.on_history_date_selected)
        date_dialog.open()


    def on_history_date_selected(self, instance, value, date_range):
        selected_date = value.strftime("%d_%m_%Y")

        self.selected_history_date = selected_date

        screen = self.root.get_screen("history")
        screen.ids.history_date_label.text = selected_date.replace("_", "/")

        self.load_history(selected_date)
        
    def _daily_json_path_by_date(self, date_str):
        filename = f".bk_{date_str}.json"
        base = App.get_running_app().user_data_dir
        return os.path.join(base, filename)


    def _read_sales_by_date(self, date_str):
        path = self._daily_json_path_by_date(date_str)

        if not os.path.exists(path):
            return []

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                return data

        except Exception as e:
            print(f"Error reading sales data: {e}")

        return []


    def edit_sale(self, sale_index):
        """Edit a sale from history."""
        date_str = getattr(
            self,
            "selected_history_date",
            datetime.now().strftime("%d_%m_%Y")
        )

        sales = self._read_sales_by_date(date_str)
        
        # Reverse to get correct index (since we reversed when displaying)
        actual_index = len(sales) - 1 - sale_index
        
        if actual_index < 0 or actual_index >= len(sales):
            self.show_error("Invalid sale index!", is_error=True)
            return
        
        sale = sales[actual_index]
        customer_name = sale.get("customer_name", "")
        
        # Create a dialog to edit the customer name (for now)
        # You can expand this to edit individual products if needed
        self.edit_customer_field = MDTextField(text=customer_name, hint_text="Customer Name")
        
        box = BoxLayout(orientation='vertical', spacing="10dp", size_hint_y=None, height="80dp")
        box.add_widget(self.edit_customer_field)
        
        self.edit_sale_index = actual_index
        
        self.dialog = MDDialog(
            title="Edit Sale",
            type="custom",
            content_cls=box,
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="Save", on_release=lambda x: self.save_edited_sale())
            ]
        )
        self.dialog.open()

    def save_edited_sale(self):
        """Save the edited sale."""
        date_str = getattr(
            self,
            "selected_history_date",
            datetime.now().strftime("%d_%m_%Y")
        )

        sales = self._read_sales_by_date(date_str)
        
        new_customer_name = self.edit_customer_field.text.strip()
        
        if not new_customer_name:
            self.show_error("Customer name cannot be empty!", is_error=True)
            return
        
        sales[self.edit_sale_index]["customer_name"] = new_customer_name
        
        date_str = getattr(
            self,
            "selected_history_date",
            datetime.now().strftime("%d_%m_%Y")
        )

        path = self._daily_json_path_by_date(date_str)
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(sales, f, indent=4, ensure_ascii=False)
            
            self.dialog.dismiss()
            self.show_error("Sale updated successfully!", is_error=False)
            self.load_history(date_str)  # Reload history
        except Exception as e:
            self.show_error(f"Error saving sale: {e}", is_error=True)

    def delete_sale(self, sale_index):
        """Delete a sale from history."""
        date_str = getattr(
            self,
            "selected_history_date",
            datetime.now().strftime("%d_%m_%Y")
        )

        sales = self._read_sales_by_date(date_str)
        
        # Reverse to get correct index (since we reversed when displaying)
        actual_index = len(sales) - 1 - sale_index
        
        if actual_index < 0 or actual_index >= len(sales):
            self.show_error("Invalid sale index!", is_error=True)
            return
        
        # Show confirmation dialog
        self.dialog = MDDialog(
            title="Delete Sale",
            text="Are you sure you want to delete this sale?",
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="Delete", on_release=lambda x: self.confirm_delete_sale(actual_index))
            ]
        )
        self.dialog.open()

    def confirm_delete_sale(self, actual_index):
        """Confirm and delete the sale."""
        date_str = getattr(
            self,
            "selected_history_date",
            datetime.now().strftime("%d_%m_%Y")
        )

        sales = self._read_sales_by_date(date_str)
        
        del sales[actual_index]
        
        date_str = getattr(
            self,
            "selected_history_date",
            datetime.now().strftime("%d_%m_%Y")
        )

        path = self._daily_json_path_by_date(date_str)
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(sales, f, indent=4, ensure_ascii=False)
            
            self.dialog.dismiss()
            self.show_error("Sale deleted successfully!", is_error=False)
            self.load_history(date_str) # Reload history
        except Exception as e:
            self.show_error(f"Error deleting sale: {e}", is_error=True)
        
    def load_theme(self):
        path = get_theme_path()

        if not os.path.exists(path):
            return  # default stays

        try:
            with open(path, "r") as f:
                data = json.load(f)

            theme = data.get("theme", "Dark")
            self.theme_cls.theme_style = theme

            # update icon if you're using dynamic icon
            if hasattr(self, "theme_icon"):
                if theme == "Dark":
                    self.theme_icon = "weather-night"
                else:
                    self.theme_icon = "white-balance-sunny"
        except:
            pass

    # def switch_price_type(self):
        # # Toggle between price types: retail, wholesale, subd
        # price_types = ["retail", "wholesale", "subd"]
        
        # if self.selected_price_type not in price_types:
            # self.selected_price_type = "retail" 
        
        # current_index = price_types.index(self.selected_price_type)
        # new_index = (current_index + 1) % len(price_types)
        # self.selected_price_type = price_types[new_index]
        
    def switch_price_type(self):
        """Switch between retail, wholesale, and subd price types."""
        price_types = ["retail", "wholesale", "subd"]
        
        if self.selected_price_type not in price_types:
            self.selected_price_type = "retail"
        
        current_index = price_types.index(self.selected_price_type)
        new_index = (current_index + 1) % len(price_types)
        self.selected_price_type = price_types[new_index]

        # ✅ Update the label
        Clock.schedule_once(self.update_price_type_label, 0)

        # ✅ Update products with new price type
        self.update_price_for_products()

        # ✅ DON'T CLEAR - just update totals!
        # Remove: self.clear_sales()
        
        # ✅ Update total with new prices
        Clock.schedule_once(lambda dt: self.update_total(), 0.1)    
        

    def update_price_type_label(self, dt):
        # Manually update the price type label in the UI
        screen = self.root.get_screen("sales")
        price_label = screen.ids.price_type_label
        price_label.text = f"Price Type: {self.selected_price_type.capitalize()}"


    # def update_price_display(self):
        # # Update the top app bar to show the current price type
        # screen = self.root.get_screen("sales")
        # top_app_bar = screen.ids.top_app_bar
        # top_app_bar.title = f"Price Type: {self.selected_price_type.capitalize()}"  # Set title directly

    def update_price_for_products(self):
        """Update all products with the new selected price type (visible AND hidden)."""
        rv = self.root.get_screen("sales").ids.product_list

        # ✅ Step 1: Update data items for ALL products
        for item in rv.data:
            item["selected_price"] = self.selected_price_type

        # ✅ Step 2: Force RecycleView to rebuild ALL cards
        # This ensures hidden products are updated too
        rv.refresh_from_data()

        # ✅ Step 3: Update the total calculation
        Clock.schedule_once(lambda dt: self.update_total(), 0.1)
        
        
    def load_sales(self):
        self.products = []
        rv = self.root.get_screen("sales").ids.product_list
        rv.data = []  # Clear existing data

        product_list_data = []
  
        for pid, name, case_size, retail_price, wholesale_price, subd_price in get_products():
            product_dict = {
                "name": name,
                "case_size": case_size,
                "retail_price": retail_price,
                "wholesale_price": wholesale_price,
                "subd_price": subd_price,
                "selected_price": self.selected_price_type,
                "case_text": "",
                "dozen_text": "",
                "pieces_text": "",
                "update_callback": self.update_total
            }
            product_list_data.append(product_dict)

        rv.data = product_list_data
            
            
    def update_total(self):
        rv = self.root.get_screen("sales").ids.product_list

        total = 0

        for item in rv.data:

            # case = int(item.get("case_text") or 0)
            # dozen = int(item.get("dozen_text") or 0)
            # pieces = int(item.get("pieces_text") or 0)
            case = self.safe_int(item.get("case_text"))
            dozen = self.safe_int(item.get("dozen_text"))
            pieces = self.safe_int(item.get("pieces_text"))
            
            case_size = item["case_size"]

            total_pieces = (case * case_size) + (dozen * 12) + pieces

            # choose correct price
            if item["selected_price"] == "retail":
                price = item["retail_price"]

            elif item["selected_price"] == "wholesale":
                price = item["wholesale_price"]

            elif item["selected_price"] == "subd":
                price = item["subd_price"]

            else:
                price = 0

            total += total_pieces * price

        self.total_text = f"Total ETB: {total:.2f}"
        
    def clear_sales(self):
        """Clear all inputs from ALL product cards."""
        rv = self.root.get_screen("sales").ids.product_list

        # ✅ Clear the data
        for item in rv.data:
            item["case_text"] = ""
            item["dozen_text"] = ""
            item["pieces_text"] = ""

        # ✅ Update visible widget TextInputs directly (don't rebuild)
        for i in range(len(rv.data)):
            item_card = rv.view_adapter.get_visible_view(i)
            if item_card:
                item_card.ids.case.text = ""
                item_card.ids.dozen.text = ""
                item_card.ids.pieces.text = ""
                item_card.ids.subtotal.text = "Subtotal: 0.00 ETB"

        # ✅ Update total
        self.update_total()

        # Reset total display
        self.total_text = "Total ETB: 0.00"

        # Clear customer name
        self.root.get_screen("sales").ids.customer_name.text = ""
 
    
    def save_sale(self):

        customer_name = self.root.get_screen(
            "sales"
        ).ids.customer_name.text.strip()

        sale_products = []

        rv = self.root.get_screen("sales").ids.product_list

        # READ DIRECTLY FROM rv.data
        for item in rv.data:

            # case = int(item.get("case_text") or 0)
            # dozen = int(item.get("dozen_text") or 0)
            # pieces = int(item.get("pieces_text") or 0)

            case = self.safe_int(item.get("case_text"))
            dozen = self.safe_int(item.get("dozen_text"))
            pieces = self.safe_int(item.get("pieces_text"))

            case_size = item["case_size"]

            total_pieces = (
                (case * case_size)
                + (dozen * 12)
                + pieces
            )

            if total_pieces <= 0:
                continue

            # Correct price
            if self.selected_price_type == "retail":
                price = item["retail_price"]

            elif self.selected_price_type == "wholesale":
                price = item["wholesale_price"]

            elif self.selected_price_type == "subd":
                price = item["subd_price"]

            else:
                price = 0

            product_data = {
                "name": item["name"],
                "pieces": total_pieces,
                "price": price,
                "case_size": case_size
            }

            sale_products.append(product_data)

        # Nothing selected
        if not sale_products:
            self.show_error(
                "Please add at least one product!",
                is_error=True
            )
            return

        # Existing sales
        sales = self._read_daily_sales()

        # Sale object
        sale_data = {
            "customer_name": (
                customer_name
                if customer_name
                else f"customer {len(sales) + 1}"
            ),

            "price_type": self.selected_price_type,
            "products": sale_products
        }

        sales.append(sale_data)

        path = self._daily_json_path()

        try:
            with open(path, "w", encoding="utf-8") as f:

                json.dump(
                    sales,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

        except Exception as e:

            self.show_error(
                f"Save failed: {e}",
                is_error=True
            )

            return

        self.clear_sales()

        self.show_error(
            "Sale saved successfully!",
            is_error=False
        )
        
    def load_admin(self):
        c = self.root.get_screen("admin").ids.admin_list
        c.clear_widgets()

        for pid, name, case_size, retail_price, wholesale_price, subd_price in get_products():
            item = AdminItem(name=f"{name} | {retail_price} ETB, {wholesale_price} ETB, {subd_price} ETB", pid=pid, case_size=case_size)
            c.add_widget(item)

    def change_password_dialog(self):
        """Create a dialog for the admin to change their password."""
        # Create fields for old password, new password, and confirm new password
        from kivymd.uix.textfield import MDTextField
        self.old_password_field = MDTextField(password=True, hint_text="Enter current password")
        self.new_password_field = MDTextField(password=True, hint_text="Enter new password")
        self.confirm_new_password_field = MDTextField(password=True, hint_text="Confirm new password")

        # Create a layout for the dialog content
        from kivy.uix.boxlayout import BoxLayout
        box = BoxLayout(orientation='vertical', spacing="10dp", size_hint_y=None, height="250dp")
        box.add_widget(self.old_password_field)
        box.add_widget(self.new_password_field)
        box.add_widget(self.confirm_new_password_field)

        # Create the dialog with the above box layout
        from kivymd.uix.dialog import MDDialog
        self.dialog = MDDialog(
            title="Change Password",
            type="custom",
            content_cls=box,
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="Save", on_release=lambda x: self.save_new_password())  # Call the save method when Save is clicked
            ]
        )
        self.dialog.open()
        
        
    def save_new_password(self):
        """Save the new password after validating it."""
        old_password = self.old_password_field.text
        new_password = self.new_password_field.text
        confirm_password = self.confirm_new_password_field.text

        # Step 1: Check if the old password is correct (you can compare it with the current password in the database)
        if not check_password(old_password):  # Assume check_password is defined to validate the old password
            self.show_error("Incorrect current password!",is_error=True)
            return

        # Step 2: Check if the new password and confirm password match
        if new_password != confirm_password:
            self.show_error("New passwords do not match!", is_error=True)
            return

        # Step 3: Update the password (you'll need a method to actually save the new password, like `update_password`)
        update_password(new_password)  # Assuming update_password is a function that updates the password in the database

        # Step 4: Close the dialog after saving the password
        self.dialog.dismiss()

        # Optionally, display a success message
        self.show_error("Password updated successfully!", is_error=False)


    def add_new_product(self, name, case_size, retail_price, wholesale_price, subd_price):
        if name and case_size and retail_price and wholesale_price and subd_price:
            #add_product(name, int(case_size), float(retail_price), float(wholesale_price), float(subd_price))
            
            add_product(
                name,
                self.safe_int(case_size),
                self.safe_float(retail_price),
                self.safe_float(wholesale_price),
                self.safe_float(subd_price)
)
            
            scr = self.root.get_screen("admin")
            scr.ids.name.text = ""
            scr.ids.case_size.text = ""
            scr.ids.retail_price.text = ""
            scr.ids.wholesale_price.text = ""
            scr.ids.subd_price.text = ""
            self.load_admin()
            self.load_sales()

    def delete_product(self, pid):
        delete_product_db(pid)
        self.load_admin()
        self.load_sales()

    def open_edit_dialog(self, pid):
        from kivymd.uix.textfield import MDTextField

        # Fetch the product details from the database
        for p in get_products():
            if p[0] == pid:
                name, case_size, retail_price, wholesale_price, subd_price = p[1], p[2], p[3], p[4], p[5]

        self.edit_id = pid


        

        # Create text fields for editing
        self.n = MDTextField(text=name)
        self.c = MDTextField(text=str(case_size))
        self.retail = MDTextField(text=str(retail_price))
        self.wholesale = MDTextField(text=str(wholesale_price))
        self.subd = MDTextField(text=str(subd_price))

        # Define the layout with corrected indentation
        box = Builder.load_string("""
BoxLayout:
    orientation: 'vertical'
    spacing: '10dp'
    size_hint_y: None
    height: '250dp'
""")
        box.add_widget(self.n)
        box.add_widget(self.c)
        box.add_widget(self.retail)
        box.add_widget(self.wholesale)
        box.add_widget(self.subd)

        # Create the dialog with the box layout
        self.dialog = MDDialog(
            title="Edit Product",
            type="custom",
            content_cls=box,
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="Save", on_release=lambda x: self.save_edit())
            ]
        )
        self.dialog.open()

        # Focus on the name field automatically
        Clock.schedule_once(lambda dt: setattr(self.n, "focus", True), 0.2)

    def save_edit(self):
        # Get the updated values from the dialog fields
        name = self.n.text
        
        # case_size = int(self.c.text)
        # retail_price = float(self.retail.text)
        # wholesale_price = float(self.wholesale.text)
        # subd_price = float(self.subd.text)
        
        case_size = self.safe_int(self.c.text)
        retail_price = self.safe_float(self.retail.text)
        wholesale_price = self.safe_float(self.wholesale.text)
        subd_price = self.safe_float(self.subd.text)

        # Update the product in the database with new values
        update_product(self.edit_id, name, case_size, retail_price, wholesale_price, subd_price)
        
        self.dialog.dismiss()  # Close the dialog
        self.load_admin()  # Reload the admin products
        self.load_sales()  # Reload the sales products

    def switch_sales(self):
  
        self.switch_screen("sales")

    # def show_error(self, message):
        # from kivymd.uix.label import MDLabel
        # from kivy.clock import Clock

        # # Create a custom label
        # error_label = MDLabel(
            # text=message,
            # theme_text_color="Error",
            # halign="center",
            # size_hint=(None, None),
            # size=(self.root.width * 0.8, 50),  # Adjust size as needed
            # pos_hint={"center_x": 0.5, "center_y": 0.5}  # Center the label on screen
        # )

        # # Add the label to the current active screen (not ScreenManager)
        # current_screen = self.root.current_screen  # Get the current screen
        # current_screen.add_widget(error_label)

        # # Remove the label after 1 second
        # Clock.schedule_once(lambda dt: current_screen.remove_widget(error_label), 1)



    def show_error(self, message, is_error=True):
        """Display an error or success message as an overlay in the center of the screen."""
        from kivymd.uix.label import MDLabel
        from kivy.clock import Clock
        from kivy.uix.floatlayout import FloatLayout  # For overlay
        from kivy.uix.popup import Popup  # A more reliable approach for overlay

        # Create a new layout that will act as the overlay for the message
        overlay = FloatLayout(size_hint=(1, 1))

        # Set the color and title based on whether it's an error or success
        if is_error:
            color = "Error"  # Red for error
            text_color = "Error"  # Red text for error
            #title = "Error"
        else:
            color = "Custom"  # Custom color for success
            text_color = "Primary"  # Green for success (Primary color)
            #title = "Success"

        # Create the label with either error or success message
        error_label = MDLabel(
            text=message,
            theme_text_color=text_color,
            halign="center",
            size_hint=(None, None),
            size=(self.root.width * 0.8, 50),  # Adjust size as needed
            pos_hint={"center_x": 0.5, "center_y": 0.5}  # Center the label on screen
        )

        # Add the error or success label to the overlay layout
        overlay.add_widget(error_label)

        # Create a Popup to show the overlay message
        error_popup = Popup(
            #title=title,  # Set title based on whether it's an error or success
            title="",
            separator_height=0,
            content=overlay,
            size_hint=(None, None),
            size=(self.root.width * 0.8, 100),  # Adjust size as needed
            auto_dismiss=True  # Automatically dismiss the popup
        )

        # Open the popup to display the message
        error_popup.open()

        # Close the popup after 2 seconds
        Clock.schedule_once(lambda dt: error_popup.dismiss(), 2)
    
    
    def toggle_theme(self):
        if self.theme_cls.theme_style == "Dark":
            self.theme_cls.theme_style = "Light"
        else:
            self.theme_cls.theme_style = "Dark"
        self.save_theme()


    def save_theme(self):
        path = get_theme_path()
        data = {"theme": self.theme_cls.theme_style}
        with open(path, "w") as f:
            json.dump(data, f)
            
    def exit_app(self):
        self.dialog = MDDialog(
            title="Exit",
            text="Are you sure you want to exit?",
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="Exit", on_release=lambda x: self._confirm_exit())
            ]
        )
        self.dialog.open()

    def _confirm_exit(self):
        self.dialog.dismiss()
        App.get_running_app().stop()
        
        
        
    def _get_files_in_range(self, from_date, to_date):
        base = App.get_running_app().user_data_dir
        files = []

        try:
            start = datetime.strptime(from_date, "%d_%m_%Y")
            end = datetime.strptime(to_date, "%d_%m_%Y")
        except:
            return []

        for fname in os.listdir(base):
            if fname.startswith(".bk_") and fname.endswith(".json"):
                try:
                    date_str = fname.replace(".bk_", "").replace(".json", "")
                    file_date = datetime.strptime(date_str, "%d_%m_%Y")

                    if start <= file_date <= end:
                        files.append(os.path.join(base, fname))
                except:
                    continue

        return files
            
            


    def open_date_picker(self, date_type):
        self.date_type = date_type

        date_dialog = MDDatePicker(mode="range")
        date_dialog.bind(on_save=self.on_date_selected)
        date_dialog.open()
        
        
    def on_date_selected(self, instance, value, date_range):
        if date_range:
            # Convert both dates to the desired string format
            self.selected_from_date = date_range[0].strftime("%d_%m_%Y")
            self.selected_to_date = date_range[-1].strftime("%d_%m_%Y")

            # Format the date range text
            date_range_text = f"From: {self.selected_from_date} To: {self.selected_to_date}"

            # Update the UI label to display the selected date range
            screen = self.root.get_screen("analytics") 
            screen.ids.date_range_label.text = date_range_text  
            


    def open_price_type_dialog(self):
        price_types = ["All", "Retail", "Wholesale", "Subd"]

        scroll = ScrollView(
            do_scroll_x=True,
            do_scroll_y=False,
            size_hint_y=None,
            height="60dp"
        )

        self.chip_box = MDBoxLayout(
            orientation="horizontal",
            adaptive_width=True,
            size_hint_y=None,
            height="50dp",
            spacing="8dp",
            padding="10dp"
        )

        scroll.add_widget(self.chip_box)
        self.chip_buttons = {}

        for pt in price_types:
            btn = MDFlatButton(
                text=pt,
                theme_text_color="Custom",      # 🔥 IMPORTANT FIX
                text_color=(0, 0, 0, 1),        # default black
                md_bg_color=(0.96, 0.96, 0.96, 1),
            )

            btn.bind(on_release=lambda x, p=pt: self.toggle_chip(p))

            self.chip_buttons[pt] = btn
            self.chip_box.add_widget(btn)

        self.price_dialog = MDDialog(
            title="Select Price Types",
            type="custom",
            content_cls=scroll,   # 🔥 IMPORTANT
            buttons=[
                MDRaisedButton(
                    text="CANCEL",
                    on_release=lambda x: self.price_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="OK",
                    on_release=self.on_price_dialog_ok
                ),
            ],
        )

        self.price_dialog.open()

        # 🔥 IMPORTANT: update AFTER buttons exist
        self.update_chip_ui()



    def toggle_chip(self, price_type):

        if price_type == "All":
            self.analytics_selected_price_types = ["All"]
        else:
            if "All" in self.analytics_selected_price_types:
                self.analytics_selected_price_types.remove("All")

            if price_type in self.analytics_selected_price_types:
                self.analytics_selected_price_types.remove(price_type)
            else:
                self.analytics_selected_price_types.append(price_type)

        if not self.analytics_selected_price_types:
            self.analytics_selected_price_types = ["All"]

        # 🔥 FORCE UI UPDATE IMMEDIATELY
        self.update_chip_ui()
        self.update_price_type_field()

    def update_chip_ui(self):
        for pt, btn in self.chip_buttons.items():

            if pt in self.analytics_selected_price_types:
                # SELECTED (deep material blue + white text for contrast)
                btn.md_bg_color = (0.10, 0.45, 0.90, 1)
                btn.text_color = (1, 1, 1, 1)

            else:
                # UNSELECTED (light gray + dark text for readability)
                btn.md_bg_color = (0.96, 0.96, 0.96, 1)
                btn.text_color = (0, 0, 0, 1)
                
    def on_price_dialog_ok(self, *args):
        self.update_price_type_field()
        self.price_dialog.dismiss()
        
    def update_price_type_field(self):
        screen = self.root.get_screen("analytics")
        screen.ids.price_type.text = ", ".join(self.analytics_selected_price_types)
    
    def load_analytics(self):
        screen = self.root.get_screen("analytics")
        container = screen.ids.analytics_list
        container.clear_widgets()

        from_date = self.selected_from_date
        to_date = self.selected_to_date

        selected_types = [t.lower() for t in self.analytics_selected_price_types]

        if not from_date or not to_date:
            container.add_widget(MDLabel(text="Please select a valid date range.", size_hint_y=None, height=30))
            return

        files = self._get_files_in_range(from_date, to_date)

        if not files:
            container.add_widget(MDLabel(text="No data found in the specified date range.", size_hint_y=None, height=30))
            return

        product_summary = {}
        total_sum = 0

        for path in files:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    sales = json.load(f)
            except Exception as e:
                print(f"Error reading file {path}: {e}")
                continue

            for sale in sales:

                # ✅ MULTI FILTER FIX
                if "all" not in selected_types:
                    if sale.get("price_type", "").lower() not in selected_types:
                        continue

                for p in sale.get("products", []):
                    name = p["name"]
                    pieces = p["pieces"]
                    price = p["price"]
                    case_size = p["case_size"]

                    if name not in product_summary:
                        product_summary[name] = {
                            "pieces": 0,
                            "total": 0.0,
                            "case_size": case_size
                        }

                    product_summary[name]["pieces"] += pieces
                    product_summary[name]["total"] += pieces * price
                    total_sum += pieces * price

        if not product_summary:
            container.add_widget(MDLabel(text="No products found matching the filters.", size_hint_y=None, height=30))
            return

        sorted_products = sorted(product_summary.items())

        for name, data in sorted_products:
            pieces = data["pieces"]
            total_sales = data["total"]
            case_size = data["case_size"]

            qty_text = self.format_quantity(pieces, case_size)

            text = f"{name} → {qty_text} = {total_sales:.2f} ETB"

            container.add_widget(
                MDLabel(
                    text=text,
                    size_hint_y=None,
                    height=30
                )
            )

        container.add_widget(
            MDLabel(
                text=f"[b]TOTAL SALES: {total_sum:.2f} ETB[/b]",
                markup=True,
                size_hint_y=None,
                height=40
            )
        )
    def show_about(self):
        self.dialog = MDDialog(
            title="About",
            text="Sales App\nVersion 1.0\n brktmbrt@gmail.com ",
            buttons=[
                MDFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())
            ]
        )
        self.dialog.open()
        
    def on_resume(self):
        Clock.schedule_once(self.refresh_sales_view, 0.2)
        return True


    def refresh_sales_view(self, *args):
        try:
            rv = self.root.get_screen("sales").ids.product_list

            # force redraw
            rv.refresh_from_data()

            # update totals/subtotals again
            Clock.schedule_once(lambda dt: self.update_total(), 0.1)

        except Exception as e:
            print("Resume refresh error:", e)
            





    def backup_data(self):
        """Backup app data to /storage/emulated/0/Download/BiraBiroBackups"""
        import shutil

        try:
            source_dir = App.get_running_app().user_data_dir
            
            # ✅ Android path: /storage/emulated/0/Download/BiraBiroBackups
            backup_root = "/storage/emulated/0/Download/BiraBiroBackups"
            os.makedirs(backup_root, exist_ok=True)

            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
            backup_dir = os.path.join(backup_root, f"backup_{timestamp}")
            os.makedirs(backup_dir, exist_ok=True)

            # Backup DB file
            db_path = os.path.join(source_dir, "products.db")
            if os.path.exists(db_path):
                shutil.copy2(db_path, os.path.join(backup_dir, "products.db"))
                print(f"Backed up: products.db")

            # Backup JSON files (.bk_*.json)
            for file in os.listdir(source_dir):
                if file.startswith("bk_") and file.endswith(".json"):
                    shutil.copy2(
                        os.path.join(source_dir, file),
                        os.path.join(backup_dir, file)
                    )
                    print(f"Backed up: {file}")

            self.show_error(f"✅ Backup completed!\nFolder: backup_{timestamp}", False)

        except Exception as e:
            self.show_error(f"❌ Backup failed: {str(e)}", True)
            print(f"Backup error: {e}")


    def restore_backup(self, backup_db):

        import sqlite3
        import os

        try:

            app_dir = App.get_running_app().user_data_dir

            current_db = os.path.join(
                app_dir,
                "products.db"
            )

            init_db()

            backup_conn = sqlite3.connect(backup_db)
            current_conn = sqlite3.connect(current_db)

            backup_cur = backup_conn.cursor()
            current_cur = current_conn.cursor()

            current_cur.execute("DELETE FROM products")

            backup_cur.execute("""
                SELECT
                    name,
                    case_size,
                    retail_price,
                    wholesale_price,
                    subd_price
                FROM products
            """)

            rows = backup_cur.fetchall()

            current_cur.executemany("""
                INSERT INTO products(
                    name,
                    case_size,
                    retail_price,
                    wholesale_price,
                    subd_price
                )
                VALUES(?,?,?,?,?)
            """, rows)

            try:

                current_cur.execute("DELETE FROM admin")

                backup_cur.execute(
                    "SELECT id,password FROM admin"
                )

                current_cur.executemany(
                    "INSERT INTO admin VALUES(?,?)",
                    backup_cur.fetchall()
                )

            except Exception:
                pass

            current_conn.commit()

            backup_conn.close()
            current_conn.close()

            Clock.schedule_once(
                self._reload_after_restore,
                0.5
            )

            self.show_error(
                "Products restored successfully.",
                False
            )

        except Exception as e:

            import traceback
            traceback.print_exc()

            self.show_error(str(e), True)

    def _reload_after_restore(self, dt):

        init_db()

        self.load_sales()

        self.load_admin()

        today = datetime.now().strftime("%d_%m_%Y")

        self.selected_history_date = today

        self.load_history(today)

        self.show_error(
            "Data restored successfully!",
            False
        )



    def open_sync_menu(self):
        """Show backup/restore menu"""
        content = MDBoxLayout(
            orientation="vertical",
            spacing="10dp",
            padding="10dp",
            size_hint_y=None,
            height="240dp",
        )

        self.sync_dialog = MDDialog(
            title="Data Options",
            type="custom",
            content_cls=content,
            size_hint=(0.85, None),
        )

        content.add_widget(
            MDRaisedButton(
                text="BACKUP PRODUCT",
                size_hint_y=None,
                height="50dp",
                on_release=lambda x: [self.backup_data(), self.sync_dialog.dismiss()]
            )
        )


        content.add_widget(
            MDRaisedButton(
                text="BACKUP HISTORY",
                size_hint_y=None,
                height="50dp",
                on_release=lambda x: [self.backup_history(), self.sync_dialog.dismiss()]
            )
        )
        content.add_widget(
            MDRaisedButton(
                text="RESTORE PRODUCTS",
                size_hint_y=None,
                height="50dp",
                on_release=lambda x: [
                    self.pick_product_backup(),
                    self.sync_dialog.dismiss()
                ]
            )
        )
        
        
        content.add_widget(
            MDRaisedButton(
                text="RESTORE HISTORY FROM BACKUPS",
                size_hint_y=None,
                height="50dp",
                on_release=lambda x: [ self.open_restore_history_menu(), self.sync_dialog.dismiss() ]
            )
        )

        content.add_widget(
            MDRaisedButton(
                text="SYNC (Coming Soon)",
                size_hint_y=None,
                height="50dp",
                on_release=lambda x: [
                    self.show_error("☁️ Cloud sync coming soon!", False),
                    self.sync_dialog.dismiss()
                ]
            )
        )

        content.add_widget(
            MDRaisedButton(
                text="CLOSE",
                size_hint_y=None,
                height="50dp",
                on_release=lambda x: self.sync_dialog.dismiss()
            )
        )

        self.sync_dialog.open()


    def sync_data(self):
        """Placeholder for future cloud sync - currently just opens menu"""
        self.open_sync_menu()
        
        
        
        
        
        


    def pick_product_backup(self):
        chooser = Chooser(self.on_product_selected)
        chooser.choose_content("*/*")

    def on_product_selected(self, shared_file_list):
        if not shared_file_list:
            return

        ss = SharedStorage()

        private_file = ss.copy_from_shared(shared_file_list[0])

        self.restore_backup(private_file)

    # def pick_history_backup(self):
        # self.chooser = Chooser(self.on_history_backup_selected)
        # self.chooser.choose_content("application/json")


    # def on_history_backup_selected(self, path):
        # if path:
            # print("Selected:", path)

            # if path.lower().endswith(".json"):
                # print("JSON backup selected")
            # else:
                # print("Please select a JSON backup file")
            
        

    # def restore_history(self, filename):
        # backup_dir = os.path.join(
            # App.get_running_app().user_data_dir,
            # "backups"
        # )

        # path = os.path.join(backup_dir, filename)

        # with open(path, "r", encoding="utf-8") as f:
            # history = json.load(f)

        # self.history = history

        # self.save_history()

        # self.load_history()
        
    def backup_history(self):
        """Copy all history JSON files (.bk_*.json and bk_*.json) from user_data_dir
        into /storage/emulated/0/Download/BiraBiroBackups/backup_<timestamp>/history"""
        import shutil

        try:
            source_dir = App.get_running_app().user_data_dir
            backup_root = "/storage/emulated/0/Download/BiraBiroBackups"
            os.makedirs(backup_root, exist_ok=True)

            timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
            backup_dir = os.path.join(backup_root, f"backup_{timestamp}")
            os.makedirs(backup_dir, exist_ok=True)

            history_dir = os.path.join(backup_dir, "history")
            os.makedirs(history_dir, exist_ok=True)

            copied = 0
            for fname in os.listdir(source_dir):
                # Accept both hidden (.bk_*.json) and non-hidden (bk_*.json) naming
                if (fname.startswith(".bk_") or fname.startswith("bk_")) and fname.endswith(".json"):
                    src = os.path.join(source_dir, fname)
                    dst = os.path.join(history_dir, fname)
                    try:
                        shutil.copy2(src, dst)
                        copied += 1
                    except Exception as e:
                        print(f"Failed to copy {src}: {e}")

            if copied == 0:
                self.show_error("No history files found to backup.", True)
            else:
                self.show_error(f"✅ History backup completed! {copied} files\nFolder: backup_{timestamp}", False)

        except Exception as e:
            self.show_error(f"❌ History backup failed: {str(e)}", True)
            print(f"History backup error: {e}")       




    def open_restore_history_menu(self):
        """Show available backup folders from Download/BiraBiroBackups for the user to pick."""
        backup_root = "/storage/emulated/0/Download/BiraBiroBackups"
        if not os.path.exists(backup_root):
            self.show_error("No backups found in Download/BiraBiroBackups.", True)
            return

        # list dirs sorted newest first
        dirs = sorted(
            [d for d in os.listdir(backup_root) if os.path.isdir(os.path.join(backup_root, d))],
            reverse=True
        )

        if not dirs:
            self.show_error("No backup folders found.", True)
            return

        from kivymd.uix.scrollview import ScrollView
        from kivymd.uix.list import OneLineListItem

        content = MDBoxLayout(orientation="vertical", spacing="4dp", padding="4dp", size_hint_y=None)
        content.height = min(56 * len(dirs) + 20, 400)

        for d in dirs:
            btn = OneLineListItem(text=d, on_release=lambda x, dd=d: self._show_backup_files(os.path.join(backup_root, dd)))
            content.add_widget(btn)

        self.restore_backup_dialog = MDDialog(
            title="Select backup folder",
            type="custom",
            content_cls=content,
            size_hint=(0.9, None)
        )
        self.restore_backup_dialog.open()

    def _show_backup_files(self, backup_dir):
        """List history files present in backup_dir (or backup_dir/history) and allow restore single/all."""
        # close previous dialog if open
        if hasattr(self, "restore_backup_dialog") and getattr(self, "restore_backup_dialog", None):
            try:
                self.restore_backup_dialog.dismiss()
            except:
                pass

        hist_dir = os.path.join(backup_dir, "history")
        base = hist_dir if os.path.exists(hist_dir) else backup_dir

        files = []
        for f in os.listdir(base):
            if f.endswith(".json") and (f.startswith("bk_") or f.startswith(".bk_")):
                files.append(os.path.join(base, f))

        if not files:
            self.show_error("No history files found in selected backup.", True)
            return

        from kivymd.uix.list import OneLineListItem
        content = MDBoxLayout(orientation="vertical", spacing="4dp", padding="4dp", size_hint_y=None)
        content.height = min(56 * len(files) + 80, 500)

        for fp in files:
            fname = os.path.basename(fp)
            item = OneLineListItem(text=fname, on_release=lambda x, p=fp: self._confirm_restore_single(p))
            content.add_widget(item)

        # buttons area (Restore All + Cancel)
        btn_box = MDBoxLayout(size_hint_y=None, height="60dp", spacing="8dp", padding=("8dp", "8dp"))
        btn_box.add_widget(
            MDRaisedButton(text="Restore All", on_release=lambda x, paths=files: [self._restore_history_files(paths), self._close_restore_dialog()])
        )
        btn_box.add_widget(
            MDRaisedButton(text="Cancel", on_release=lambda x: self._close_restore_dialog())
        )

        content.add_widget(btn_box)

        self.restore_files_dialog = MDDialog(
            title=f"Files in {os.path.basename(backup_dir)}",
            type="custom",
            content_cls=content,
            size_hint=(0.95, None)
        )
        self.restore_files_dialog.open()

    def _confirm_restore_single(self, file_path):
        """Ask user to confirm restoring a single file."""
        self.confirm_dialog = MDDialog(
            title="Restore History File",
            text=f"Restore {os.path.basename(file_path)} ?\nThis will overwrite any existing file with the same name.",
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: self.confirm_dialog.dismiss()),
                MDFlatButton(text="Restore", on_release=lambda x, p=file_path: [self.confirm_dialog.dismiss(), self._restore_history_files([p]), self._close_restore_dialog()])
            ]
        )
        self.confirm_dialog.open()

    def _close_restore_dialog(self):
        try:
            if getattr(self, "restore_files_dialog", None):
                self.restore_files_dialog.dismiss()
        except:
            pass
        try:
            if getattr(self, "restore_backup_dialog", None):
                self.restore_backup_dialog.dismiss()
        except:
            pass

    def _restore_history_files(self, file_paths):
        """Copy the selected history JSON files into the user_data_dir."""
        import shutil
        copied = 0
        dest_base = App.get_running_app().user_data_dir

        for src in file_paths:
            try:
                dst = os.path.join(dest_base, os.path.basename(src))
                shutil.copy2(src, dst)
                copied += 1
            except Exception as e:
                print(f"Failed to restore {src}: {e}")

        if copied == 0:
            self.show_error("No files restored.", True)
            return

        # If a single file was restored and it follows the daily naming, load that date
        if len(file_paths) == 1:
            fn = os.path.basename(file_paths[0])
            # Expecting names like .bk_DD_MM_YYYY.json or bk_DD_MM_YYYY.json
            try:
                name = fn.replace(".json", "").lstrip(".")
                if name.startswith("bk_"):
                    date_str = name.replace("bk_", "")
                    # Update selected_history_date and reload
                    self.selected_history_date = date_str
                    screen = self.root.get_screen("history")
                    screen.ids.history_date_label.text = date_str.replace("_", "/")
                    self.load_history(date_str)
            except Exception:
                pass
        else:
            # multiple files restored - refresh current history view (today or selected)
            try:
                date_str = getattr(self, "selected_history_date", None)
                if date_str:
                    self.load_history(date_str)
                else:
                    self.load_history()
            except:
                pass

        self.show_error(f"✅ Restored {copied} file(s).", False)





    # def load_theme(self):
        # path = get_theme_path()

        # if not os.path.exists(path):
            # return  # default stays

        # try:
            # with open(path, "r") as f:
                # data = json.load(f)

            # theme = data.get("theme", "Dark")
            # self.theme_cls.theme_style = theme
        # except:
            # pass


if __name__ == "__main__":
    SalesApp().run()
