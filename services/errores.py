class ErrorServicio(Exception):
    """Error controlado: se convierte en una respuesta JSON con su código HTTP."""

    def __init__(self, estado, mensaje):
        super().__init__(mensaje)
        self.estado = estado
        self.mensaje = mensaje
