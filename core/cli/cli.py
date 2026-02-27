"""
core/cli/cli.py
Interface de linha de comando para validação e leitura de arquivos SFF.
"""
import sys

from core.reader.reader import read_sff_file
from core.validator.validator import validate_sff_structure
from core.compiler.compiler import compile_sff
from core.logger.logger import Logger

logger = Logger()

def main():
    if len(sys.argv) < 3:
        print("Uso: python -m core.cli.cli <validate|compile> <arquivo.sff>")
        sys.exit(1)
    command = sys.argv[1]
    filepath = sys.argv[2]
    if command == "validate":
        logger.info(f"Validando arquivo {filepath}")
        try:
            data = read_sff_file(filepath)
            errors = validate_sff_structure(data)
            if errors:
                for err in errors:
                    logger.error(err)
                print("Erros de validação encontrados:")
                for err in errors:
                    print(f"- {err}")
                sys.exit(2)
            else:
                logger.info("Validação estrutural OK")
                print("Validação estrutural OK")
        except Exception as e:
            logger.error(str(e))
            print(f"Erro: {e}")
            sys.exit(3)
    elif command == "compile":
        logger.info(f"Compilando arquivo {filepath}")
        try:
            data = read_sff_file(filepath)
            compiled = compile_sff(data)
            errors = compiled['validation']['errors']
            warnings = compiled['validation']['warnings']
            if errors:
                for err in errors:
                    logger.error(err)
                print("Erros de validação lógica encontrados:")
                for err in errors:
                    print(f"- {err}")
                sys.exit(1)
            else:
                logger.info("Compilação OK")
                print("Compilação OK!")
                print("Índices prev/next:")
                print("prev:", compiled['index']['prev'])
                print("next:", compiled['index']['next'])
                if warnings:
                    print("Avisos:")
                    for w in warnings:
                        logger.warn(w)
                        print(f"- {w}")
                sys.exit(0)
        except Exception as e:
            logger.error(str(e))
            print(f"Erro: {e}")
            sys.exit(3)
    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
