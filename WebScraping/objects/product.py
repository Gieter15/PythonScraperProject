class Product:
    #constructor
    def __init__(self, id ='', product_id = '', title = '', price_int = -1, price_frac = -1, url = '', sale = 0) -> None:
        self.id = id
        self.title = title
        self.product_id = product_id
        self.price_int = price_int
        self.price_frac = price_frac
        self.url = url
        self.sale = sale

    def get_price(self):
        return self.price_int + self.price_frac/100

    def set_price(self, price):
        price = round(float(price), 2)
        [price_int, price_frac] = str(price).split('.')
        self.price_int = int(price_int)
        self.price_frac = int(price_frac)
    
    def set_title(self, title):
        self.title = title.replace('\"','\'')

    def get_info(self):
        print(f'Product info\nTitle: {self.title}\nPrice: {self.get_price()}\nUrl: {self.url}')


if __name__== "__main__":
    my_product = Product()
    my_product.title = input("title of product: ")
    my_product.price_int = int(input("Price integer: "))
    my_product.price_frac = int(input("Price fractional: "))

    my_product.get_info()
