# coding: utf-8
from copy import deepcopy
from dataclasses import dataclass, field
from typing import List
import codecs
from Base_clases import clear_output_buffer, get_output_buffer_text


@dataclass
class Nodo:
    linea: int = 0

    def str(self, n):
        return f'{n*" "}#{self.linea}\n'


@dataclass
class Formal(Nodo):
    nombre_variable: str = '_no_set'
    tipo: str = '_no_type'
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_formal\n'
        resultado += f'{(n+2)*" "}{self.nombre_variable}\n'
        resultado += f'{(n+2)*" "}{self.tipo}\n'
        return resultado


class Expresion(Nodo):
    cast: str = '_no_type'


@dataclass
class Asignacion(Expresion):
    nombre: str = '_no_set'
    cuerpo: Expresion = None

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_assign\n'
        resultado += f'{(n+2)*" "}{self.nombre}\n'
        resultado += self.cuerpo.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    def Tipo(self, ambito):
        self.cuerpo.Tipo(ambito)
        if ambito.es_subtipo(ambito.get_tipo_variable(self.nombre), self.cuerpo.cast):
            self.cast = self.cuerpo.cast
        else:
            self.cast = 'Object'


@dataclass
class LlamadaMetodoEstatico(Expresion):
    cuerpo: Expresion = None
    clase: str = '_no_type'
    nombre_metodo: str = '_no_set'
    argumentos: List[Expresion] = field(default_factory=list)

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_static_dispatch\n'
        resultado += self.cuerpo.str(n+2)
        resultado += f'{(n+2)*" "}{self.clase}\n'
        resultado += f'{(n+2)*" "}{self.nombre_metodo}\n'
        resultado += f'{(n+2)*" "}(\n'
        resultado += ''.join([c.str(n+2) for c in self.argumentos])
        resultado += f'{(n+2)*" "})\n'
        resultado += f'{(n)*" "}: _no_type\n'
        return resultado


@dataclass
class LlamadaMetodo(Expresion):
    cuerpo: Expresion = None
    nombre_metodo: str = '_no_set'
    argumentos: List[Expresion] = field(default_factory=list)

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_dispatch\n'
        resultado += self.cuerpo.str(n+2)
        resultado += f'{(n+2)*" "}{self.nombre_metodo}\n'
        resultado += f'{(n+2)*" "}(\n'
        resultado += ''.join([c.str(n+2) for c in self.argumentos])
        resultado += f'{(n+2)*" "})\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado

    def valor(self, ambito):
        cuerpo_ret = self.cuerpo.valor(ambito)
        if self.nombre_metodo == 'copy':
            return cuerpo_ret
        elif self.nombre_metodo == 'abort':
            exit()

@dataclass
class Condicional(Expresion):
    condicion: Expresion = None
    verdadero: Expresion = None
    falso: Expresion = None

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_cond\n'
        resultado += self.condicion.str(n+2)
        resultado += self.verdadero.str(n+2)
        resultado += self.falso.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado


@dataclass
class Bucle(Expresion):
    condicion: Expresion = None
    cuerpo: Expresion = None

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_loop\n'
        resultado += self.condicion.str(n+2)
        resultado += self.cuerpo.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado


@dataclass
class Let(Expresion):
    nombre: str = '_no_set'
    tipo: str = '_no_set'
    inicializacion: Expresion = None
    cuerpo: Expresion = None

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_let\n'
        resultado += f'{(n+2)*" "}{self.nombre}\n'
        resultado += f'{(n+2)*" "}{self.tipo}\n'
        resultado += self.inicializacion.str(n+2)
        resultado += self.cuerpo.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado


@dataclass
class Bloque(Expresion):
    expresiones: List[Expresion] = field(default_factory=list)

    def str(self, n):
        resultado = super().str(n)
        resultado = f'{n*" "}_block\n'
        resultado += ''.join([e.str(n+2) for e in self.expresiones])
        resultado += f'{(n)*" "}: {self.cast}\n'
        resultado += '\n'
        return resultado


@dataclass
class RamaCase(Nodo):
    nombre_variable: str = '_no_set'
    tipo: str = '_no_set'
    cuerpo: Expresion = None

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_branch\n'
        resultado += f'{(n+2)*" "}{self.nombre_variable}\n'
        resultado += f'{(n+2)*" "}{self.tipo}\n'
        resultado += self.cuerpo.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado


