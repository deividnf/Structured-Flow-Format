"""
core/cli/cli.py
Interface de linha de comando para validação e leitura de arquivos SFF.
"""
import sys
from core.reader.reader import read_sff_file
from core.validator.validator import validate_sff_structure
from core.logger.logger import Logger

logger = Logger()

def main():
    if len(sys.argv) < 3:
        print("Uso: python -m core.cli.cli validate <arquivo.sff>")
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
    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
