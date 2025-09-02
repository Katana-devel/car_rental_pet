#TODO Cart_services (total sum, optoins true/false)

class TotalCartSum:

    def __init__(self, car_price: int = 0, duration: int = 0, **options: list[int]):
        self.car_price = car_price
        self.duration = duration
        self.options = options


    async def total_sum(self,):
        return (self.car_price * self.duration) + sum(self.options)



cart_total = TotalCartSum()