from flask import Flask, jsonify
import requests
import pdfplumber
import json
import re
import logging

# Configuração do Flask
app = Flask(__name__)

# URL do PDF da Fenabrave
url_pdf = "https://www.fenabrave.org.br/portal/files/2025_03_02.pdf"
caminho_pdf = "dados_fenabrave.pdf"

# Configuração de log
logging.getLogger("pdfminer").setLevel(logging.ERROR)

# Função para extrair dados do PDF
def extrair_emplacamentos():
    # Baixar o PDF
    response = requests.get(url_pdf)
    if response.status_code != 200:
        return {"error": f"Erro ao baixar PDF. Código HTTP: {response.status_code}"}, 500

    # Salvar PDF localmente
    with open(caminho_pdf, "wb") as f:
        f.write(response.content)

    # Extrair texto da página 7
    with pdfplumber.open(caminho_pdf) as pdf:
        pagina = pdf.pages[6]  # Página 7 (índice 6)
        texto_extraido = pagina.extract_text()

    # Verificar extração
    if not texto_extraido:
        return {"error": "Erro ao extrair texto do PDF."}, 500

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

    return jsonify(todos_os_carros)

# Rota para extrair emplacamentos
@app.route('/extrair_emplacamentos', methods=['GET'])
def extrair_emplacamentos_api():
    return extrair_emplacamentos()

# Rodar a aplicação Flask
if __name__ == "__main__":
    app.run(debug=True)
