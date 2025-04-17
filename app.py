from flask import Flask, jsonify, request
import requests
import pdfplumber
import re
import logging

# Desativa os logs do pdfminer
logging.getLogger("pdfminer").setLevel(logging.ERROR)

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "API da Fenabrave Online!"})

@app.route('/extrair_emplacamentos', methods=['GET'])
def extrair_emplacamentos_api():
    ano = request.args.get('ano')
    mes = request.args.get('mes')

    if not ano or not mes:
        return jsonify({"erro": "Parâmetros 'ano' e 'mes' são obrigatórios. Ex: ?ano=2025&mes=03"}), 400

    try:
        ano = int(ano)
        mes = int(mes)
        if mes < 1 or mes > 12:
            raise ValueError
    except ValueError:
        return jsonify({"erro": "Ano deve ser inteiro e mês deve estar entre 1 e 12."}), 400

    nome_arquivo = f"{ano}_{str(mes).zfill(2)}_02.pdf"
    url_pdf = f"https://www.fenabrave.org.br/portal/files/{nome_arquivo}"
    caminho_pdf = "dados_fenabrave.pdf"

    response = requests.get(url_pdf)
    if response.status_code != 200:
        return jsonify({"error": f"Erro ao baixar PDF. Código HTTP: {response.status_code}"}), 500

    with open(caminho_pdf, "wb") as f:
        f.write(response.content)

    resultado_final = []

    mapa_meses = {
        "jan": "janeiro", "fev": "fevereiro", "mar": "marco", "abr": "abril",
        "mai": "maio", "jun": "junho", "jul": "julho", "ago": "agosto",
        "set": "setembro", "out": "outubro", "nov": "novembro", "dez": "dezembro"
    }

    with pdfplumber.open(caminho_pdf) as pdf:
        for numero_pagina in range(10, 16):  # páginas 11 a 16
            pagina = pdf.pages[numero_pagina]
            texto_extraido = pagina.extract_text()

            if not texto_extraido:
                continue

            texto_limpo = texto_extraido.replace("\n", " ")

            nome_mes_1 = "mes_1"
            nome_mes_2 = "mes_2"

            if "acumulado até" in texto_limpo.lower():
                match_acumulado = re.search(r"acumulado até\s+([A-Za-z]{3})\/\d{4}", texto_limpo, re.IGNORECASE)
                if match_acumulado:
                    mes_abrev = match_acumulado.group(1).lower()
                    if mes_abrev in mapa_meses:
                        mes_2_full = mapa_meses[mes_abrev]
                        lista_abreviacoes = list(mapa_meses.keys())
                        idx = lista_abreviacoes.index(mes_abrev)
                        mes_1_abrev = lista_abreviacoes[idx - 1] if idx > 0 else lista_abreviacoes[-1]
                        mes_1_full = mapa_meses[mes_1_abrev]
                        nome_mes_1 = mes_1_full
                        nome_mes_2 = mes_2_full

            padrao = r"\d+º\s([A-Z0-9\/\-\.\s]+?)\s(\d{1,3}(?:\.\d{3})*|0,00)\s(\d{1,3}(?:\.\d{3})*|0,00)\s(\d{1,3}(?:\.\d{3})*)"
            matches = re.findall(padrao, texto_limpo)

            for match in matches:
                modelo = match[0].strip()
                valor_mes_1 = int(match[1].replace(".", "").replace(",", "")) if match[1] != "0,00" else 0
                valor_mes_2 = int(match[2].replace(".", "").replace(",", "")) if match[2] != "0,00" else 0
                acumulado = int(match[3].replace(".", "").replace(",", ""))

                resultado_final.append({
                    "modelo": modelo,
                    nome_mes_1: valor_mes_1,
                    nome_mes_2: valor_mes_2,
                    "acumulado": acumulado,
                    "pagina": numero_pagina + 1
                })

    if not resultado_final:
        return jsonify({"error": "Nenhum dado encontrado nas páginas indicadas."}), 404

    return jsonify(resultado_final)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