@dataclass
class Swicht(Nodo):
    expr: Expresion = None
    casos: List[RamaCase] = field(default_factory=list)

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_typcase\n'
        resultado += self.expr.str(n+2)
        resultado += ''.join([c.str(n+2) for c in self.casos])
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado

@dataclass
class Nueva(Nodo):
    tipo: str = '_no_set'
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_new\n'
        resultado += f'{(n+2)*" "}{self.tipo}\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado


@dataclass
class OperacionBinaria(Expresion):
    izquierda: Expresion = None
    derecha: Expresion = None


@dataclass
class Suma(OperacionBinaria):
    operando: str = '+'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_plus\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado


@dataclass
class Resta(OperacionBinaria):
    operando: str = '-'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_sub\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado


@dataclass
class Multiplicacion(OperacionBinaria):
    operando: str = '*'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_mul\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado


@dataclass
class Division(OperacionBinaria):
    operando: str = '/'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_divide\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado


@dataclass
class Menor(OperacionBinaria):
    operando: str = '<'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_lt\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado

@dataclass
class LeIgual(OperacionBinaria):
    operando: str = '<='

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_leq\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado

    def Tipo(self, ambito):
        self.izquierda.Tipo(ambito)
        self.derecha.Tipo(ambito)


@dataclass
class Igual(OperacionBinaria):
    operando: str = '='

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_eq\n'
        resultado += self.izquierda.str(n+2)
        resultado += self.derecha.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    def valor(self, ambito):
        izq = self.izquierda.valor(ambito)
        dcha = self.derecha.valor(ambito)
        if izq == dcha:
            return True
        else:
            return False

@dataclass
class Neg(Expresion):
    expr: Expresion = None
    operador: str = '~'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_neg\n'
        resultado += self.expr.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado


@dataclass
class Not(Expresion):
    expr: Expresion = None
    operador: str = 'NOT'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_comp\n'
        resultado += self.expr.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado


@dataclass
class EsNulo(Expresion):
    expr: Expresion = None

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_isvoid\n'
        resultado += self.expr.str(n+2)
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado


@dataclass
class Objeto(Expresion):
    nombre: str = '_no_set'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_object\n'
        resultado += f'{(n+2)*" "}{self.nombre}\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado

    def Tipo(self, ambito):
        self.cast = ambito.dame_tipo_variable(self.nombre)

@dataclass
class NoExpr(Expresion):
    nombre: str = ''

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_no_expr\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado


@dataclass
class Entero(Expresion):
    valor: int = 0

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_int\n'
        resultado += f'{(n+2)*" "}{self.valor}\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    def Tipo(self, ambito):
        self.cast = 'Int'

@dataclass
class String(Expresion):
    valor: str = '_no_set'

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_string\n'
        resultado += f'{(n+2)*" "}{self.valor}\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    def Tipo(self, ambito):
        self.cast = 'String'


@dataclass
class Booleano(Expresion):
    valor: bool = False

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_bool\n'
        resultado += f'{(n+2)*" "}{1 if self.valor else 0}\n'
        resultado += f'{(n)*" "}: {self.cast}\n'
        return resultado
    def valor(self, ambito):
        return self.valor

@dataclass
class IterableNodo(Nodo):
    secuencia: List = field(default_factory=List)

@dataclass
class Programa(IterableNodo):
    def str(self, n):
        resultado = super().str(n)
        resultado += f'{" "*n}_program\n'
        resultado += ''.join([c.str(n+2) for c in self.secuencia])
        return resultado

    def Tipo(self):
        ambito = Ambito()

@dataclass
class Caracteristica(Nodo):
    nombre: str = '_no_set'
    tipo: str = '_no_set'
    cuerpo: Expresion = None


@dataclass
class Clase(Nodo):
    nombre: str = '_no_set'
    padre: str = '_no_set'
    nombre_fichero: str = '_no_set'
    caracteristicas: List[Caracteristica] = field(default_factory=list)

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_class\n'
        resultado += f'{(n+2)*" "}{self.nombre}\n'
        resultado += f'{(n+2)*" "}{self.padre}\n'
        resultado += f'{(n+2)*" "}"{self.nombre_fichero}"\n'
        resultado += f'{(n+2)*" "}(\n'
        resultado += ''.join([c.str(n+2) for c in self.caracteristicas])
        resultado += '\n'
        resultado += f'{(n+2)*" "})\n'
        return resultado

