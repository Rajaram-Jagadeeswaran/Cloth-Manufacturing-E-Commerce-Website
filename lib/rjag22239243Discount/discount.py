class OrderCheckoutProcessor:
    def __init__(self):
        self.orders = []

    def create_order(self, price, discount=0):
        # Logic for creating an order
        checkout_price = price
        discounted_price = checkout_price - (checkout_price * discount)
        order = discounted_price
        self.orders.append(order)
        return order

    def calculate_tax(self, checkout_price, tax_rate=0.3):
        # Logic for calculating tax
        return checkout_price * tax_rate

    def calculate_shipping(self, checkout_price, free_shipping=100):
        # Logic for calculating shipping cost
        if checkout_price >= free_shipping:
            return 0
        else:
            return 10  # flat-rate shipping cost
        
    def apply_discount(self, order, discount_amount):
        # Logic for applying additional discounts
        order -= discount_amount
        return order

    def update_item_quantity(self, order, item_index, new_quantity):
        # Logic for updating the quantity of an item in the order
        if 0 <= item_index < len(order['items']):
            order['items'][item_index]['quantity'] = new_quantity
            return order
        else:
            raise ValueError("Invalid item index")
        
    def calculate_net_total(self, order, tax_rate=0.3, free_shipping=100):
        # Logic for calculating NET total
        checkout_price = order
        tax = self.calculate_tax(checkout_price, tax_rate)
        shipping = self.calculate_shipping(checkout_price, free_shipping)
        net_total = checkout_price + tax + shipping
        return net_total