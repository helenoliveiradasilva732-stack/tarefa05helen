import math


def validar_texto(valor, campo):
    texto = str(valor).strip()
    if not texto:
        raise ValueError(f"Informe {campo}.")
    return texto


def validar_preco(valor):
    try:
        preco = float(valor)
    except (TypeError, ValueError) as error:
        raise ValueError("O preço deve ser um número válido.") from error
    if not math.isfinite(preco) or preco < 0:
        raise ValueError("O preço não pode ser negativo.")
    return preco


def validar_quantidade(valor, permitir_zero=False):
    try:
        quantidade = int(valor)
    except (TypeError, ValueError) as error:
        raise ValueError("A quantidade deve ser um número inteiro.") from error
    if str(valor).strip() != str(quantidade):
        raise ValueError("A quantidade deve ser um número inteiro.")
    minimo = 0 if permitir_zero else 1
    if quantidade < minimo:
        if permitir_zero:
            raise ValueError("A quantidade não pode ser negativa.")
        raise ValueError("A quantidade deve ser maior que zero.")
    return quantidade
