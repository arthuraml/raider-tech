class UserSession:
    _instance = None

    def __new__(cls, usuario=None, loja=None, cargo=None):
        if not cls._instance:
            cls._instance = super(UserSession, cls).__new__(cls)
            cls._instance.usuario = usuario
            cls._instance.loja = loja
            cls._instance.cargo = cargo  # Novo atributo para armazenar o cargo
        return cls._instance

    def get_user(self):
        return self.usuario

    def get_loja(self):
        return self.loja

    def get_cargo(self):  # Novo método para obter o cargo
        return self.cargo

    def update_session(self, usuario, loja, cargo):
        self.usuario = usuario
        self.loja = loja
        self.cargo = cargo

