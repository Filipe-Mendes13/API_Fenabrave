from flask import Flask, jsonify
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

@app.route('/dados', methods=['GET'])
def obter_dados():
    url_pdf = "https://www.fenabrave.org.br/portal/files/2025_03_02.pdf"
    caminho_pdf = "dados_fenabrave.pdf"

    response = requests.get(url_pdf)
    if response.status_code == 200:
        with open(caminho_pdf, "wb") as f:
            f.write(response.content)
    else:
        return jsonify({"erro": f"Erro ao baixar PDF. Código HTTP: {response.status_code}"}), 500

    with pdfplumber.open(caminho_pdf) as pdf:
        pagina = pdf.pages[6]
        texto_extraido = pagina.extract_text()

    if not texto_extraido:
        return jsonify({"erro": "Erro ao extrair texto do PDF."}), 500

    texto_limpo = texto_extraido.replace("\n", " ")

    padrao = r"(\d+º)\s([A-Z0-9\/\-\.\s]+?)\s(\d{1,3}(?:\.\d{3})*)"
    matches = re.findall(padrao, texto_limpo)

    todos_os_carros = []
    for i, match in enumerate(matches):
        modelo = match[1].strip()
        emplacamentos = int(match[2].replace(".", ""))
        categoria = "Automóvel" if i < 50 else "Comercial Leve"

        todos_os_carros.append({
            "modelo": modelo,
            "emplacamentos": emplacamentos,
            "categoria": categoria
        })

    return jsonify(todos_os_carros)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