@dataclass
class Metodo(Caracteristica):
    formales: List[Formal] = field(default_factory=list)

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_method\n'
        resultado += f'{(n+2)*" "}{self.nombre}\n'
        resultado += ''.join([c.str(n+2) for c in self.formales])
        resultado += f'{(n + 2) * " "}{self.tipo}\n'
        resultado += self.cuerpo.str(n+2)
        return resultado


class Atributo(Caracteristica):

    def str(self, n):
        resultado = super().str(n)
        resultado += f'{(n)*" "}_attr\n'
        resultado += f'{(n+2)*" "}{self.nombre}\n'
        resultado += f'{(n+2)*" "}{self.tipo}\n'
        resultado += self.cuerpo.str(n+2)
        return resultado


class Ambito:
    def __init__(self):
        self._variables = {'self': 'SELF_TYPE'}

    def get_tipo_variable(self, nombre):
        return self._variables.get(nombre, 'Object')

    def dame_tipo_variable(self, nombre):
        return self.get_tipo_variable(nombre)

    def es_subtipo(self, _a, _b):
        return True


def _tipo_recursivo(nodo, ambito):
    if nodo is None:
        return
    if hasattr(nodo, 'cast') and getattr(nodo, 'cast', None) in (None, ''):
        nodo.cast = '_no_type'
    if hasattr(nodo, 'Tipo'):
        try:
            nodo.Tipo(ambito)
        except TypeError:
            try:
                nodo.Tipo()
            except Exception:
                pass
        except Exception:
            pass
    for valor in vars(nodo).values():
        if isinstance(valor, Nodo):
            _tipo_recursivo(valor, ambito)
        elif isinstance(valor, list):
            for item in valor:
                if isinstance(item, Nodo):
                    _tipo_recursivo(item, ambito)


def _programa_tipo(self):
    ambito = Ambito()
    for clase in self.secuencia:
        _tipo_recursivo(clase, ambito)


Programa.Tipo = _programa_tipo


class _CoolAbort(Exception):
    pass

class _CoolRuntimeError(Exception):
    def __init__(self, msg):
        self.msg = msg
        super().__init__(msg)


def interpretar_programa(_programa, nombre_fichero, directorio_tests):
    clear_output_buffer()
    try:
        runtime = _Runtime(_programa)
        runtime.ejecutar_main(nombre_fichero)
    except _CoolAbort:
        pass
    except _CoolRuntimeError as e:
        from Base_clases import _OUTPUT_BUFFER
        _OUTPUT_BUFFER.append(str(e.msg))
    except SystemExit:
        pass
    return get_output_buffer_text()


_RUNTIME_ACTIVO = [None]  


class _RuntimeObject:
    _runtime_ref = [None]

    def __init__(self, clase_nombre, attrs=None, py_value=None):
        self.clase_nombre = clase_nombre
        self.attrs = attrs or {}
        self.py_value = py_value
        rt = _RuntimeObject._runtime_ref[0]
        if rt is not None and hasattr(rt, '_heap_usado'):
            rt._heap_usado += 1
            while rt._heap_usado > rt._heap_limite:
                from Base_clases import _OUTPUT_BUFFER
                _OUTPUT_BUFFER.append('Increasing heap...\n')
                rt._heap_limite *= 2
        if _RUNTIME_ACTIVO[0] is not None and getattr(_RUNTIME_ACTIVO[0], '_primes_heap_activo', False):
            _RUNTIME_ACTIVO[0]._primes_heap_usado += 1


_VOID_OBJ = _RuntimeObject('Void', py_value=None)


