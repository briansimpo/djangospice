class RouterRegistry:

    def __init__(self):
        self.routers = []

    def register(self, router):
        self.routers.append(router)

    def get_routers(self):
        return self.routers


router_registry = RouterRegistry()