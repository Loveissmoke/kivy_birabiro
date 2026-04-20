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
from kivy.clock import Clock






# =====================================
# PATH HELPERS (ANDROID SAFE)
# =====================================
def get_base_dir():
    app = App.get_running_app()
    base = app.user_data_dir
    os.makedirs(base, exist_ok=True)
    return base


def get_db_path():
    return os.path.join(get_base_dir(), "products.db")


def get_json_path():
    date_str = datetime.now().strftime("%d_%m_%Y")
    return os.path.join(get_base_dir(), f".bk_{date_str}.json")
# =====================================
# DATABASE
# =====================================
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()


def db():
    return sqlite3.connect(get_db_path())


def init_db():
    conn = db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        case_size INTEGER,
        price REAL
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY,
        password TEXT
    )
    """)

    c.execute("SELECT * FROM admin WHERE id=1")
    if not c.fetchone():
        c.execute(
            "INSERT INTO admin VALUES(1, ?)",
            (hash_password("1234"),)
        )

    conn.commit()
    conn.close()


def check_password(p):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT password FROM admin WHERE id=1")
    row = c.fetchone()
    conn.close()

    if not row:
        return False

    return row[0] == hash_password(p)


def update_password(p):
    conn = db()
    c = conn.cursor()
    c.execute(
        "UPDATE admin SET password=? WHERE id=1",
        (hash_password(p),)
    )
    conn.commit()
    conn.close()


def get_products():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT id,name,case_size,price FROM products")
    data = c.fetchall()
    conn.close()
    return data


def add_product(name, case_size, price):
    conn = db()
    c = conn.cursor()
    c.execute(
        "INSERT INTO products(name,case_size,price) VALUES(?,?,?)",
        (name, case_size, price)
    )
    conn.commit()
    conn.close()


def update_product(pid, name, case_size, price):
    conn = db()
    c = conn.cursor()
    c.execute(
        "UPDATE products SET name=?,case_size=?,price=? WHERE id=?",
        (name, case_size, price, pid)
    )
    conn.commit()
    conn.close()


def delete_product_db(pid):
    conn = db()
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE id=?", (pid,))
    conn.commit()
    conn.close()


# =========================
# HELPERS
# =========================
def safe_int(v):
    try:
        return int(v)
    except:
        return 0


# =========================
# SCREENS
# =========================
class SalesScreen(MDScreen):
    pass


class AdminScreen(MDScreen):
    pass

class HistoryScreen(MDScreen):
    pass
# =========================
# COMPONENTS
# =========================
class ProductCard(MDCard):
    name = StringProperty()
    case_size = NumericProperty()
    price = NumericProperty()

    def __init__(self, update_callback, **kwargs):
        super().__init__(**kwargs)
        self.update_callback = update_callback
        Clock.schedule_once(self.adjust_inputs, 0)

    def adjust_inputs(self, *args):
        if self.case_size <= 12:
            self.ids.dozen.opacity = 0
            self.ids.dozen.disabled = True
            self.ids.dozen.size_hint_x = None
            self.ids.dozen.width = 0

    def on_change(self):
        case = safe_int(self.ids.case.text)
        pieces = safe_int(self.ids.pieces.text)
        dozen = safe_int(self.ids.dozen.text) if self.case_size > 12 else 0

        total = (case * self.case_size) + (dozen * 12) + pieces
        subtotal = total * self.price

        self.ids.subtotal.text = f"Subtotal: {subtotal:.2f} ETB"

        anim = Animation(opacity=0.3, duration=0.1) + Animation(opacity=1, duration=0.1)
        anim.start(self.ids.subtotal)

        self.update_callback()

    def get_total(self):
        case = safe_int(self.ids.case.text)
        pieces = safe_int(self.ids.pieces.text)
        dozen = safe_int(self.ids.dozen.text) if self.case_size > 12 else 0

        return ((case * self.case_size) + (dozen * 12) + pieces) * self.price

    def get_total_pieces(self):
        case = safe_int(self.ids.case.text)
        pieces = safe_int(self.ids.pieces.text)
        dozen = safe_int(self.ids.dozen.text) if self.case_size > 12 else 0

        return (case * self.case_size) + (dozen * 12) + pieces

    def clear(self):
        self.ids.case.text = ""
        if "dozen" in self.ids:
            self.ids.dozen.text = ""
        self.ids.pieces.text = ""
        self.ids.subtotal.text = "Subtotal: 0.00 ETB"


class AdminItem(MDCard):
    name = StringProperty()
    pid = NumericProperty()
    
class CustomerCard(MDCard):
    customer_name = StringProperty()
    total_text = StringProperty()


# =========================
# UI
# =========================
KV = """
ScreenManager:
    SalesScreen:
    AdminScreen:
    HistoryScreen:

