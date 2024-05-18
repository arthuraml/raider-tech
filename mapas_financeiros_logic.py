import dbf
from PyQt5 import QtWidgets, QtCore, QtGui
import mysql.connector
from mapas_financeiros_ui import Ui_Dialog
from datetime import datetime
import pytz
import os
import sqlite3

class MapasFinanceirosLogic(QtWidgets.QDialog):
    def __init__(self):
        super(MapasFinanceirosLogic, self).__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.tableWidget.setColumnCount(5)
        self.ui.tableWidget.setHorizontalHeaderLabels(['', 'Cód. Loja', 'Loja', 'Fechamento', 'Venda Líquida'])
        self.ui.tableWidget.setColumnWidth(0, 30)
        self.ui.tableWidget.setColumnWidth(1, 70)
        self.ui.tableWidget.setColumnWidth(2, 100)
        self.ui.tableWidget.setColumnWidth(3, 150)
        self.ui.tableWidget.setColumnWidth(4, 90)
        self.ui.pushButton.clicked.connect(self.gerar_dbf_mapas_financeiros)
        self.ui.pushButton_2.clicked.connect(self.gerar_dbf_vendas)
        self.ui.pushButton_3.clicked.connect(self.limpar_campos)  # Adiciona o evento de clique ao pushButton_3
        self.ui.lineEdit.returnPressed.connect(self.buscar_mapas_financeiros)
        data_atual = datetime.now().strftime("%d/%m/%Y")
        self.ui.lineEdit.setText(data_atual)
        self.ui.lineEdit.setFocus()
        self.ui.pushButton_4.clicked.connect(self.selecionar_pasta_dbf)
        self.carregar_caminho_dbf()
        self.ui.pushButton_5.clicked.connect(self.selecionar_todos)
        #Colocar o lineEdit_3 como igual ao valor do valorTotal

    def selecionar_todos(self):
        for ix in range(self.ui.tableWidget.rowCount()):
            self.ui.tableWidget.cellWidget(ix, 0).setChecked(True)

    def get_mysql_connection(self):
        return mysql.connector.connect(
            host='34.151.192.214',
            user='arthuraml',
            password='Ij{p=6$Y2Wits7bAo',
            database='bbcia'
        )
    
    def get_sqlite_connection(self):
        return sqlite3.connect('bd/retaguarda.db')

    def selecionar_pasta_dbf(self):
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Selecione a Pasta")
        if dir_path:
            self.ui.lineEdit_3.setText(dir_path)
            self.salvar_caminho_dbf(dir_path)

    def salvar_caminho_dbf(self, dir_path):
        conn = self.get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS config (local_dbfs TEXT)")
        cursor.execute("DELETE FROM config")
        cursor.execute("INSERT INTO config (local_dbfs) VALUES (?)", (dir_path,))
        conn.commit()
        conn.close()

    def carregar_caminho_dbf(self):
        conn = self.get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS config (local_dbfs TEXT)")
        cursor.execute("SELECT local_dbfs FROM config LIMIT 1")
        result = cursor.fetchone()
        if result:
            self.ui.lineEdit_3.setText(result[0])
        conn.close()

    def buscar_mapas_financeiros(self):
        data_str = self.ui.lineEdit.text()
        formato_data = "%d/%m/%Y"
        fuso_horario = pytz.timezone('America/Sao_Paulo')
        soma_vendas = 0.0  # Inicializa a soma das vendas líquidas

        try:
            data_datetime = datetime.strptime(data_str, formato_data)
            data_datetime = fuso_horario.localize(data_datetime)
            data_inicio_dia = int(data_datetime.timestamp() * 1000)

            mysql_conn = self.get_mysql_connection()
            cursor = mysql_conn.cursor()
            query_mapas = """
            SELECT loja_cod, fechamento_timestamp, venda_liquida
            FROM mapas_financeiros
            WHERE (abertura_timestamp < %s AND fechamento_timestamp > %s)
            """
            cursor.execute(query_mapas, (data_inicio_dia, data_inicio_dia))
            results = cursor.fetchall()

            if not results:
                QtWidgets.QMessageBox.information(self, 'Informação', 'Nenhum mapa encontrado para essa data')
                return

            self.ui.tableWidget.setRowCount(len(results))
            for ix, (loja_cod, fechamento_timestamp, venda_liquida) in enumerate(results):
                cursor.execute("SELECT loja FROM lojas WHERE loja_cod = %s", (loja_cod,))
                loja_nome = cursor.fetchone()

                self.ui.tableWidget.setItem(ix, 1, QtWidgets.QTableWidgetItem(str(loja_cod)))
                self.ui.tableWidget.setItem(ix, 2, QtWidgets.QTableWidgetItem(loja_nome[0] if loja_nome else 'Desconhecida'))
                
                if fechamento_timestamp:
                    fechamento_str = datetime.fromtimestamp(fechamento_timestamp / 1000, tz=fuso_horario).strftime('%d/%m/%Y %H:%M:%S')
                    self.ui.tableWidget.setItem(ix, 3, QtWidgets.QTableWidgetItem(fechamento_str))
                else:
                    self.ui.tableWidget.setItem(ix, 3, QtWidgets.QTableWidgetItem('Em aberto'))

                venda_liquida_item = QtWidgets.QTableWidgetItem(str(venda_liquida))
                venda_liquida_item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                self.ui.tableWidget.setItem(ix, 4, venda_liquida_item)
                checkbox = QtWidgets.QCheckBox()
                self.ui.tableWidget.setCellWidget(ix, 0, checkbox)
                
                soma_vendas += float(venda_liquida)

            # Atualiza o lineEdit_2 com a soma das vendas líquidas, formatada adequadamente e alinhada à direita
            self.ui.lineEdit_2.setText("{:.2f}".format(soma_vendas))
            self.ui.lineEdit_2.setAlignment(QtCore.Qt.AlignRight)

            mysql_conn.close()
        except ValueError:
            print("Data inválida.")


    def gerar_dbf_mapas_financeiros(self):
        if not any(self.ui.tableWidget.cellWidget(ix, 0).isChecked() for ix in range(self.ui.tableWidget.rowCount())):
            QtWidgets.QMessageBox.warning(self, 'Aviso', 'Seleção em branco.')
            return

        data_str = self.ui.lineEdit.text()
        data_formatada = data_str.split('/')
        dir_path = self.ui.lineEdit_3.text().strip()
        if not dir_path:
            QtWidgets.QMessageBox.warning(self, 'Aviso', 'Nenhum diretório selecionado para salvar o arquivo DBF.')
            return
        nome_arquivo_dbf = os.path.join(dir_path, f"MPF{data_formatada[0]}{data_formatada[1]}.dbf")
        try:
            # Definindo a estrutura da tabela DBF
            table = dbf.Table(nome_arquivo_dbf,
                'LOJA_COD N(2, 0); ABERTURA C(10); FECHAMENTO C(10); '
                'SALDO_ANT N(12, 2); VEND_BRUT N(12, 2); CANCELAD N(12, 2); '
                'DIF_ATACAD N(12, 2); DIF_VENDEX N(12, 2); VEND_LIQ N(12, 2); '
                'DESPESAS N(12, 2); DEPOSITOS N(12, 2); REMESSAS N(12, 2); '
                'SALD_CAIXA N(12, 2); CHEQUES N(12, 2); PROMISS N(12, 2); '
                'DINHEIRO N(12, 2); OBS C(255); DESP_PROL N(12, 2); '
                'DESP_PRO_O C(255); DESP_IMPOS N(12, 2); DESP_IMP_O C(255); '
                'DESP_PASS N(12, 2); DESP_PAS_O C(255); DESP_MOTO N(12, 2); '
                'DESP_MOT_O C(255); DESP_ALUG N(12, 2); DESP_ALU_O C(255); '
                'DESP_AGUA N(12, 2); DESP_AGU_O C(255); DESP_LUZ N(12, 2); '
                'DESP_LUZ_O C(255); DESP_TEL N(12, 2); DESP_TEL_O C(255); '
                'DESP_DESC N(12, 2); DESP_DES_O C(255); DESP_GERA N(12, 2); '
                'DESP_GER_O C(255); DEP_BB N(12, 2); DEP_BB_O C(255); '
                'DEP_BARC N(12, 2); DEP_BARC_O C(255); DEP_BRADE N(12, 2); '
                'DEP_BRAD_O C(255); DEP_CAIXA N(12, 2); DEP_CAIX_O C(255); '
                'DEP_NORD N(12, 2); DEP_NORD_O C(255); REM_DINH N(12, 2); '
                'REM_DINH_O C(255); REM_CHEQ N(12, 2); REM_CHEQ_O C(255); '
                'REM_PIXCJ N(12, 2); REM_PXCJ_O C(255); REM_PIXQR N(12, 2); REM_DEBC N(12, 2); '
                'REM_CRED N(12, 2); REM_BOLETO N(12, 2); REM_BLT_O C(255); SALVO N(1, 0); FECHADO N(1, 0); OBS_G C(255); TOTAL_ATAC N(12, 2); ',
                codepage='cp850')
            table.open(mode=dbf.READ_WRITE)

            # Conexão com MySQL para obter os dados
            mysql_conn = self.get_mysql_connection()
            cursor = mysql_conn.cursor()

            # Verificando e processando cada linha da tabela do widget
            for ix in range(self.ui.tableWidget.rowCount()):
                checkbox = self.ui.tableWidget.cellWidget(ix, 0)
                if checkbox.isChecked():
                    loja_cod = int(self.ui.tableWidget.item(ix, 1).text())
                    fechamento_str = self.ui.tableWidget.item(ix, 3).text()
                    fuso_horario = pytz.timezone('America/Sao_Paulo')
                    fechamento_dt = datetime.strptime(fechamento_str, '%d/%m/%Y %H:%M:%S')

                    cursor.execute("SELECT * FROM mapas_financeiros WHERE loja_cod = %s AND fechamento_timestamp = %s", (loja_cod, fechamento_dt.timestamp() * 1000))
                    mapa = cursor.fetchone()
                    if mapa:
                        # Ajustando o formato da data na inserção
                        mapa = list(mapa)
                        mapa[1] = datetime.fromtimestamp(mapa[1] / 1000, tz=fuso_horario).strftime('%d/%m/%Y')  # ABERTURA
                        mapa[2] = datetime.fromtimestamp(mapa[2] / 1000, tz=fuso_horario).strftime('%d/%m/%Y')  # FECHAMENTO
                        table.append(tuple(mapa))

            table.close()
            mysql_conn.close()
            QtWidgets.QMessageBox.information(self, 'Sucesso', 'DBF criado com sucesso.')

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Erro', f'Erro ao criar a tabela DBF: {e}')

    def gerar_dbf_vendas(self):
        if not any(self.ui.tableWidget.cellWidget(ix, 0).isChecked() for ix in range(self.ui.tableWidget.rowCount())):
            QtWidgets.QMessageBox.warning(self, 'Aviso', 'Seleção em branco.')
            return
        
        data_str = self.ui.lineEdit.text()
        data_formatada = data_str.split('/')
        data_milissegundos = int(datetime.strptime(data_str, '%d/%m/%Y').timestamp() * 1000)
        dir_path = self.ui.lineEdit_3.text().strip()
        if not dir_path:
            QtWidgets.QMessageBox.warning(self, 'Aviso', 'Nenhum diretório selecionado para salvar o arquivo DBF.')
            return
        nome_arquivo_dbf = os.path.join(dir_path, f"VND{data_formatada[0]}{data_formatada[1]}.dbf")
        try:
            table = dbf.Table(nome_arquivo_dbf,
                            'LOJA_COD N(4, 0); DATA C(255); CUPOM N(10, 0); NM_PROD C(255); REF N(10, 0); '
                            'PRC_PROD N(12, 2); QTD N(10, 2); ESTORNAD L; EST_TIMESP N(20, 0); '
                            'CANCELAD N(1, 0); CANCELTIME N(20, 0); SUBTOTAL N(12, 2); TOTAL_ATAC N(12, 2); '
                            'TOTAL_VAR N(12, 2); PRECO_APL C(255); PONTA L; PROMO L; COD_VEND N(6, 0); '
                            'NOME_VEND C(255); LOJA C(255); TERMINAL N(6, 0); PAGAMENT L; '
                            'FORMA_PAGT C(255); PARCELAS N(3, 0); CHEQUE L; CLIENT_NOM C(255); '
                            'CLIENT_CPF C(255); EXTERNA N(1, 0); EXT_DIF N(12, 2); PRECO_ATAC N(12, 2); '
                            'PAG_DIN N(12, 2); PAG_CCRED N(12, 2); PAG_CDEB N(12, 2); PAG_PIXQR N(12, 2); PAG_PIXCJ N(12, 2); '
                            'PAG_CHEQUE N(12, 2); PAG_BOLETO N(12, 2); ENV N(1, 0); NFE N(1, 0); NFE_C C(255); DATA_DBF C(10); ',
                            codepage='cp850')
            table.open(mode=dbf.READ_WRITE)

            mysql_conn = self.get_mysql_connection()
            cursor = mysql_conn.cursor()

            for ix in range(self.ui.tableWidget.rowCount()):
                checkbox = self.ui.tableWidget.cellWidget(ix, 0)
                if checkbox.isChecked():
                    loja_cod = int(self.ui.tableWidget.item(ix, 1).text())
                    cursor.execute("""SELECT abertura_timestamp, fechamento_timestamp 
                                        FROM mapas_financeiros 
                                        WHERE loja_cod = %s 
                                        AND abertura_timestamp < %s AND fechamento_timestamp > %s
                                    """, (loja_cod, data_milissegundos, data_milissegundos))
                    timestamps = cursor.fetchall()

                    for abertura_timestamp, fechamento_timestamp in timestamps:
                        query_vendas = """
                        SELECT loja_cod, data_formatada, cupom, nome_do_produto, referencia, 
                        preco_produto, quantidade, estornado, estorno_timestamp, cancelado, 
                        cancelamento_timestamp, subtotal_produto, preco_atacado, preco_varejo, 
                        preco_aplicado, ponta, promo, cod_vendedor, nome_vendedor, loja, terminal, 
                        pagamento, forma_pagamento, parcelas, cheque, cliente_nome, cliente_cpf, 
                        externa, externa_dif, preco_produto_atacado, pag_dinheiro, pag_ccredito, pag_cdebito, pag_pix_qr, pag_pix_cnpj, pag_cheque, pag_boleto, enviado, nfe_emitida, nfe_chave
                        FROM vendas 
                        WHERE loja_cod = %s AND pagamento_timestamp BETWEEN %s AND %s
                        """
                        cursor.execute(query_vendas, (loja_cod, abertura_timestamp, fechamento_timestamp))
                        vendas = cursor.fetchall()

                        for venda in vendas:
                            venda = list(venda)
                            venda.append(data_str)  # Adiciona a data do lineEdit ao final de cada registro
                            table.append(tuple(venda))

            table.close()
            mysql_conn.close()
            QtWidgets.QMessageBox.information(self, 'Sucesso', 'DBF de vendas criado com sucesso.')

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Erro', f'Erro ao criar a tabela DBF: {e}')


        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Erro', f'Erro ao criar a tabela DBF: {e}')


    def limpar_campos(self):
        self.ui.lineEdit.clear()
        self.ui.lineEdit_2.clear()
        self.ui.tableWidget.setRowCount(0)

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = MapasFinanceirosLogic()
    window.show()
    sys.exit(app.exec_())