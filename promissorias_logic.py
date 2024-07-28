from PyQt5 import QtCore, QtGui, QtWidgets
import mysql.connector
from promissorias_ui import Ui_Dialog
import locale
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak

# Definindo o local para formatação monetária
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

class PromissoriasApp(QtWidgets.QDialog):
    def __init__(self):
        super(PromissoriasApp, self).__init__()
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.radioButton.setChecked(True)  # RadioButton "Em caixa" selecionado por padrão
        self.setup_connections()
        self.populate_lojas()
        self.populate_promissorias()

    def setup_connections(self):
        self.ui.comboBox.activated.connect(self.populate_promissorias)
        self.ui.radioButton.toggled.connect(self.populate_promissorias)
        self.ui.radioButton_2.toggled.connect(self.populate_promissorias)
        self.ui.pushButton.clicked.connect(self.confirm_generate_pdf)  # Conecta o botão de impressão à função

    def populate_lojas(self):
        try:
            conexao = mysql.connector.connect(
                host='34.151.192.214',
                user='arthuraml',
                password='Ij{p=6$Y2Wits7bAo',
                database='bbcia'
            )

            cursor = conexao.cursor()
            query = "SELECT loja_cod, loja FROM lojas ORDER BY loja ASC"
            cursor.execute(query)

            self.ui.comboBox.addItem("Todas as lojas")

            for (loja_cod, loja) in cursor:
                item = f"{str(loja_cod).zfill(2)} - {loja}"
                self.ui.comboBox.addItem(item)

            cursor.close()
            conexao.close()
        except mysql.connector.Error as err:
            print(f"Erro ao se conectar ao MySQL: {err}")

    def populate_promissorias(self):
        selected_loja = self.ui.comboBox.currentText()
        selected_loja_cod = None
        if selected_loja != "Todas as lojas":
            selected_loja_cod = int(selected_loja.split(" - ")[0])

        show_caixa = self.ui.radioButton.isChecked()

        try:
            conexao = mysql.connector.connect(
                host='34.151.192.214',
                user='arthuraml',
                password='Ij{p=6$Y2Wits7bAo',
                database='bbcia'
            )

            cursor = conexao.cursor()

            query = "SELECT l.loja, p.cpf, p.cnpj, p.cliente, p.valor, p.vencimento, p.excluido " \
                    "FROM promissorias p " \
                    "JOIN lojas l ON p.loja_cod = l.loja_cod "

            # Ajustar a cláusula WHERE com base nos estados dos radioButtons
            conditions = []
            params = []

            if show_caixa:
                conditions.append("p.excluido = 0")
            else:
                conditions.append("p.excluido != 0")

            if selected_loja_cod:
                conditions.append("p.loja_cod = %s")
                params.append(selected_loja_cod)

            if conditions:
                query += "WHERE " + " AND ".join(conditions)

            query += " ORDER BY l.loja ASC, p.vencimento ASC"
            cursor.execute(query, params)

            self.ui.tableWidget.setRowCount(0)
            self.ui.tableWidget.setColumnCount(6)
            self.ui.tableWidget.setHorizontalHeaderLabels(["Loja", "CPF", "CNPJ", "Cliente", "Valor", "Vencimento"])

            total_value = 0
            for row_number, row_data in enumerate(cursor):
                self.ui.tableWidget.insertRow(row_number)
                for column_number, data in enumerate(row_data):
                    if data in [None, "", "null"]:
                        data = "Não informado"
                    elif column_number == 4:  # Coluna "Valor"
                        total_value += float(data) if data != "Não informado" else 0
                        data = locale.currency(float(data), grouping=True)
                    elif column_number == 5:  # Coluna "Vencimento"
                        data = QtCore.QDate.fromString(str(data), "yyyy-MM-dd").toString("dd/MM/yyyy")
                    self.ui.tableWidget.setItem(row_number, column_number, QtWidgets.QTableWidgetItem(str(data)))

            self.set_column_widths()
            self.ui.lineEdit.setText(locale.currency(total_value, grouping=True))

            cursor.close()
            conexao.close()
        except mysql.connector.Error as err:
            print(f"Erro ao se conectar ao MySQL: {err}")

    def set_column_widths(self):
        # Definindo tamanhos fixos para as colunas
        self.ui.tableWidget.setColumnWidth(0, 120)  # Loja
        self.ui.tableWidget.setColumnWidth(1, 90)  # CPF
        self.ui.tableWidget.setColumnWidth(2, 90)  # CNPJ
        self.ui.tableWidget.setColumnWidth(3, 150)  # Cliente
        self.ui.tableWidget.setColumnWidth(4, 70)  # Valor
        self.ui.tableWidget.setColumnWidth(5, 75)  # Vencimento

    def confirm_generate_pdf(self):
        reply = QtWidgets.QMessageBox.question(self, 'Confirmar Geração de PDF',
                                               'Deseja gerar o PDF do relatório de promissórias?',
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

        current_loja = None
        header = ["CPF", "CNPJ", "Cliente", "Valor", "Vencimento"]

        for row in range(row_count):
            loja_item = table.item(row, 0)
            loja = loja_item.text() if loja_item else "Não informado"

            if loja != current_loja:
                if current_loja is not None:
                    conteudo_relatorio.append([f"Total: {locale.currency(total_loja, grouping=True)}"])
                    conteudo_relatorio.append(PageBreak())
                current_loja = loja
                conteudo_relatorio.append(["RELATÓRIO DE CRÉDITOS A RECEBER"])
                conteudo_relatorio.append([f"Loja: {loja}"])
                conteudo_relatorio.append(header)
                total_loja = 0

            linha = [""] * len(header)  # Garante que a linha tenha o comprimento correto
            for col in range(1, col_count):
                item = table.item(row, col)
                text = item.text() if item else "Não informado"
                linha[col - 1] = text
                if col == 4 and text != "Não informado":
                    total_loja += float(text.replace("R$", "").replace(".", "").replace(",", "."))  # Calcula o total da loja
            conteudo_relatorio.append(linha)

        conteudo_relatorio.append([f"Total: {locale.currency(total_loja, grouping=True)}"])
        return conteudo_relatorio

    def create_pdf(self, data, file_path):
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        header = ["CPF", "CNPJ", "Cliente", "Valor", "Vencimento"]
        right_align_style = ParagraphStyle(name='RightAlign', parent=styles['Normal'], alignment=2)

        for line in data:
            if isinstance(line, list) and len(line) == 1 and line[0].startswith("RELATÓRIO"):
                elements.append(Spacer(1, 12))
                elements.append(Paragraph(line[0], styles['Title']))
                elements.append(Spacer(1, 12))
            elif isinstance(line, list) and len(line) == 1 and line[0].startswith("Loja:"):
                elements.append(Paragraph(line[0], styles['Heading2']))
                elements.append(Spacer(1, 12))
            elif isinstance(line, PageBreak):
                elements.append(line)
            elif isinstance(line, list) and "Total:" in line[0]:
                elements.append(Spacer(1, 12))
                elements.append(Paragraph(line[0], right_align_style))  # Alinhado à direita
                elements.append(Spacer(1, 12))
            elif line == header:
                table = Table([line], colWidths=[100, 100, 150, 70, 90])  # Linhas sem a coluna "Loja"
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                elements.append(table)
            else:
                table = Table([line], colWidths=[100, 100, 150, 70, 90])  # Linhas sem a coluna "Loja"
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

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    application = PromissoriasApp()
    application.show()
    sys.exit(app.exec_())
