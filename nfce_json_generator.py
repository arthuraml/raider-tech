import sqlite3
import json

def obterCaminhoBancoDados():
    conn = sqlite3.connect('bd/bbcia.db')
    cursor = conn.cursor()
    cursor.execute('SELECT bd_servidor FROM config')
    caminho_banco_dados = cursor.fetchone()[0]
    conn.close()
    return caminho_banco_dados

def get_next_id(caminho_banco_dados):
    conn = sqlite3.connect(caminho_banco_dados)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(ID) FROM nfce_emitidas")
    max_id = cursor.fetchone()[0]
    conn.close()
    return max_id + 1 if max_id else 1

def get_ambiente_emissao():
    conn = sqlite3.connect('bd/bbcia.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ambiente_emissao_nfe FROM config')
    ambiente = cursor.fetchone()[0]
    conn.close()
    return ambiente

def get_client_data(client_id, is_cpf, caminho_banco_dados):
    conn = sqlite3.connect(caminho_banco_dados)
    cursor = conn.cursor()
    table_name = 'cadastro_PF' if is_cpf else 'cadastro_PJ'
    column_name = 'CPF' if is_cpf else 'CNPJ'
    cursor.execute(f"SELECT * FROM {table_name} WHERE {column_name} = ?", (client_id,))
    data = cursor.fetchone()
    conn.close()

    if is_cpf:
        return {
            "cpf": data[2],
            "nome_completo": data[1],
            "endereco": data[5],
            "complemento": data[7],
            "numero": data[6],
            "bairro": data[8],
            "cidade": data[9],
            "uf": data[10],
            "cep": data[4],
            "telefone": data[3],
            "email": data[11]
        }
    else:
        return {
            "cnpj": data[2],
            "razao_social": data[1],
            "endereco": data[4],
            "complemento": data[11],
            "numero": data[5],
            "bairro": data[7],
            "cidade": data[8],
            "uf": data[9],
            "cep": data[6],
            "telefone": data[3],
            "email": data[10],
            "ie": data[14]
        }

def get_product_data(products, caminho_banco_dados):
    conn = sqlite3.connect(caminho_banco_dados)
    cursor = conn.cursor()
    product_list = []
    for product in products:
        cursor.execute("SELECT ncm, unidade_medida FROM produtos WHERE referencia = ?", (product['codigo'],))
        data = cursor.fetchone()
        if data:
            product_data = {
                "nome": product['nome'],
                "codigo": product['codigo'],
                "ncm": data[0],
                "quantidade": product['quantidade'],
                "unidade": data[1],
                "origem": 0,
                "subtotal": product['subtotal'],
                "total": product['total'],
                "classe_imposto": "REF135399234"
            }
            product_list.append(product_data)
    conn.close()
    return product_list

def generate_nfce_json(client_id, products, is_cpf=True, payment_method=0, form_of_payment=0, valor_pagamento=0.0, caminho_banco_dados = obterCaminhoBancoDados()):
    ambiente = get_ambiente_emissao()
    product_data = get_product_data(products, caminho_banco_dados)
    print("Product data inside generate_nfce_json:")
    print(json.dumps(product_data, indent=4, ensure_ascii=False))
    
    nfce_data = {
        "ID": get_next_id(caminho_banco_dados),
        "url_notificacao": "",
        "operacao": 1,
        "natureza_operacao": "Venda de mercadoria",
        "modelo": 2,
        "finalidade": 1,
        "ambiente": ambiente,
        "cliente": get_client_data(client_id, is_cpf, caminho_banco_dados),
        "produtos": product_data,
        "pedido": {
            "pagamento": payment_method,
            "forma_pagamento": form_of_payment,
            "valor_pagamento": valor_pagamento,
            "presenca": 1,
            "modalidade_frete": 9,
            "frete": "0",
            "desconto": "0"
        }
    }

    print("Dados enviados para a emissão da NFC-e:")
    print(json.dumps(nfce_data, indent=4, ensure_ascii=False))
    
    return nfce_data

def generate_nfce_json_without_client(products, payment_method=0, form_of_payment=0, valor_pagamento=0.0, caminho_banco_dados = obterCaminhoBancoDados()):
    ambiente = get_ambiente_emissao()
    product_data = get_product_data(products, caminho_banco_dados)
    print("Product data inside generate_nfce_json_without_client:")
    print(json.dumps(product_data, indent=4, ensure_ascii=False))
    
    nfce_data = {
        "ID": get_next_id(caminho_banco_dados),
        "url_notificacao": "",
        "operacao": 1,
        "natureza_operacao": "Venda de mercadoria",
        "modelo": 2,
        "finalidade": 1,
        "ambiente": ambiente,
        "produtos": product_data,
        "pedido": {
            "pagamento": payment_method,
            "forma_pagamento": form_of_payment,
            "valor_pagamento": valor_pagamento,
            "presenca": 1,
            "modalidade_frete": 9,
            "frete": "0",
            "desconto": "0"
        }
    }

    print("Dados enviados para a emissão da NFC-e sem cliente:")
    print(json.dumps(nfce_data, indent=4, ensure_ascii=False))
    
    return nfce_data
