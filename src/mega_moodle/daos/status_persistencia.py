from enum import Enum


class StatusPersistencia(Enum):
    OK = "ok"
    DUPLICADO = "duplicado"
    ERRO = "erro"
