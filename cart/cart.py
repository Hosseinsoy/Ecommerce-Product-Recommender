from shop.models import Product, ProductVariant


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product):
        product_id = str(product.id)
        product = ProductVariant.objects.get(id=int(product_id))
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 1}
        else:
            if self.cart[product_id]['quantity'] < product.product.inventory:
                self.cart[product_id]['quantity'] += 1
        self.save()

    def decrease(self, product):
        product_id = str(product.id)

        if product_id not in self.cart:
            return

        if self.cart[product_id]['quantity'] > 1:
            self.cart[product_id]['quantity'] -= 1
        else:
            del self.cart[product_id]

        self.save()

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def clear(self):
        del self.session['cart']
        self.save()

    def total_price(self):
        total_price = 0
        for product_id in self.cart.keys():
            product_obj = ProductVariant.objects.get(id=int(product_id))
            total_price += product_obj.product.off_price * self.cart[product_id]['quantity']
        return total_price

    def post_price(self):
        total_weight = 0
        for product_id in self.cart.keys():
            product_obj = ProductVariant.objects.get(id=int(product_id))
            total_weight += product_obj.product.weight * self.cart[product_id]['quantity']
        if total_weight == 0:
            return 0
        elif 0 < total_weight < 1000:
            return 20000
        elif 1000 <= total_weight <= 20000:
            return 30000
        elif total_weight > 2000:
            return 50000

    def final_price(self):
        return self.total_price() + self.post_price()

    def price_after_discount_code(self, discount_code):
        if discount_code.type == 'روی مبلغ نهایی (درصد)':
            return str(self.final_price() - int(self.final_price() * (discount_code.value / 100)))
        elif discount_code.type == 'روی مبلغ نهایی (مبلغ)':
            return str(self.final_price() - discount_code.value)
        elif discount_code.type == 'روی هزینه ارسال (درصد)':
            return str(self.final_price() - int(self.post_price() * (discount_code.value / 100)))

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def __iter__(self):
        products = ProductVariant.objects.filter(id__in=self.cart.keys())

        dict_cart = {
            k: v.copy()
            for k, v in self.cart.items()
        }

        for product in products:
            dict_cart[str(product.id)]["product"] = product

        for item in dict_cart.values():
            item["total"] = item["product"].product.off_price * item["quantity"]
            yield item
    def save(self):
        self.session.modified = True
