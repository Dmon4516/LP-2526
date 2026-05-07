import os
import re
import sys



DIRECTORIO = os.path.dirname(os.path.abspath(__file__))
sys.path.append(DIRECTORIO)

from Lexer import *
from Clases import *

PRACTICAS = ("01", "02", "03")  
DEBUG = False   
NUMLINEAS = 3   
sys.path.append(DIRECTORIO)

def subdirectorios_practica(practica):
    if practica == '01':
        return ('grading', 'minimos', 'minimo')
    if practica == '02':
        return ('grading', 'minimos', 'minimo')
    if practica == '03':
        return ('grading', 'minimos', 'minimo')
    return ()


for PRACTICA in PRACTICAS:
    for subdir in subdirectorios_practica(PRACTICA):
        DIR = os.path.join(DIRECTORIO, PRACTICA, subdir)
        if not os.path.isdir(DIR):
            continue

        FICHEROS = os.listdir(DIR)
        TESTS = [fich for fich in FICHEROS
                 if os.path.isfile(os.path.join(DIR, fich)) and
                 re.search(r"^[a-zA-Z].*\.(cool|test|cl)$", fich) and
                 os.path.isfile(os.path.join(DIR, fich + '.out'))]
        TESTS.sort()

        if not TESTS:
            continue

        print(f'>>> Practica {PRACTICA}/{subdir}: {len(TESTS)} tests')
        for fich in TESTS:
            lexer = CoolLexer()
            f = open(os.path.join(DIR, fich), 'r', newline='')
            g = open(os.path.join(DIR, fich + '.out'), 'r', newline='')
            if os.path.isfile(os.path.join(DIR, fich) + '.nuestro'):
                os.remove(os.path.join(DIR, fich) + '.nuestro')
            if os.path.isfile(os.path.join(DIR, fich) + '.bien'):
                os.remove(os.path.join(DIR, fich) + '.bien')
            texto = ''
            entrada = f.read()
            f.close()
            if PRACTICA == '01':
                texto = '\n'.join(lexer.format_output(entrada))
                texto = f'#name "{fich}"\n' + texto
                resultado = g.read()
                g.close()
                texto = re.sub(r'#\d+\b', '', texto)
                resultado = re.sub(r'#\d+\b', '', resultado)
                nuestro = [linea.strip() for linea in texto.split('\n') if linea.strip()]
                bien = [linea.strip() for linea in resultado.split('\n') if linea.strip()]
                texto = '\n'.join(nuestro)
                resultado = '\n'.join(bien)
                if texto.strip().split() != resultado.strip().split():
                    print(f"Revisa el fichero {PRACTICA}/{subdir}/{fich}")
                    if DEBUG:
                        f = open(os.path.join(DIR, fich) + '.nuestro', 'w')
                        g = open(os.path.join(DIR, fich) + '.bien', 'w')
                        f.write(texto.strip())
                        g.write(resultado.strip())
                        f.close()
                        g.close()
            elif PRACTICA in ('02', '03'):
                from Parser import CoolParser

                parser = CoolParser()
                parser.nombre_fichero = fich
                parser.errores = []
                bien = ''.join([c for c in g.readlines() if c and '#' not in c])
                g.close()
                j = parser.parse(lexer.tokenize(entrada))
                try:
                    if PRACTICA == '03' and j:
                        j.Tipo()

                    if j and not parser.errores:
                        if PRACTICA == '03':
                            resultado = interpretar_programa(j, fich, DIR).rstrip('\n')
                        else:
                            resultado = '\n'.join([c for c in j.str(0).split('\n')
                                                   if c and '#' not in c])
                    else:
                        resultado = '\n'.join(parser.errores)
                        resultado += '\n' + "Compilation halted due to lex and parse errors"

                    if resultado.lower().strip().split() != bien.lower().strip().split():
                        print(f"Revisa el fichero {PRACTICA}/{subdir}/{fich}")
                    if DEBUG:
                        nuestro = [linea for linea in resultado.split('\n') if linea]
                        bien = [linea for linea in bien.split('\n') if linea]
                        linea = 0
                        while linea < min(len(nuestro), len(bien)) and nuestro[linea:linea + NUMLINEAS] == bien[linea:linea + NUMLINEAS]:
                            linea += 1
                        print('\n'.join(nuestro[linea:linea + NUMLINEAS]))
                        print('\n'.join(bien[linea:linea + NUMLINEAS]))

                except Exception as e:
                    print(f"Lanza excepción en {PRACTICA}/{subdir}/{fich} con el texto {e}")
