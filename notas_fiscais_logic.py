from PyQt5.QtWidgets import QMessageBox, QDialog
from datetime import datetime, timedelta
from notas_fiscais_ui import Ui_Dialog
from PyQt5 import QtWidgets
import mysql.connector
import pandas as pd
from PyQt5.QtCore import Qt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
import locale

# Definindo o local para formatação monetária
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Classe de lógica para Notas Fiscais
class NotasFiscaisLogic(QDialog):
    def __init__(self):
        super(NotasFiscaisLogic, self).__init__()
        self.ui = Ui_Dialog()  # Cria a interface internamente
        self.ui.setupUi(self)  # Configura a interface
        self.setup_connections()  # Conecta os sinais aos slots
        self.initialize_ui()  # Inicializa a interface com valores padrão

    def setup_connections(self):
        self.ui.pushButton.clicked.connect(self.consultar_notas)
        self.ui.pushButton_2.clicked.connect(self.confirm_generate_pdf)
        self.ui.comboBox.currentIndexChanged.connect(self.atualizar_meta_nfe)
        self.ui.comboBox.currentIndexChanged.connect(self.atualizar_total_emitido)
        self.ui.radioButton.toggled.connect(self.atualizar_estado_pushButton_2)
        self.ui.radioButton_2.toggled.connect(self.atualizar_estado_pushButton_2)
        self.ui.radioButton_3.toggled.connect(self.atualizar_estado_pushButton_2)

    def atualizar_estado_pushButton_2(self):
        if self.ui.radioButton_3.isChecked():
            self.ui.pushButton_2.setEnabled(True)
        else:
            self.ui.pushButton_2.setEnabled(False)

    def initialize_ui(self):
        self.set_default_dates()
        self.carregar_lojas()
        self.atualizar_total_emitido()  # Atualiza o total emitido para a loja selecionada
        self.ui.radioButton_3.setChecked(True)  # Define o radioButton_3 como selecionado ao iniciar o programa
        self.ui.pushButton_2.setEnabled(True)  # Deixa o botão habilitado por padrão


    def set_default_dates(self):
        current_date = datetime.now()
        first_day = current_date.replace(day=1).strftime("%d/%m/%Y")
        last_day = (current_date.replace(day=1).replace(month=current_date.month % 12 + 1) - timedelta(days=1)).strftime("%d/%m/%Y")
        self.ui.lineEdit.setText(first_day)
        self.ui.lineEdit_2.setText(last_day)

    def carregar_lojas(self):
        try:
            conn = self.get_mysql_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT loja_cod, loja FROM lojas ORDER BY loja")
            lojas = cursor.fetchall()
            self.ui.comboBox.clear()  # Limpa o comboBox antes de adicionar as lojas
            for loja_cod, nome_loja in lojas:
                self.ui.comboBox.addItem(f"{loja_cod} - {nome_loja}", loja_cod)
            self.atualizar_meta_nfe()  # Atualiza a meta ao carregar as lojas
        except mysql.connector.Error as err:
            QtWidgets.QMessageBox.warning(self, 'Erro de Banco de Dados', f'Ocorreu um erro ao acessar o banco de dados: {err}')
        finally:
            if conn.is_connected():
                conn.close()

    def get_mysql_connection(self):
        return mysql.connector.connect(
            host='34.151.192.214',
            user='arthuraml',
            password='Ij{p=6$Y2Wits7bAo',
            database='bbcia'
        )

    def consultar_notas(self):
        data_inicial = self.ui.lineEdit.text()
        data_final = self.ui.lineEdit_2.text()
        loja_selecionada = self.ui.comboBox.currentData()  # Obter o código da loja

        # Definir o filtro de modelo de NFe
        if self.ui.radioButton.isChecked():
            nfe_modelo = "nfe"
        elif self.ui.radioButton_2.isChecked():
            nfe_modelo = "nfce"
        else:
            nfe_modelo = None  # Sem filtro de modelo

        # Converter as datas para timestamps
        try:
            timestamp_inicial = int(datetime.strptime(data_inicial, "%d/%m/%Y").timestamp() * 1000)
            timestamp_final = int((datetime.strptime(data_final, "%d/%m/%Y") + timedelta(days=1) - timedelta(milliseconds=1)).timestamp() * 1000)
        except ValueError:
            QMessageBox.warning(self, "Erro", "Formato de data inválido. Use DD/MM/AAAA.")
            return

        try:
            conn = self.get_mysql_connection()
            cursor = conn.cursor()

            query = """
            SELECT 
                DATE(FROM_UNIXTIME(nfe_timestamp / 1000)) AS data_emissao,
                nfe_serie,
                MIN(cupom) AS nota_inicial,
                MAX(cupom) AS nota_final,
                SUM(subtotal_produto) AS total_dia
            FROM vendas
            WHERE loja_cod = %s AND nfe_emitida = 1 
                AND nfe_timestamp BETWEEN %s AND %s
            """

            if nfe_modelo:
                query += " AND nfe_modelo = %s"
                query += " GROUP BY data_emissao, nfe_serie"
                cursor.execute(query, (loja_selecionada, timestamp_inicial, timestamp_final, nfe_modelo))
            else:
                query += " GROUP BY data_emissao, nfe_serie"
                cursor.execute(query, (loja_selecionada, timestamp_inicial, timestamp_final))

            resultados = cursor.fetchall()

            # Transformar os resultados em um DataFrame
            df = pd.DataFrame(resultados, columns=["data_emissao", "nfe_serie", "nota_inicial", "nota_final", "total_dia"])

            self.populate_table(df)
            self.atualizar_total_emitido()  # Atualiza o total emitido sem o filtro de modelo de NFe

        except mysql.connector.Error as err:
            QMessageBox.warning(self, 'Erro de Banco de Dados', f'Ocorreu um erro ao acessar o banco de dados: {err}')
        finally:
            if conn.is_connected():
                conn.close()


    def populate_table(self, df):
        """
        Preenche o QTableWidget com os resultados das notas fiscais consultadas.
        """
        self.ui.tableWidget.setRowCount(len(df))
        self.ui.tableWidget.setColumnCount(5)  # Cinco colunas: Emissão, Série, Nota Inicial, Nota Final, Total
        self.ui.tableWidget.setHorizontalHeaderLabels(["Emissão", "Série", "Nota Inicial", "Nota Final", "Total Emitido"])

        for row in range(len(df)):
            self.ui.tableWidget.setItem(row, 0, QtWidgets.QTableWidgetItem(df.loc[row, "data_emissao"].strftime("%d/%m/%Y")))
            self.ui.tableWidget.setItem(row, 1, QtWidgets.QTableWidgetItem(df.loc[row, "nfe_serie"]))
            self.ui.tableWidget.setItem(row, 2, QtWidgets.QTableWidgetItem(str(df.loc[row, "nota_inicial"])))
            self.ui.tableWidget.setItem(row, 3, QtWidgets.QTableWidgetItem(str(df.loc[row, "nota_final"])))

            total_emitido_item = QtWidgets.QTableWidgetItem(f"R$ {df.loc[row, 'total_dia']:.2f}")
            total_emitido_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.ui.tableWidget.setItem(row, 4, total_emitido_item)

        self.ui.tableWidget.resizeColumnsToContents()

    def atualizar_meta_nfe(self):
        """
        Atualiza o campo lineEdit_6 com a meta de emissão de notas fiscais do mês.
        """
        loja_selecionada = self.ui.comboBox.currentData()
        try:
            conn = self.get_mysql_connection()
            cursor = conn.cursor()

            query = "SELECT total_nfe_mensal FROM lojas WHERE loja_cod = %s"
            cursor.execute(query, (loja_selecionada,))
            resultado = cursor.fetchone()

            if resultado:
                meta_nfe = resultado[0]
                meta_nfe_formatada = f"R$ {meta_nfe:,.2f}".replace(',', 'v').replace('.', ',').replace('v', '.')
                self.ui.lineEdit_6.setText(meta_nfe_formatada)
                self.ui.lineEdit_6.setAlignment(Qt.AlignRight)
            else:
                self.ui.lineEdit_6.setText("R$ 0,00")
                self.ui.lineEdit_6.setAlignment(Qt.AlignRight)

        except mysql.connector.Error as err:
            QtWidgets.QMessageBox.warning(self, 'Erro de Banco de Dados', f'Ocorreu um erro ao acessar o banco de dados: {err}')
        finally:
            if conn.is_connected():
                conn.close()

    def atualizar_total_emitido(self):
        """
        Atualiza o campo lineEdit_4 com a soma total das notas fiscais emitidas na loja selecionada.
        """
        loja_selecionada = self.ui.comboBox.currentData()  # Obter o código da loja
        data_inicial = self.ui.lineEdit.text()
        data_final = self.ui.lineEdit_2.text()

        # Converter as datas para timestamps
        try:
            timestamp_inicial = int(datetime.strptime(data_inicial, "%d/%m/%Y").timestamp() * 1000)
            timestamp_final = int((datetime.strptime(data_final, "%d/%m/%Y") + timedelta(days=1) - timedelta(milliseconds=1)).timestamp() * 1000)
        except ValueError:
            QMessageBox.warning(self, "Erro", "Formato de data inválido. Use DD/MM/AAAA.")
            return

        try:
            conn = self.get_mysql_connection()
            cursor = conn.cursor()

            query = """
            SELECT 
                SUM(subtotal_produto) AS total_emitido
            FROM vendas
            WHERE loja_cod = %s AND nfe_emitida = 1 
                  AND nfe_timestamp BETWEEN %s AND %s
            """
            cursor.execute(query, (loja_selecionada, timestamp_inicial, timestamp_final))
            resultado = cursor.fetchone()

            if resultado and resultado[0] is not None:
                total_emitido = resultado[0]
            else:
                total_emitido = 0.0

            total_emitido_formatado = f"R$ {total_emitido:,.2f}".replace(',', 'v').replace('.', ',').replace('v', '.')
            self.ui.lineEdit_4.setText(total_emitido_formatado)
            self.ui.lineEdit_4.setAlignment(Qt.AlignRight)

        except mysql.connector.Error as err:
            QMessageBox.warning(self, 'Erro de Banco de Dados', f'Ocorreu um erro ao acessar o banco de dados: {err}')
        finally:
            if conn.is_connected():
                conn.close()

    def confirm_generate_pdf(self):
        reply = QtWidgets.QMessageBox.question(self, 'Confirmar Geração de PDF',
                                               'Deseja gerar o PDF do relatório de notas fiscais?',
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                               QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            options = QtWidgets.QFileDialog.Options()
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Salvar Relatório", "", "PDF Files (*.pdf);;All Files (*)", options=options)
            if file_path:
                self.generate_pdf(file_path)

    def generate_pdf(self, pdf_path):
        conteudo_relatorio = self.gerar_conteudo_relatorio()
        self.create_pdf(conteudo_relatorio, pdf_path)
        QtWidgets.QMessageBox.information(self, "PDF Gerado", f"Relatório PDF gerado com sucesso em {pdf_path}")

    def gerar_conteudo_relatorio(self):
        conteudo_relatorio = []
        table = self.ui.tableWidget
        row_count = table.rowCount()
        col_count = table.columnCount()

        loja_selecionada = self.ui.comboBox.currentText()
        meta_nfe = self.ui.lineEdit_6.text()
        total_emitido = self.ui.lineEdit_4.text()

        conteudo_relatorio.append(["RELATÓRIO DE NOTAS FISCAIS"])
        conteudo_relatorio.append([f"Loja: {loja_selecionada}"])
        conteudo_relatorio.append([f"Meta de Emissão: {meta_nfe}"])
        conteudo_relatorio.append([f"Total Emitido: {total_emitido}"])
        conteudo_relatorio.append(Spacer(1, 12))  # Adicionando um espaço entre os elementos
        conteudo_relatorio.append(["Emissão", "Série", "Nota Inicial", "Nota Final", "Total Emitido"])

        for row in range(row_count):
            linha = []
            for col in range(col_count):
                item = table.item(row, col)
                text = item.text() if item else "Não informado"
                linha.append(text)
            conteudo_relatorio.append(linha)

        return conteudo_relatorio

    def create_pdf(self, data, file_path):
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        right_align_style = ParagraphStyle(name='RightAlign', parent=styles['Normal'], alignment=2)

        for line in data:
            if isinstance(line, list) and len(line) == 1 and line[0].startswith("RELATÓRIO"):
                elements.append(Spacer(1, 12))
                elements.append(Paragraph(line[0], styles['Title']))
                elements.append(Spacer(1, 12))
            elif isinstance(line, list) and len(line) == 1 and (line[0].startswith("Loja:") or line[0].startswith("Meta de Emissão:") or line[0].startswith("Total Emitido:")):
                elements.append(Paragraph(line[0], styles['Heading2']))
                elements.append(Spacer(1, 12))
            elif line == ["Emissão", "Série", "Nota Inicial", "Nota Final", "Total Emitido"]:
                table = Table([line], colWidths=[100, 60, 60, 60, 80])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(table)
            elif isinstance(line, list):
                table = Table([line], colWidths=[100, 60, 60, 60, 80])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.beige),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(table)

        doc.build(elements)

# Uso da lógica em conjunto com a interface:
if __name__ == "__main__":
    from PyQt5 import QtWidgets
    import sys

    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    logic = NotasFiscaisLogic()
    Dialog.show()
    sys.exit(app.exec_())
