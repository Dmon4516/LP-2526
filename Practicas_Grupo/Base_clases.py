from copy import deepcopy

_OUTPUT_BUFFER = []


def clear_output_buffer():
    _OUTPUT_BUFFER.clear()


def get_output_buffer_text():
    return ''.join(_OUTPUT_BUFFER)

class Objeto:
    def abort(self):
        exit()

    def copy(self):
        return deepcopy(self)

class Entero(Objeto):
    def __init__(self, numero):
        super().__init__()
        self.numero = numero

    def __add__(self, s):
        return Entero(self.numero + s.numero)


class IO(Objeto):
    def out_string(self, s):
        _OUTPUT_BUFFER.append(str(s))
        return self

    def out_int(self, s):
        _OUTPUT_BUFFER.append(str(s))
        return self