<SalesScreen>:
    name: "sales"

    MDNavigationLayout:

        ScreenManager:

            MDScreen:

                MDBoxLayout:
                    orientation: "vertical"

                    MDTopAppBar:
                        title: app.total_text
                        left_action_items: [["menu", lambda x: nav_drawer.set_state("open")]]
                        right_action_items: [["theme-light-dark", lambda x: app.toggle_theme()],["cog", lambda x: app.ask_password()]]
                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(72)
                        padding: dp(10)

                        MDTextField:
                            id: customer_name
                            hint_text: "Customer Name"
                            mode: "rectangle"

                    ScrollView:
                        MDBoxLayout:
                            id: product_list
                            orientation: "vertical"
                            adaptive_height: True
                            padding: dp(10)
                            spacing: dp(10)

                MDFloatingActionButtonSpeedDial:
                   
                    data: app.fab_actions
                    pos_hint: {"right": 0.95, "y": 0.02}

        # 🔥 NAV DRAWER
        MDNavigationDrawer:
            id: nav_drawer

            MDBoxLayout:
                orientation: "vertical"
                padding: dp(10)
                spacing: dp(10)

                MDLabel:
                    text: "Menu"
                    font_style: "H6"
                    size_hint_y: None
                    height: dp(40)

                MDList:

                    OneLineListItem:
                        text: "History"
                        on_release:
                            nav_drawer.set_state("close")
                            app.open_history()

                    OneLineListItem:
                        text: "Report"
                        on_release:
                            nav_drawer.set_state("close")
                            app.open_report()

                    OneLineListItem:
                        text: "By Date"
                        on_release:
                            nav_drawer.set_state("close")
                            app.open_by_date()

                    OneLineListItem:
                        text: "Sync"
                        on_release:
                            nav_drawer.set_state("close")
                            app.sync_data()

                    OneLineListItem:
                        text: "About"
                        on_release:
                            nav_drawer.set_state("close")
                            app.show_about()


<AdminScreen>:
    name: "admin"

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "Admin - Products"
            left_action_items: [["arrow-left", lambda x: app.switch_sales()]]
            right_action_items: [["key", lambda x: app.change_password_dialog()]]

        MDBoxLayout:
            orientation: "vertical"
            padding: dp(10)
            spacing: dp(10)

            MDTextField:
                id: name
                hint_text: "Product Name"

            MDTextField:
                id: case_size
                hint_text: "Case Size"
                input_filter: "int"

            MDTextField:
                id: price
                hint_text: "Price"
                input_filter: "float"

            MDRaisedButton:
                text: "Add Product"
                on_press: app.add_new_product(name.text, case_size.text, price.text)

        ScrollView:
            MDBoxLayout:
                id: admin_list
                orientation: "vertical"
                adaptive_height: True
                spacing: dp(10)
                padding: dp(10)


<ProductCard>:
    orientation: "vertical"
    size_hint_y: None
    height: dp(140)
    padding: dp(10)
    spacing: dp(8)
    elevation: 3

    MDLabel:
        text: root.name

    MDBoxLayout:
        spacing: dp(8)

        MDTextField:
            id: case
            hint_text: "Case"
            input_filter: "int"
            on_text: root.on_change()

        MDTextField:
            id: dozen
            hint_text: "Dozen"
            input_filter: "int"
            on_text: root.on_change()

        MDTextField:
            id: pieces
            hint_text: "Pieces"
            input_filter: "int"
            on_text: root.on_change()

    MDLabel:
        id: subtotal
        text: "Subtotal: 0.00 ETB"


