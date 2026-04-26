import sqlite3
import hashlib
import json
import os
from kivy.app import App
from datetime import datetime

from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty
from kivy.animation import Animation
from kivy.clock import Clock

from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.label import MDLabel

from kivy_config.screens import SalesScreen, AdminScreen, HistoryScreen
from kivy_config.widgets import ProductCard, AdminItem, CustomerCard
from kivy_config.helpers import init_db, get_products, add_product, update_product, delete_product_db, check_password, update_password, get_theme_path


class SalesApp(MDApp):
    total_text = StringProperty("Total ETB: 0.00")

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.fab_actions = {
            "save": ["Save Sale", "white", "on_release", lambda x: self.save_sale()],
            "clear": ["Clear All", "white", "on_release", lambda x: self.clear_sales()],
        }

        # Loading the UI from the 'ui.kv' file
        return Builder.load_file('kivy_config/ui.kv')

    def on_start(self):
        self.load_theme()
        init_db()
        self.load_sales()
        self.load_admin()

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
        self.root.current = "admin"

    def open_history(self):
        # Switch to the HistoryScreen
        self.root.current = "history"  # Make sure the screen name matches what you've set in the kv file
        self.load_history()  # Optionally, you can load any data or history-related functionality here

    def load_history(self):
        container = self.root.get_screen("history").ids.history_list
        container.clear_widgets()

        sales = self._read_daily_sales()

        for sale in reversed(sales):  # latest first
            customer = sale.get("customer_name", "Unknown")
            products = sale.get("products", [])

            total = 0

            # Create a new CustomerCard to display this sale
            card = CustomerCard(
                customer_name=customer,
                total_text=""
            )

            # Access product_box inside CustomerCard
            product_box = card.ids.product_box

            # Add products to the product_box inside the CustomerCard
            for p in products:
                name = p["name"]
                pieces = p["pieces"]
                price = p["price"]

                # Get case size
                case_size = p["case_size"]

                # conversion
                case = pieces // case_size
                rem = pieces % case_size
                dozen = rem // 12
                pcs = rem % 12

                subtotal = pieces * price
                total += subtotal

                # Build clean text to display product details
                parts = []
                if case > 0:
                    parts.append(f"{case} CZ")
                if dozen > 0:
                    parts.append(f"{dozen} DZ")
                if pcs > 0:
                    parts.append(f"{pcs} PCS")

                qty_text = ", ".join(parts) if parts else "0"

                text = f"• {name} — {qty_text} = {subtotal:.2f} ETB"

                from kivymd.uix.label import MDLabel
                # Add each product's details as a label to the product_box
                product_box.add_widget(
                    MDLabel(
                        text=text,
                        font_style="Body2",
                        size_hint_y=None,
                        height=20
                    )
                )

            card.total_text = f"Total: {total:.2f} ETB"
            container.add_widget(card)

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

    def load_sales(self):
        self.products = []
        c = self.root.get_screen("sales").ids.product_list
        c.clear_widgets()

        for pid, name, case_size, price in get_products():
            card = ProductCard(name=name, case_size=case_size, price=price, update_callback=self.update_total)
            c.add_widget(card)
            self.products.append(card)

    def update_total(self):
        total = sum(p.get_total() for p in self.products)
        self.total_text = f"Total ETB: {total:.2f}"

    def clear_sales(self):
        for p in self.products:
            p.clear()
        self.total_text = "Total ETB: 0.00"
        self.root.get_screen("sales").ids.customer_name.text = ""

    def save_sale(self):
        customer_name = self.root.get_screen("sales").ids.customer_name.text.strip()
        sale_products = []
        for p in self.products:
            total_pieces = p.get_total_pieces()
            if total_pieces > 0:
                product_data = {
                    "name": p.name,
                    "pieces": total_pieces,
                    "price": p.price,
                    "case_size": p.case_size
                }
                sale_products.append(product_data)

        if not sale_products:
            self.show_error("Please add at least one product!", is_error=True)
            return

        sales = self._read_daily_sales()
        sale_data = {
            "customer_name": customer_name if customer_name else f"customer {len(sales) + 1}",
            "products": sale_products
        }
        path = self._daily_json_path()
        sales.append(sale_data)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(sales, f, indent=4, ensure_ascii=False)

        self.clear_sales()

    def load_admin(self):
        c = self.root.get_screen("admin").ids.admin_list
        c.clear_widgets()

        for pid, name, case_size, price in get_products():
            item = AdminItem(name=f"{name} | {price} ETB", pid=pid, case_size=case_size)
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


    def add_new_product(self, name, case_size, price):
        if name and case_size and price:
            add_product(name, int(case_size), float(price))
            scr = self.root.get_screen("admin")
            scr.ids.name.text = ""
            scr.ids.case_size.text = ""
            scr.ids.price.text = ""
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
                name, case, price = p[1], p[2], p[3]

        self.edit_id = pid

        # Create text fields for editing
        self.n = MDTextField(text=name)
        self.c = MDTextField(text=str(case))
        self.p = MDTextField(text=str(price))

        # Create a box layout to hold the fields
        box = Builder.load_string("""
BoxLayout:
    orientation: "vertical"
    spacing: "10dp"
    size_hint_y: None
    height: "200dp"
""")

        # Add the fields to the box layout
        box.add_widget(self.n)
        box.add_widget(self.c)
        box.add_widget(self.p)

        # Create a dialog to hold the form
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
        # Update the product in the database with new values
        update_product(self.edit_id, self.n.text, int(self.c.text), float(self.p.text))
        self.dialog.dismiss()
        self.load_admin()  # Reload the admin products
        self.load_sales()  # Reload the sales products

    def switch_sales(self):
        # This method is used to switch back to the SalesScreen
        self.root.current = "sales"  # Make sure the screen name matches what you've set in the kv file

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
            title = "Error"
        else:
            color = "Custom"  # Custom color for success
            text_color = "Primary"  # Green for success (Primary color)
            title = "Success"

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
            title=title,  # Set title based on whether it's an error or success
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

    def load_theme(self):
        path = get_theme_path()

        if not os.path.exists(path):
            return  # default stays

        try:
            with open(path, "r") as f:
                data = json.load(f)

            theme = data.get("theme", "Dark")
            self.theme_cls.theme_style = theme
        except:
            pass


if __name__ == "__main__":
    SalesApp().run()
