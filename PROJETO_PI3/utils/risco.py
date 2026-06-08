def classificar_risco(dados):
    sintoma = (dados.get("sintoma_principal") or "").lower()
    descricao = (dados.get("descricao_sintomas") or "").lower()

    temperatura = float(dados.get("temperatura") or 0)
    saturacao = int(dados.get("saturacao_oxigenio") or 100)
    frequencia = int(dados.get("frequencia_cardiaca") or 0)
    dor = int(dados.get("escala_dor") or 0)

    texto = sintoma + " " + descricao

    if (
        "parada" in texto
        or "inconsciente" in texto
        or "convulsão" in texto
        or "falta de ar intensa" in texto
        or saturacao < 90
    ):
        return "VERMELHO"

    if (
        "falta de ar" in texto
        or "dor no peito" in texto
        or temperatura >= 39
        or dor >= 8
        or frequencia >= 130
    ):
        return "LARANJA"

    if (
        temperatura >= 38
        or dor >= 5
        or "vômito" in texto
        or "tontura" in texto
    ):
        return "AMARELO"

    if dor >= 2:
        return "VERDE"

    return "AZUL"