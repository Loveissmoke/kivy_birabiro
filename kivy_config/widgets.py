from kivy.lang import Builder
from kivy.properties import StringProperty, NumericProperty
from kivymd.uix.card import MDCard
from kivy.clock import Clock
from kivy.animation import Animation
from kivymd.uix.label import MDLabel


# Function to safely convert values to integers
def safe_int(v):
    try:
        return int(v)
    except ValueError:
        return 0


# =====================================
# Product Card (Sales screen)
# =====================================
class ProductCard(MDCard):
    name = StringProperty()
    case_size = NumericProperty()
    retail_price = NumericProperty()
    wholesale_price = NumericProperty()
    subd_price = NumericProperty()
    selected_price = StringProperty()

    def __init__(self, update_callback, **kwargs):
        super().__init__(**kwargs)
        self.update_callback = update_callback
        Clock.schedule_once(self.adjust_inputs, 0)

    def adjust_inputs(self, *args):
# hide pcs
        if self.case_size == 1:
            self.ids.pieces.opacity = 0
            self.ids.pieces.disabled = True
            self.ids.pieces.size_hint_x = None
            self.ids.pieces.width = 0
# hide dozen
            self.ids.dozen.opacity = 0
            self.ids.dozen.disabled = True
            self.ids.dozen.size_hint_x = None
            self.ids.dozen.width = 0
            
        elif self.case_size <= 12:
            self.ids.dozen.opacity = 0
            self.ids.dozen.disabled = True
            self.ids.dozen.size_hint_x = None
            self.ids.dozen.width = 0

    def on_change(self):
        case = safe_int(self.ids.case.text)
        pieces = safe_int(self.ids.pieces.text)
        dozen = safe_int(self.ids.dozen.text) if self.case_size > 12 else 0

        total = (case * self.case_size) + (dozen * 12) + pieces
        
        if self.selected_price == "retail":
            subtotal = total * self.retail_price
        elif self.selected_price == "wholesale":
            subtotal = total * self.wholesale_price
        elif self.selected_price == "subd":
            subtotal = total * self.subd_price
        else:
            subtotal = 0

        self.ids.subtotal.text = f"Subtotal: {subtotal:.2f} ETB"

        # Animation for subtotal
        anim = Animation(opacity=0.3, duration=0.1) + Animation(opacity=1, duration=0.1)
        anim.start(self.ids.subtotal)

        self.update_callback()

    def get_total(self):
        case = safe_int(self.ids.case.text)
        pieces = safe_int(self.ids.pieces.text)
        dozen = safe_int(self.ids.dozen.text) if self.case_size > 12 else 0

        # Calculate total number of items
        total_items = (case * self.case_size) + (dozen * 12) + pieces

        # Now, use the total_items to calculate the subtotal
        if self.selected_price == "retail":
            return total_items * self.retail_price
        elif self.selected_price == "wholesale":
            return total_items * self.wholesale_price
        elif self.selected_price == "subd":
            return total_items * self.subd_price
        else:
            return 0

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
    


# =====================================
# Admin Product Item (Admin screen)
# =====================================
class AdminItem(MDCard):
    name = StringProperty()
    pid = NumericProperty()
    case_size = NumericProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def edit_product(self):
        pass  

    def delete_product(self):
        pass  

# =====================================
# Customer Card (History screen)
# =====================================
class CustomerCard(MDCard):
    customer_name = StringProperty()
    total_text = StringProperty()

    # This will be the product_box container where products will be displayed
    product_box = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self):
        # This is the layout where products will be dynamically added
        self.product_box = Builder.load_string("""
BoxLayout:
    orientation: 'vertical'
    MDLabel:
        text: root.customer_name
        font_style: "H6"
        bold: True
    MDLabel:
        text: root.total_text
    ScrollView:
        BoxLayout:
            orientation: 'vertical'
            padding: 10
            spacing: 10
            id: product_box  # This is the product_box container for dynamically adding content
        """)
        return self.product_box

    def add_product(self, name, qty, subtotal):
        from kivymd.uix.label import MDLabel
        # Create a label with the product's info and add it to product_box
        self.product_box.add_widget(
            MDLabel(
                text=f"• {name} — {qty} = {subtotal:.2f} ETB",
                font_style="Body2",
                size_hint_y=None,
                height=20
            )
        )
