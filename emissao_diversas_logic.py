from PyQt5 import QtWidgets, QtCore, QtGui
from emissao_diversas_ui import Ui_Dialog
import sys
import sqlite3
import locale
from datetime import datetime
import pytz
import mysql.connector
from user_session import UserSession
from PyQt5.QtWidgets import QCheckBox, QMessageBox
import http.client
import json
import nfce_json_generator
from PyQt5.QtCore import QThread, pyqtSignal

class EmitirNotasThread(QThread):
    update_progress = pyqtSignal(int)
    finished_successfully = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, cupons, parent=None):
        super().__init__(parent)
        self.cupons = cupons
        self.parent = parent
        self.error_flag = False

    def run(self):
        total_cupons = len(self.cupons)
        for index, cupom_number in enumerate(self.cupons):
            try:
                self.parent.emitir_nota_fiscal_individual(cupom_number)
                progress = int((index + 1) / total_cupons * 100)
                self.update_progress.emit(progress)
            except Exception as e:
                self.error_flag = True
                self.error_occurred.emit(str(e))
                break
        if not self.error_flag:
            self.finished_successfully.emit()

class EmissaoDiversasLogic(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.session = UserSession()
        self.valor_selecionado = 0
        self.carregar_lojas()

        # Configurar a localidade para o formato brasileiro
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

        # Conectar o botão a uma função
        self.pushButton.clicked.connect(self.buscar_vendas)

        # Inicializar os dados com a data atual
        self.inicializar_data_atual()
        self.radioButton_2.setChecked(True)
        self.lineEdit_6.setText(locale.currency(self.obter_limite_emissao(), grouping=True))
        #Alinha lineEdit_3 a direita
        self.lineEdit_3.setAlignment(QtCore.Qt.AlignRight)
        self.lineEdit_4.setAlignment(QtCore.Qt.AlignRight)
        self.lineEdit_5.setAlignment(QtCore.Qt.AlignRight)
        self.lineEdit_6.setAlignment(QtCore.Qt.AlignRight)
        self.pushButton_2.clicked.connect(self.emitir_notas_fiscais_selecionadas)

    def inicializar_data_atual(self):
        # Definir o fuso horário de São Paulo
        fuso_sao_paulo = pytz.timezone('America/Sao_Paulo')
        data_atual = datetime.now(fuso_sao_paulo)
        primeiro_dia_do_mes = data_atual.replace(day=1)

        # Converter a data para o formato brasileiro
        data_formatada = data_atual.strftime('%d/%m/%Y')
        primeiro_dia_do_mes_formatado = primeiro_dia_do_mes.strftime('%d/%m/%Y')

        # Definir as datas nos lineEdits
        self.lineEdit.setText(primeiro_dia_do_mes_formatado)
        self.lineEdit_2.setText(data_formatada)

    def obterCaminhoBancoDados(self):
        conn = sqlite3.connect('bd/bbcia.db')
        cursor = conn.cursor()
        cursor.execute('SELECT bd_servidor FROM config')
        caminho_banco_dados = cursor.fetchone()[0]
        conn.close()
        return caminho_banco_dados
    
    def obter_codigo_loja(self):
        return self.comboBox.currentData()
    
    def obter_nome_loja(self):
        texto_completo = self.comboBox.currentText()
        nome_loja = texto_completo.split(' - ', 1)[1] if ' - ' in texto_completo else ''
        return nome_loja

    def carregar_lojas(self):
        try:
            conn = self.get_mysql_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT loja_cod, loja FROM lojas ORDER BY loja")
            lojas = cursor.fetchall()
            for loja_cod, nome_loja in lojas:
                self.comboBox.addItem(f"{loja_cod} - {nome_loja}", loja_cod)
        except mysql.connector.Error as err:
            QtWidgets.QMessageBox.warning(self, 'Erro de Banco de Dados', f'Ocorreu um erro ao acessar o banco de dados: {err}')
        finally:
            if conn.is_connected():
                conn.close()
    
    def obter_limite_emissao(self):
        conn = self.get_mysql_connection()
        cursor = conn.cursor()
        loja_cod = 12

        # Altere a linha abaixo, substituindo "?" por "%s" para compatibilidade com MySQL
        cursor.execute("SELECT total_nfe_mensal FROM lojas WHERE loja_cod = %s", (loja_cod,))
        limite_emissao = cursor.fetchone()[0]
        conn.close()
        return limite_emissao


    def get_mysql_connection(self):
        return mysql.connector.connect(
            host='34.151.192.214',
            user='arthuraml',
            password='Ij{p=6$Y2Wits7bAo',
            database='bbcia'
        )
    
    def atualizar_valor_selecionado(self, state):
        sender = self.sender()
        row_index = self.tableWidget.indexAt(sender.pos()).row()
        valor_celula = self.tableWidget.item(row_index, 2).text().replace('R$', '').replace('.', '').replace(',', '.')
        valor = float(valor_celula)
        
        if state == QtCore.Qt.Checked:
            self.valor_selecionado += valor
        else:
            self.valor_selecionado -= valor
        
        self.lineEdit_5.setText(locale.currency(self.valor_selecionado, grouping=True))  # Atualizar o valor no lineEdit_5


    def buscar_vendas(self):
        conn = self.get_mysql_connection()
        cursor = conn.cursor()

        #Se o radioButton estiver selecionado, adicionar na query SQL "AND nfe_emitida = 1", se o radioButton_2 estiver selecionado, adicionar "AND nfe_emitida = 0"
        if self.radioButton.isChecked():
            query_nfe = "AND nfe_emitida = 1"
        elif self.radioButton_2.isChecked():
            query_nfe = "AND nfe_emitida = 0"

        try:
            # Converter datas para timestamp
            data_inicial = datetime.strptime(self.lineEdit.text(), '%d/%m/%Y').timestamp() * 1000
            data_final = 86400000 + datetime.strptime(self.lineEdit_2.text(), '%d/%m/%Y').timestamp() * 1000
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Data Inválida", "Por favor, insira datas válidas.")
            return

        query = f"""
        SELECT cupom, 
            MAX(CASE WHEN preco_aplicado = 'varejo' THEN preco_varejo 
                        WHEN preco_aplicado = 'atacado' THEN preco_atacado 
                        ELSE 0 END) as valor,
            MAX(pagamento_timestamp) as data_venda, 
            terminal, nome_vendedor, forma_pagamento, 
            cancelado, pagamento, nfe_emitida
        FROM vendas 
        WHERE (pagamento_timestamp >= %s AND pagamento_timestamp <= %s)
        {query_nfe}
        AND cancelado = 0
        GROUP BY cupom
        """
        cursor.execute(query, (data_inicial, data_final))
        vendas_agrupadas = cursor.fetchall()

        if not vendas_agrupadas:
            QtWidgets.QMessageBox.information(self, "Sem Vendas", "Nenhuma venda encontrada nesse período.")
            conn.close()
            return

        conn.close()

        query_notas_emitidas = """
        SELECT MAX(CASE WHEN preco_aplicado = 'varejo' THEN preco_varejo 
                        WHEN preco_aplicado = 'atacado' THEN preco_atacado 
                        ELSE 0 END) as valor
        FROM vendas 
        WHERE (pagamento_timestamp >= ? AND pagamento_timestamp <= ?)
        AND nfe_emitida = 1
        AND cancelado = 0
        GROUP BY cupom
        """
        cursor = conn.cursor()
        cursor.execute(query_notas_emitidas, (data_inicial, data_final))
        valor_emitida = cursor.fetchall()
        valor_total_emitida = 0
        for valor in valor_emitida:
            valor_total_emitida += valor[0]

        print(valor_total_emitida)
        print(query_notas_emitidas)
        conn.close()


        self.tableWidget.setRowCount(len(vendas_agrupadas))
        self.tableWidget.setColumnCount(7)  # Adicionamos mais uma coluna para o "Status"
        self.tableWidget.setHorizontalHeaderLabels(['Seleção', 'Cupom', 'Valor', 'Data do Pagamento', 'Vendedor', 'Forma de Pagamento', 'NFe Emitida'])

        # Ajustar o tamanho das colunas
        self.tableWidget.setColumnWidth(0, 50)  # Coluna Cupom
        self.tableWidget.setColumnWidth(1, 60)  # Coluna Cupom
        self.tableWidget.setColumnWidth(2, 100)  # Coluna Valor
        self.tableWidget.setColumnWidth(3, 120)
        self.tableWidget.setColumnWidth(4, 200)  # Coluna Vendedor
        self.tableWidget.setColumnWidth(5, 150)  # Coluna Forma de Pagamento
        self.tableWidget.setColumnWidth(6, 100)  # Coluna NFe Emitida

        valor_total_pago = 0
        valor_total = 0
        self.valor_selecionado = 0  # Resetar o valor total selecionado quando uma nova busca é feita
        for row_num, venda_agrupada in enumerate(vendas_agrupadas):
            checkbox = QCheckBox()
            checkbox.stateChanged.connect(self.atualizar_valor_selecionado)  # Conectar o checkbox ao slot de atualização
            self.tableWidget.setCellWidget(row_num, 0, checkbox)
            cupom, valor, data_venda, terminal, nome_vendedor, forma_pagamento, cancelado, pagamento, nfe_emitida = venda_agrupada

            #Se nfe_emitida = 1, o checkBox deve ser bloqueado
            if nfe_emitida == 1:
                checkbox.setEnabled(False)

            # Formatar o valor para o formato monetário brasileiro
            valor_formatado = locale.currency(valor, grouping=True)

            # Determinar o status da venda
            if cancelado == 1:
                status = "Cancelado"
            elif pagamento == 1 and cancelado == 0:
                valor_total_pago += valor
                status = "Pago"
                valor_total += valor
            elif pagamento == 0 and cancelado == 0:
                status = "À receber"
                valor_total += valor

            if nfe_emitida == 1:
                nfe_emitida = "Emitida"
            else:
                nfe_emitida = "Não emitida"

            #Converter a data_venda de timestamp para formato brasileiro
            data_venda = datetime.fromtimestamp(data_venda / 1000).strftime('%d/%m/%Y %H:%M:%S')

            self.tableWidget.setItem(row_num, 1, QtWidgets.QTableWidgetItem(str(cupom)))
            self.tableWidget.setItem(row_num, 2, QtWidgets.QTableWidgetItem(valor_formatado))
            self.tableWidget.setItem(row_num, 3, QtWidgets.QTableWidgetItem(data_venda))
            self.tableWidget.setItem(row_num, 4, QtWidgets.QTableWidgetItem(nome_vendedor))
            self.tableWidget.setItem(row_num, 5, QtWidgets.QTableWidgetItem(forma_pagamento))
            self.tableWidget.setItem(row_num, 6, QtWidgets.QTableWidgetItem(nfe_emitida))
            #Limite de emissão será igual ao lineEdit_6, retirando a formatação monetária brasileira e convertido para float
            limite_emissao = float(self.lineEdit_6.text().replace('R$', '').replace('.', '').replace(',', '.'))
            a_emitir = limite_emissao - valor_total_emitida

        self.lineEdit_3.setText(locale.currency(a_emitir, grouping=True))
        self.lineEdit_4.setText(locale.currency(valor_total_emitida, grouping=True))
        self.lineEdit_5.setText(locale.currency(self.valor_selecionado, grouping=True))

    def emitir_notas_fiscais_selecionadas(self):
        selected_cupons = [self.tableWidget.item(row, 1).text() for row in range(self.tableWidget.rowCount()) if self.tableWidget.cellWidget(row, 0).isChecked()]
        if not selected_cupons:
            QMessageBox.warning(self, 'Erro', 'Nenhum cupom selecionado para emissão.')
            return
        
        self.progress_dialog = QtWidgets.QProgressDialog("Emitindo notas fiscais...", "Cancelar", 0, 100, self)
        self.progress_dialog.setAutoClose(True)
        self.progress_dialog.show()
        
        self.thread = EmitirNotasThread(selected_cupons, self)
        self.thread.update_progress.connect(self.progress_dialog.setValue)
        self.thread.finished_successfully.connect(self.on_all_invoices_emitted_successfully)
        self.thread.error_occurred.connect(self.on_emit_invoice_error)
        self.thread.start()

    def on_all_invoices_emitted_successfully(self):
        QMessageBox.information(self, "Emissão de NF-e", "Notas fiscais emitidas com sucesso")
        self.buscar_vendas()  # Refresh the data

    def on_emit_invoice_error(self, error_message):
        QMessageBox.warning(self, "Erro na Emissão", error_message)

    def obter_credenciais(self, loja_cod):
        conn = sqlite3.connect('bd/bbcia.db')
        cursor = conn.cursor()
        cursor.execute("SELECT consumer_key, consumer_secret, access_token, access_token_secret FROM lojas WHERE loja_cod = ?", (loja_cod,))
        credentials = cursor.fetchone()
        conn.close()
        return credentials

    def get_ambiente_emissao(self):
        conn = sqlite3.connect('bd/bbcia.db')
        cursor = conn.cursor()
        cursor.execute('SELECT ambiente_emissao_nfe FROM config')
        ambiente = cursor.fetchone()[0]
        conn.close()
        return ambiente

    def emitir_nota_fiscal_individual(self, cupom_number):
        caminho_banco = self.obterCaminhoBancoDados()
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT nome_do_produto, referencia, quantidade, estornado, preco_produto, 
                subtotal_produto, preco_atacado, preco_varejo, preco_aplicado 
            FROM vendas WHERE cupom = ? LIMIT 1""", (cupom_number,))  # Pegando um registro para definir o valor_pagamento
        product_info = cursor.fetchone()

        if not product_info:
            print(f"Nenhum produto encontrado para o cupom {cupom_number}.")
            return

        # Escolher entre preco_atacado e preco_varejo dependendo de preco_aplicado
        valor_pagamento = product_info[6] if product_info[8] == 'atacado' else product_info[7]

        # Obter todos produtos que não foram totalmente estornados
        cursor.execute("""
            SELECT nome_do_produto, referencia, quantidade, estornado, preco_produto, 
                subtotal_produto, preco_atacado, preco_varejo, preco_aplicado 
            FROM vendas WHERE cupom = ? AND quantidade > estornado""", (cupom_number,))
        products_info = cursor.fetchall()

        products = [{
            'nome': info[0],
            'codigo': str(info[1]).zfill(5),
            'quantidade': max(0, info[2] - info[3]),
            'subtotal': info[4],
            'total': info[5]
        } for info in products_info]

        if not products:
            print(f"Nenhum produto válido para o cupom {cupom_number} ou todos estornados.")
            conn.close()
            return

        payment_method = 0  # Placeholder value
        form_of_payment = 1  # Placeholder value

        request_data = nfce_json_generator.generate_nfce_json_without_client(products, payment_method, form_of_payment, valor_pagamento)

        if not request_data['produtos']:  # Certificar que a lista de produtos não está vazia
            QMessageBox.warning(self, 'Erro', 'Erro na preparação dos produtos para emissão da nota.')
            conn.close()
            return

        loja_cod = self.obter_codigo_loja()
        loja = self.obter_nome_loja()

        credentials = self.obter_credenciais(loja_cod)
        if not credentials:
            QMessageBox.warning(self, 'Erro', f'Credenciais para a loja {loja} não encontradas.')
            conn.close()
            return

        consumer_key, consumer_secret, access_token, access_token_secret = credentials

        headers = {
            'cache-control': "no-cache",
            'content-type': "application/json",
            'x-consumer-key': consumer_key,
            'x-consumer-secret': consumer_secret,
            'x-access-token': access_token,
            'x-access-token-secret': access_token_secret
        }

        ambiente = self.get_ambiente_emissao()

        http_conn = http.client.HTTPSConnection("webmaniabr.com")
        try:
            http_conn.request("POST", "/api/1/nfe/emissao/", json.dumps(request_data), headers)
            res = http_conn.getresponse()
            response_data = json.loads(res.read().decode("utf-8"))
            if res.status // 100 == 2 and response_data.get('status') == 'aprovado':
                if ambiente == 1:
                    self.marcar_como_emitido(cupom_number)
            else:
                QMessageBox.warning(self, 'Erro na Emissão', response_data.get('error'))
                print("Resposta de erro:", response_data)
        except Exception as e:
            QMessageBox.warning(self, 'Erro', f"Ocorreu um erro durante a emissão da nota fiscal. Erro: {e}")
        finally:
            http_conn.close()
            conn.close()

            
    def marcar_como_emitido(self, cupom_number):
        caminho_banco = self.obterCaminhoBancoDados()
        conn = sqlite3.connect(caminho_banco)
        cursor = conn.cursor()
        update_query = "UPDATE vendas SET nfe_emitida = 1 WHERE cupom = ?"
        cursor.execute(update_query, (cupom_number,))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = EmissaoDiversasLogic()
    window.show()
    sys.exit(app.exec_())