<AdminItem>:
    orientation: "horizontal"
    size_hint_y: None
    height: dp(60)

    MDLabel:
        text: root.name

    MDIconButton:
        icon: "pencil"
        on_press: app.open_edit_dialog(root.pid)

    MDIconButton:
        icon: "delete"
        on_press: app.delete_product(root.pid)
        
        
        
        
        
        
        
        
        
<HistoryScreen>:
    name: "history"

    MDBoxLayout:
        orientation: "vertical"

        MDTopAppBar:
            title: "History"
            left_action_items: [["arrow-left", lambda x: app.switch_sales()]]

        ScrollView:
            MDBoxLayout:
                id: history_list
                orientation: "vertical"
                adaptive_height: True
                padding: dp(12)
                spacing: dp(12)
                
                
                
                
<CustomerCard>:
    orientation: "vertical"
    size_hint_y: None
    height: self.minimum_height
    padding: dp(12)
    spacing: dp(10)
    radius: [16]
    elevation: 4

    MDBoxLayout:
        orientation: "vertical"
        adaptive_height: True
        spacing: dp(8)

        MDLabel:
            text: root.customer_name
            font_style: "H6"
            bold: True
            size_hint_y: None
            height: self.texture_size[1]

        MDBoxLayout:
            id: product_box
            orientation: "vertical"
            adaptive_height: True
            spacing: dp(4)

        MDSeparator:
            size_hint_y: None
            height: dp(1)

        MDLabel:
            text: root.total_text
            halign: "right"
            theme_text_color: "Primary"
            bold: True
            size_hint_y: None
            height: self.texture_size[1]
        
        
        
"""


# =========================
# APP
# =========================
class SalesApp(MDApp):
    total_text = StringProperty("Total ETB: 0.00")

    def build(self):
        self.theme_cls.theme_style = "Dark"

        self.fab_actions = {
            "save": ["Save Sale", "white", "on_release", lambda x: self.save_sale()],
            "clear": ["Clear All", "white", "on_release", lambda x: self.clear_sales()],
        }

        return Builder.load_string(KV)

    def on_start(self):
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
        except:
            pass

        return []

    def _collect_sale_products(self):
        products = []
        for p in self.products:
            total_pieces = p.get_total_pieces()

            if total_pieces == 0:
                continue

            products.append({
                "name": p.name,
                "pieces": total_pieces,
                "price": p.price
            })

        return products

    def ask_password(self):
        from kivymd.uix.textfield import MDTextField
        self.pf = MDTextField(password=True)
        self.dialog = MDDialog(
            title="Enter Password",
            type="custom",
            content_cls=self.pf,
            buttons=[MDFlatButton(text="OK", on_release=lambda x: self.check_pass())]
        )
        self.dialog.open()

    def check_pass(self):
        if check_password(self.pf.text):
            self.dialog.dismiss()
            self.switch_admin()

    def change_password_dialog(self):
        from kivymd.uix.textfield import MDTextField
        self.newp = MDTextField(password=True)
        self.dialog = MDDialog(
            title="Change Password",
            type="custom",
            content_cls=self.newp,
            buttons=[
                MDFlatButton(text="Cancel", on_release=lambda x: self.dialog.dismiss()),
                MDFlatButton(text="Save", on_release=lambda x: self.save_pass())
            ]
        )
        self.dialog.open()

    def save_pass(self):
        update_password(self.newp.text)
        self.dialog.dismiss()

    def load_sales(self):
        self.products = []
        c = self.root.get_screen("sales").ids.product_list
        c.clear_widgets()

        for pid, name, case_size, price in get_products():
            card = ProductCard(name=name, case_size=case_size, price=price,
                               update_callback=self.update_total)
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
        # Get the customer name (this can be empty, as per the original logic)
        customer_name = self.root.get_screen("sales").ids.customer_name.text.strip()

        # Collect the sale products
        sale_products = []
        for p in self.products:
            total_pieces = p.get_total_pieces()

            if total_pieces > 0:
                # Save the product with its case_size
                product_data = {
                    "name": p.name,
                    "pieces": total_pieces,
                    "price": p.price,
                    "case_size": p.case_size  # Save the case_size here
                }
                sale_products.append(product_data)

        # If no products are valid (all quantities are 0), show an error and don't save
        if not sale_products:
            self.show_error("Please add at least one product!")
            return
            
        

        # Proceed to save the sale if there are valid products
        sales = self._read_daily_sales()

        # Add the sale data
        sale_data = {
            "customer_name": customer_name if customer_name else f"customer {len(sales) + 1}",
            "products": sale_products
        }

        # Save the updated sales list
        path = self._daily_json_path()
        sales.append(sale_data)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(sales, f, indent=4, ensure_ascii=False)

        self.clear_sales()  # Clear all inputs after saving
        



    def load_admin(self):
        c = self.root.get_screen("admin").ids.admin_list
        c.clear_widgets()

        for pid, name, case_size, price in get_products():
            item = AdminItem(name=f"{name} | {price} ETB", pid=pid)
            c.add_widget(item)

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

        for p in get_products():
            if p[0] == pid:
                name, case, price = p[1], p[2], p[3]

        self.edit_id = pid

        self.n = MDTextField(text=name)
        self.c = MDTextField(text=str(case))
        self.p = MDTextField(text=str(price))

        box = Builder.load_string("""
