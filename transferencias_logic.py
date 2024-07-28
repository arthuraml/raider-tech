from transferencias_ui import Ui_Dialog
from PyQt5 import QtWidgets
from datetime import datetime
import pytz
import os
import sqlite3
import dbf
from PyQt5 import QtWidgets, QtCore, QtGui
import mysql.connector

class TransferenciasApp(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        # Conectar sinais e slots
        self.pushButton.clicked.connect(self.gerar_dbf)
        self.pushButton_3.clicked.connect(self.limpar)
        self.pushButton_4.clicked.connect(self.selecionar_pasta_dbf)
        self.carregar_caminho_dbf()
        self.lineEdit.returnPressed.connect(self.buscar_transferencias)
        self.lineEdit.setFocus()
        self.pushButton_5.clicked.connect(self.selecionar_todos)
        data_atual = datetime.now().strftime("%d/%m/%Y")
        self.lineEdit.setText(data_atual)

    def selecionar_todos(self):
        for ix in range(self.tableWidget.rowCount()):
            self.tableWidget.cellWidget(ix, 0).setChecked(True)

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

    def buscar_transferencias(self):
        data_str = self.lineEdit.text()
        conn = self.get_mysql_connection()
        cursor = conn.cursor()

        query = """
        SELECT codigo_transferencia, data, loja_origem_nome, loja_destino_nome, total
        FROM transferencias
        WHERE data = STR_TO_DATE(%s, '%d/%m/%Y')
        GROUP BY codigo_transferencia, data, loja_origem_nome, loja_destino_nome, total;
        """
        
        cursor.execute(query, (data_str,))
        transferencias = cursor.fetchall()

        self.tableWidget.setColumnCount(6)  # Ajuste para contar a coluna de checkBox e código
        self.tableWidget.setHorizontalHeaderLabels(["", "Código", "Data", "Origem", "Destino", "Valor"])
        self.tableWidget.setColumnWidth(0, 30)
        self.tableWidget.setColumnWidth(1, 50)
        self.tableWidget.setColumnWidth(2, 70)
        self.tableWidget.setColumnWidth(3, 130)
        self.tableWidget.setColumnWidth(4, 130)
        self.tableWidget.setColumnWidth(5, 70)

        self.tableWidget.setRowCount(0)
        for row_number, transferencia in enumerate(transferencias):
            self.tableWidget.insertRow(row_number)
            checkbox = QtWidgets.QCheckBox()
            self.tableWidget.setCellWidget(row_number, 0, checkbox)

            for column_number, data in enumerate(transferencia, start=1):
                if column_number == 2:  # Coluna de data para ajustar formatação
                    data = data.strftime('%d/%m/%Y')
                self.tableWidget.setItem(row_number, column_number, QtWidgets.QTableWidgetItem(str(data)))

        cursor.close()
        conn.close()

    def gerar_dbf(self):
        if not any(self.tableWidget.cellWidget(ix, 0).isChecked() for ix in range(self.tableWidget.rowCount())):
            QtWidgets.QMessageBox.warning(self, 'Aviso', 'Seleção em branco.')
            return

        data_str = self.lineEdit.text()
        dir_path = self.lineEdit_3.text().strip()
        if not dir_path:
            QtWidgets.QMessageBox.warning(self, 'Aviso', 'Nenhum diretório selecionado para salvar o arquivo DBF.')
            return

        # Modificação aqui
        data_obj = datetime.strptime(data_str, "%d/%m/%Y")
        nome_arquivo_dbf = os.path.join(dir_path, f"TRF{data_obj.day:02d}{data_obj.month:02d}.dbf")

        try:
            # Estrutura DBF será definida com base nas colunas da tabela transferencias
            table = dbf.Table(nome_arquivo_dbf,
                              'CODIGO N(10, 0); DATA D; ORIG_COD N(2, 0); ORIG_NOME C(255); DEST_COD N(2, 0); DEST_NOME C(255); '
                              'PROD_COD N(10, 0); COD_BARRAS N(20, 0); PROD_NOME C(255); PRECO N(12, 2); QTD N(10, 2); TOTAL N(12, 2)',
                              codepage='cp850')
            table.open(mode=dbf.READ_WRITE)

            conn = self.get_mysql_connection()
            cursor = conn.cursor()

            for ix in range(self.tableWidget.rowCount()):
                checkbox = self.tableWidget.cellWidget(ix, 0)
                if checkbox.isChecked():
                    codigo_transferencia = int(self.tableWidget.item(ix, 1).text())
                    loja_origem = self.tableWidget.item(ix, 3).text()
                    query = "SELECT * FROM transferencias WHERE codigo_transferencia = %s and loja_origem_nome = %s"
                    cursor.execute(query, (codigo_transferencia, loja_origem))
                    transferencias_detalhes = cursor.fetchall()

                    for detalhe in transferencias_detalhes:
                        table.append(tuple(detalhe))

            table.close()
            cursor.close()
            conn.close()
            QtWidgets.QMessageBox.information(self, 'Sucesso', 'DBF de transferências criado com sucesso.')

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, 'Erro', f'Erro ao criar a tabela DBF: {e}')


    def limpar(self):
        self.lineEdit.clear()
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(0)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    dialog = TransferenciasApp()
    dialog.show()
    sys.exit(app.exec_())
