import requests
import pdfplumber
import json
import re
import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/extrair_emplacamentos', methods=['GET'])
def extrair_emplacamentos():
    # URL do PDF da Fenabrave
    url_pdf = "https://www.fenabrave.org.br/portal/files/2025_03_02.pdf"
    caminho_pdf = "dados_fenabrave.pdf"

    # Baixar o PDF
    response = requests.get(url_pdf)
    if response.status_code == 200:
        with open(caminho_pdf, "wb") as f:
            f.write(response.content)
    else:
        return jsonify({"error": f"Erro ao baixar PDF. Código HTTP: {response.status_code}"}), 400

    # Extrair texto da página 7
    with pdfplumber.open(caminho_pdf) as pdf:
        pagina = pdf.pages[6]  # Página 7 (índice 6)
        texto_extraido = pagina.extract_text()

    # Verificar extração
    if not texto_extraido:
        return jsonify({"error": "Erro ao extrair texto do PDF."}), 400

    # Pré-processar: remover quebras de linha mal posicionadas
    texto_limpo = texto_extraido.replace("\n", " ")

    # Regex ajustada
    padrao = r"(\d+º)\s([A-Z0-9\/\-\.\s]+?)\s(\d{1,3}(?:\.\d{3})*)"

    # Encontrar todos os matches
    matches = re.findall(padrao, texto_limpo)

    todos_os_carros = []

    # Categorias definidas a partir das posições (Automóvel ou Comercial Leve)
    for i, match in enumerate(matches):
        modelo = match[1].strip()
        emplacamentos = int(match[2].replace(".", ""))  # Remover ponto de milhar
        categoria = "Automóvel" if i < 50 else "Comercial Leve"

        todos_os_carros.append({
            "modelo": modelo,
            "emplacamentos": emplacamentos,
            "categoria": categoria
        })

    # Retornar o JSON com os dados
    return jsonify(todos_os_carros)


if __name__ == "__main__":
    # A variável de ambiente PORT será definida pelo Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