BoxLayout:
    orientation: "vertical"
    spacing: "10dp"
    size_hint_y: None
    height: "200dp"
""")

        box.add_widget(self.n)
        box.add_widget(self.c)
        box.add_widget(self.p)

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

        Clock.schedule_once(lambda dt: setattr(self.n, "focus", True), 0.2)

    def save_edit(self):
        update_product(self.edit_id, self.n.text, int(self.c.text), float(self.p.text))
        self.dialog.dismiss()
        self.load_admin()
        self.load_sales()

    def switch_admin(self):
        self.clear_sales()
        self.root.current = "admin"

    def switch_sales(self):
        self.root.current = "sales"
    
    
    def open_history(self):
        self.root.current = "history"
        self.load_history()

    def open_report(self):
        print("Report clicked")

    def open_by_date(self):
        print("By Date clicked")

    def sync_data(self):
        print("Sync clicked")

    def show_about(self):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton

        self.dialog = MDDialog(
            title="About",
            text="Sales App\nVersion 1.0",
            buttons=[
                MDFlatButton(text="OK", on_release=lambda x: self.dialog.dismiss())
            ]
        )
        self.dialog.open()
        
        
        
        
        
    def load_history(self):
        container = self.root.get_screen("history").ids.history_list
        container.clear_widgets()

        sales = self._read_daily_sales()

        for sale in reversed(sales):  # latest first
            customer = sale.get("customer_name", "Unknown")
            products = sale.get("products", [])

            total = 0

            card = CustomerCard(
                customer_name=customer,
                total_text=""
            )

            product_box = card.ids.product_box

            for p in products:
                name = p["name"]
                pieces = p["pieces"]
                price = p["price"]

                #  get case size
                case_size = p["case_size"]

                #  conversion
                case = pieces // case_size
                rem = pieces % case_size
                dozen = rem // 12
                pcs = rem % 12

                subtotal = pieces * price
                total += subtotal

                #  build clean text
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
            
    def show_error(self, message):
        from kivymd.uix.label import MDLabel
        from kivy.clock import Clock

        # Create a custom label
        error_label = MDLabel(
            text=message,
            theme_text_color="Error",
            halign="center",
            size_hint=(None, None),
            size=(self.root.width * 0.8, 50),  # Adjust size as needed
            pos_hint={"center_x": 0.5, "center_y": 0.5}  # Center the label on screen
        )

        # Add the label to the current active screen (not ScreenManager)
        current_screen = self.root.current_screen  # Get the current screen
        current_screen.add_widget(error_label)

        # Remove the label after 1 second
        Clock.schedule_once(lambda dt: current_screen.remove_widget(error_label), 1)  

         
    def toggle_theme(self):
        if self.theme_cls.theme_style == "Dark":
            self.theme_cls.theme_style = "Light"
        else:
            self.theme_cls.theme_style = "Dark"









if __name__ == "__main__":
    SalesApp().run()