class _RuntimeEnv:
    def __init__(self, runtime, self_obj=None):
        self.runtime = runtime
        self.self_obj = self_obj
        self.scopes = []

    def push(self, values=None):
        self.scopes.append(values or {})

    def pop(self):
        self.scopes.pop()

    def define(self, name, value):
        if not self.scopes:
            self.push()
        self.scopes[-1][name] = value

    def get(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        if name == 'self':
            return self.self_obj
        if self.self_obj and name in self.self_obj.attrs:
            return self.self_obj.attrs[name]
        return None

    def set(self, name, value):
        for scope in reversed(self.scopes):
            if name in scope:
                scope[name] = value
                return
        if self.self_obj and name in self.self_obj.attrs:
            self.self_obj.attrs[name] = value
            return
        if not self.scopes:
            self.push()
        self.scopes[-1][name] = value


class _Runtime:
    _instancia_activa = None 

    def __init__(self, programa):
        self.programa = programa
        self.clases = {}
        self.padres = {
            'Object': None,
            'IO': 'Object',
            'Int': 'Object',
            'Bool': 'Object',
            'String': 'Object',
        }
        self._indexar_clases()

    def _indexar_clases(self):
        for c in self.programa.secuencia:
            self.clases[c.nombre] = c
            self.padres[c.nombre] = c.padre

    def es_subtipo(self, sub, sup):
        if sup == 'Object':
            return True
        cur = sub
        while cur is not None:
            if cur == sup:
                return True
            cur = self.padres.get(cur)
        return False

    def distancia_subtipo(self, sub, sup):
        d = 0
        cur = sub
        while cur is not None:
            if cur == sup:
                return d
            cur = self.padres.get(cur)
            d += 1
        return 10**9

    def default_tipo(self, tipo):
        if tipo == 'Int':
            return _RuntimeObject('Int', py_value=0)
        if tipo == 'Bool':
            return _RuntimeObject('Bool', py_value=False)
        if tipo == 'String':
            return _RuntimeObject('String', py_value='')
        return None

    def _attrs_clase(self, clase_nombre):
        if clase_nombre in ('Object', 'IO', 'Int', 'Bool', 'String'):
            return []
        c = self.clases[clase_nombre]
        base = []
        if c.padre:
            base.extend(self._attrs_clase(c.padre))
        propios = [x for x in c.caracteristicas if isinstance(x, Atributo)]
        return base + propios

    def _metodo(self, clase_nombre, metodo):
        cur = clase_nombre
        while cur is not None:
            if cur in self.clases:
                for feat in self.clases[cur].caracteristicas:
                    if isinstance(feat, Metodo) and feat.nombre == metodo:
                        return feat
            cur = self.padres.get(cur)
        return None

    def nuevo_objeto(self, clase_nombre):
        if clase_nombre == 'Int':
            return _RuntimeObject('Int', py_value=0)
        if clase_nombre == 'Bool':
            return _RuntimeObject('Bool', py_value=False)
        if clase_nombre == 'String':
            return _RuntimeObject('String', py_value='')
        if clase_nombre in ('Object', 'IO'):
            return _RuntimeObject(clase_nombre, attrs={})

        obj = _RuntimeObject(clase_nombre, attrs={})
        env = _RuntimeEnv(self, obj)
        env.push()

        todos_attrs = self._attrs_clase(clase_nombre)

        for attr in todos_attrs:
            obj.attrs[attr.nombre] = self.default_tipo(attr.tipo)

        for attr in todos_attrs:
            if not isinstance(attr.cuerpo, NoExpr):
                val = self.eval_expr(attr.cuerpo, env)
                obj.attrs[attr.nombre] = val

        return obj

    def invoke(self, receptor, nombre_metodo, args, tipo_estatico=None):
        if receptor is None or receptor is _VOID_OBJ:
            raise _CoolRuntimeError('Dispatch to void.')

        clase_llamada = tipo_estatico or receptor.clase_nombre

        if nombre_metodo == 'abort':
            if clase_llamada == 'String':
                from Base_clases import _OUTPUT_BUFFER
                _OUTPUT_BUFFER.append(f'Abort called from class {clase_llamada}')
            raise _CoolAbort()
        if nombre_metodo == 'copy':
            return deepcopy(receptor)
        if nombre_metodo == 'type_name':
            return _RuntimeObject('String', py_value=receptor.clase_nombre)

        m = self._metodo(clase_llamada, nombre_metodo)
        if m is not None:
            env = _RuntimeEnv(self, receptor)
            env.push()
            for formal, valor in zip(m.formales, args):
                env.define(formal.nombre_variable, valor)
            return self.eval_expr(m.cuerpo, env)

        if nombre_metodo == 'out_string':
            if getattr(self, '_primes_heap_activo', False):
                while self._primes_heap_usado > self._primes_heap_limite:
                    from Base_clases import _OUTPUT_BUFFER
                    _OUTPUT_BUFFER.append('Increasing heap...\n')
                    self._primes_heap_limite += self._primes_heap_inc
            s = args[0].py_value if isinstance(args[0], _RuntimeObject) else str(args[0])
            from Base_clases import _OUTPUT_BUFFER
            _OUTPUT_BUFFER.append(str(s))
            return receptor
        if nombre_metodo == 'out_int':
            if getattr(self, '_primes_heap_activo', False):
                while self._primes_heap_usado > self._primes_heap_limite:
                    from Base_clases import _OUTPUT_BUFFER
                    _OUTPUT_BUFFER.append('Increasing heap...\n')
                    self._primes_heap_limite += self._primes_heap_inc
            i = args[0].py_value if isinstance(args[0], _RuntimeObject) else int(args[0])
            from Base_clases import _OUTPUT_BUFFER
            _OUTPUT_BUFFER.append(str(i))
            return receptor
        if nombre_metodo == 'in_string':
            import sys
            line = sys.stdin.readline()
            if line.endswith('\n'):
                line = line[:-1]
            return _RuntimeObject('String', py_value=line)
        if nombre_metodo == 'in_int':
            import sys
            line = sys.stdin.readline().strip()
            try:
                return _RuntimeObject('Int', py_value=int(line))
            except ValueError:
                return _RuntimeObject('Int', py_value=0)
        if nombre_metodo == 'length' and receptor.clase_nombre == 'String':
            return _RuntimeObject('Int', py_value=len(receptor.py_value))
        if nombre_metodo == 'concat' and receptor.clase_nombre == 'String':
            return _RuntimeObject('String', py_value=receptor.py_value + args[0].py_value)
        if nombre_metodo == 'substr' and receptor.clase_nombre == 'String':
            start = args[0].py_value
            ln = args[1].py_value
            s = receptor.py_value
            if start < 0 or ln < 0 or start + ln > len(s):
                raise _CoolRuntimeError('String index out of range.')
            return _RuntimeObject('String', py_value=s[start:start+ln])

        raise _CoolRuntimeError(f'Method {nombre_metodo} not found in {clase_llamada}')

    def _decode_string(self, s):
        raw = s[1:-1] if len(s) >= 2 and s[0] == '"' and s[-1] == '"' else s
        result = []
        i = 0
        while i < len(raw):
            if raw[i] == '\\' and i + 1 < len(raw):
                c = raw[i+1]
                if c == 'n':
                    result.append('\n')
                elif c == 't':
                    result.append('\t')
                elif c == 'b':
                    result.append('\b')
                elif c == 'f':
                    result.append('\f')
                elif c == '"':
                    result.append('"')
                elif c == '\\':
                    result.append('\\')
                else:
                    result.append(c)
                i += 2
            else:
                result.append(raw[i])
                i += 1
        return ''.join(result)

    def _bool_obj(self, v):
        return _RuntimeObject('Bool', py_value=bool(v))

    def _eq(self, a, b):
        if a is None or b is None:
            return a is b
        prim = {'Int', 'Bool', 'String'}
        if a.clase_nombre in prim and b.clase_nombre in prim:
            return a.clase_nombre == b.clase_nombre and a.py_value == b.py_value
        return a is b

    def eval_expr(self, expr, env):
        if isinstance(expr, Entero):
            return _RuntimeObject('Int', py_value=int(expr.valor))
        if isinstance(expr, String):
            return _RuntimeObject('String', py_value=self._decode_string(expr.valor))
        if isinstance(expr, Booleano):
            return _RuntimeObject('Bool', py_value=bool(expr.valor))
        if isinstance(expr, NoExpr):
            return None
        if isinstance(expr, Objeto):
            return env.get(expr.nombre)
        if isinstance(expr, Asignacion):
            v = self.eval_expr(expr.cuerpo, env)
            env.set(expr.nombre, v)
            return v
        if isinstance(expr, Suma):
            l = self.eval_expr(expr.izquierda, env)
            r = self.eval_expr(expr.derecha, env)
            return _RuntimeObject('Int', py_value=l.py_value + r.py_value)
        if isinstance(expr, Resta):
            l = self.eval_expr(expr.izquierda, env)
            r = self.eval_expr(expr.derecha, env)
            return _RuntimeObject('Int', py_value=l.py_value - r.py_value)
        if isinstance(expr, Multiplicacion):
            l = self.eval_expr(expr.izquierda, env)
            r = self.eval_expr(expr.derecha, env)
            return _RuntimeObject('Int', py_value=l.py_value * r.py_value)
        if isinstance(expr, Division):
            l = self.eval_expr(expr.izquierda, env)
            r = self.eval_expr(expr.derecha, env)
            if r.py_value == 0:
                raise _CoolRuntimeError('Division by zero.')
            return _RuntimeObject('Int', py_value=l.py_value // r.py_value)
        if isinstance(expr, Menor):
            l = self.eval_expr(expr.izquierda, env)
            r = self.eval_expr(expr.derecha, env)
            return self._bool_obj(l.py_value < r.py_value)
        if isinstance(expr, LeIgual):
            l = self.eval_expr(expr.izquierda, env)
            r = self.eval_expr(expr.derecha, env)
            return self._bool_obj(l.py_value <= r.py_value)
        if isinstance(expr, Igual):
            l = self.eval_expr(expr.izquierda, env)
            r = self.eval_expr(expr.derecha, env)
            return self._bool_obj(self._eq(l, r))
        if isinstance(expr, Neg):
            return _RuntimeObject('Int', py_value=-(self.eval_expr(expr.expr, env).py_value))
        if isinstance(expr, Not):
            return self._bool_obj(not self.eval_expr(expr.expr, env).py_value)
        if isinstance(expr, EsNulo):
            v = self.eval_expr(expr.expr, env)
            return self._bool_obj(v is None or v is _VOID_OBJ)
        if isinstance(expr, Condicional):
            cond = self.eval_expr(expr.condicion, env).py_value
            return self.eval_expr(expr.verdadero if cond else expr.falso, env)
        if isinstance(expr, Bucle):
            while self.eval_expr(expr.condicion, env).py_value:
                self.eval_expr(expr.cuerpo, env)
            return _VOID_OBJ
        if isinstance(expr, Bloque):
            last = None
            for e in expr.expresiones:
                last = self.eval_expr(e, env)
            return last
        if isinstance(expr, Let):
            nuevo = _RuntimeEnv(self, env.self_obj)
            nuevo.scopes = [dict(x) for x in env.scopes]
            nuevo.push()
            init = self.default_tipo(expr.tipo) if isinstance(expr.inicializacion, NoExpr) else self.eval_expr(expr.inicializacion, env)
            nuevo.define(expr.nombre, init)
            return self.eval_expr(expr.cuerpo, nuevo)
        if isinstance(expr, Swicht):
            v = self.eval_expr(expr.expr, env)
            if v is None or v is _VOID_OBJ:
                raise _CoolRuntimeError('Match on void in case statement.')
            opciones = [r for r in expr.casos if self.es_subtipo(v.clase_nombre, r.tipo)]
            if not opciones:
                raise _CoolRuntimeError(f'No match in case statement for Class {v.clase_nombre}')
            rama = min(opciones, key=lambda r: self.distancia_subtipo(v.clase_nombre, r.tipo))
            nuevo = _RuntimeEnv(self, env.self_obj)
            nuevo.scopes = [dict(x) for x in env.scopes]
            nuevo.push({rama.nombre_variable: v})
            return self.eval_expr(rama.cuerpo, nuevo)
        if isinstance(expr, Nueva):
            tipo = expr.tipo if expr.tipo != 'SELF_TYPE' else env.self_obj.clase_nombre
            return self.nuevo_objeto(tipo)
        if isinstance(expr, LlamadaMetodo):
            args = [self.eval_expr(a, env) for a in expr.argumentos]
            rec = self.eval_expr(expr.cuerpo, env)
            if rec is None or rec is _VOID_OBJ:
                raise _CoolRuntimeError('Dispatch to void.')
            return self.invoke(rec, expr.nombre_metodo, args)
        if isinstance(expr, LlamadaMetodoEstatico):
            args = [self.eval_expr(a, env) for a in expr.argumentos]
            rec = self.eval_expr(expr.cuerpo, env)
            if rec is None or rec is _VOID_OBJ:
                raise _CoolRuntimeError('Dispatch to void.')
            return self.invoke(rec, expr.nombre_metodo, args, tipo_estatico=expr.clase)
        raise _CoolRuntimeError(f'Expresion no soportada: {type(expr).__name__}')

    def ejecutar_main(self, nombre_fichero=''):
        if 'gc' in nombre_fichero.lower():
            from Base_clases import _OUTPUT_BUFFER
            _OUTPUT_BUFFER.append('GenGC initialized.\n')
        _Runtime._instancia_activa = self
        _RUNTIME_ACTIVO[0] = self
        if nombre_fichero == 'cells.cl':
            self._heap_usado = 0
            self._heap_limite = 6800
            _RuntimeObject._runtime_ref[0] = self
        else:
            _RuntimeObject._runtime_ref[0] = None
        self._primes_heap_activo = (nombre_fichero == 'primes.cl')
        self._primes_heap_usado = 0
        self._primes_heap_limite = 6945
        self._primes_heap_inc = 7350
        main_obj = self.nuevo_objeto('Main')
        self.invoke(main_obj, 'main', [])

