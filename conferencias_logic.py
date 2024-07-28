from conferencias_ui import Ui_Dialog
import os
import sys
import sqlite3
import mysql.connector
import dbf
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QDialog, QTableWidgetItem, QFileDialog, QMessageBox, QCheckBox
from PyQt5 import QtCore, QtWidgets



class ConferenciasApp(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pushButton.clicked.connect(self.gerar_dbf)
        self.pushButton_4.clicked.connect(self.selecionar_pasta_dbf)
        self.carregar_caminho_dbf()
        self.buscar_conferencias()  # Adicionado para buscar e exibir conferências ao iniciar
        self.pushButton_6.clicked.connect(self.selecionar_todos)

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
            self.lineEdit_3.setText(dir_path)
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
            self.lineEdit_3.setText(result[0])
        conn.close()

    def buscar_conferencias(self):
        conn = self.get_mysql_connection()
        cursor = conn.cursor()
        query = """
        SELECT razao, DATE_FORMAT(data, '%d/%m/%Y'), total, senha
        FROM conferencia
        WHERE fechado = 1
        GROUP BY loja, razao, data, total, fechado, senha
        ORDER BY data DESC, loja ASC
        LIMIT 10
        """
        cursor.execute(query)
        results = cursor.fetchall()

        self.tableWidget.setRowCount(len(results))
        self.tableWidget.setColumnCount(5)  # Agora são 5 colunas, incluindo os checkboxes
        self.tableWidget.setHorizontalHeaderLabels(['', 'Loja', 'Data', 'Total', 'Senha'])
        self.tableWidget.setColumnWidth(0, 30)
        self.tableWidget.setColumnWidth(1, 120)
        self.tableWidget.setColumnWidth(2, 70)
        self.tableWidget.setColumnWidth(3, 70)
        self.tableWidget.setColumnWidth(4, 70)

        for i, row in enumerate(results):
            # Adicionar um QCheckBox na primeira coluna
            chkBox = QCheckBox()
            self.tableWidget.setCellWidget(i, 0, chkBox)

            # Preencher o restante das colunas
            for j, col in enumerate(row, 1):  # começa de 1 para ajustar os índices
                item = QtWidgets.QTableWidgetItem(str(col))
                if j == 3:  # Índice 3 refere-se à coluna Total
                    item.setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                self.tableWidget.setItem(i, j, item)

    def selecionar_todos(self):
        for ix in range(self.tableWidget.rowCount()):
            chkBox = self.tableWidget.cellWidget(ix, 0)
            if chkBox:  # Verifica se realmente existe um QCheckBox
                chkBox.setChecked(True)

    def gerar_dbf(self):
        selected_conferences = []
        for ix in range(self.tableWidget.rowCount()):
            chkBox = self.tableWidget.cellWidget(ix, 0)
            if chkBox and chkBox.isChecked():
                # Coletando dados da 'Loja' e 'Data' para identificar cada conferência
                loja = self.tableWidget.item(ix, 1).text()  # Razao da loja
                data_str = self.tableWidget.item(ix, 2).text()  # Data da conferência
                selected_conferences.append((loja, data_str))

        if not selected_conferences:
            QtWidgets.QMessageBox.warning(self, 'Aviso', 'Nenhuma conferência selecionada.')
            return

        dir_path = self.lineEdit_3.text().strip()
        if not dir_path:
            QtWidgets.QMessageBox.warning(self, 'Aviso', 'Nenhum diretório selecionado para salvar o arquivo DBF.')
            return
        nome_arquivo_dbf = os.path.join(dir_path, "CONFERS.dbf")

        try:
            # Definindo a estrutura da tabela DBF conforme a estrutura da tabela 'conferencia'
            table = dbf.Table(nome_arquivo_dbf,
                              'COD_LOJA N(2, 0); LOJA C(255); DATA D; CODIGO N(10, 0); PRODUTO C(255); UNIDADE C(255); '
                              'ESPERADO N(10, 0); ENCONTRADO N(10, 0); PRECO N(12, 2); '
                              'SUBTOTAL N(12, 2); TOTAL N(12, 2); FECHADO N(1, 0); SENHA N(10, 0)',
                              codepage='cp850')
            table.open(mode=dbf.READ_WRITE)

            conn = self.get_mysql_connection()
            cursor = conn.cursor()

            for loja, data_str in selected_conferences:
                # Converter data de DD/MM/YYYY para YYYY-MM-DD para a consulta
                data = datetime.strptime(data_str, '%d/%m/%Y').strftime('%Y-%m-%d')
                query = "SELECT * FROM conferencia WHERE razao = %s AND data = STR_TO_DATE(%s, '%Y-%m-%d')"
                cursor.execute(query, (loja, data))
                conferencias_detalhes = cursor.fetchall()

                for detalhe in conferencias_detalhes:
                    # Adiciona cada linha de detalhes da conferência no arquivo DBF
                    table.append(detalhe)

            table.close()
            cursor.close()
            conn.close()
            QtWidgets.QMessageBox.information(self, 'Sucesso', 'DBF de conferências criado com sucesso.')
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Erro', f'Erro ao criar a tabela DBF: {e}')

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWin = ConferenciasApp()
    mainWin.show()
    sys.exit(app.exec_())
