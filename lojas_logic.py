from PyQt5 import QtWidgets, QtGui, QtCore
import mysql.connector
from lojas_ui import Ui_Dialog
import sys
from brutils import cnpj
import re 
import locale

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

class StoreLogic(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self):
        super(StoreLogic, self).__init__()
        self.setupUi(self)

        # Conectar sinais e slots
        self.pushButton_4.clicked.connect(self.salvar_loja)
        self.pushButton_2.clicked.connect(self.deletar_loja)
        self.pushButton_5.clicked.connect(self.cadastrar_loja)
        self.lineEdit_10.installEventFilter(self)
        self.lineEdit_11.installEventFilter(self)


        # Inicializa o tableWidget e busca o próximo código disponível
        self.iniciar_tabela_lojas()
        proximo_codigo = self.buscar_proximo_codigo_loja()
        self.label_10.setText(str(proximo_codigo))
        self.lineEdit_10.setAlignment(QtCore.Qt.AlignRight)
        self.lineEdit_11.setAlignment(QtCore.Qt.AlignRight)

        #Colocar o cursos no CNPJ_line quando o programa abrir
        self.CNPJ_line.setFocus()

    def eventFilter(self, object, event):
        if object == self.lineEdit_10 and event.type() == QtCore.QEvent.FocusOut:
            self.formatar_valor()  # Chama a função de formatação quando o lineEdit perde o foco
            return False  # Retorna False para permitir que o evento continue sendo processado
        elif object == self.lineEdit_11 and event.type() == QtCore.QEvent.FocusOut:
                self.formatar_telefone()  # Chama a função de formatação quando o lineEdit perde o foco
                return False  # Retorna False para permitir que o evento continue sendo processado
        return super(StoreLogic, self).eventFilter(object, event)

    
    def formatar_valor(self):
        texto = self.lineEdit_10.text()
        texto_limpo = re.sub(r'[^\d,]', '', texto)  # Remove tudo exceto dígitos e vírgula
        try:
            numero = locale.atof(texto_limpo)
            texto_formatado = locale.currency(numero, grouping=True, symbol=None)
            self.lineEdit_10.setText(texto_formatado)
        except ValueError:
            pass  # Em caso de valor inválido, não faz nada

    def formatar_telefone(self):
        texto = self.lineEdit_11.text()
        texto_limpo = re.sub(r'\D', '', texto)
        if len(texto_limpo) == 11:
            texto_formatado = f"({texto_limpo[:2]}) {texto_limpo[2:7]}-{texto_limpo[7:]}"
        elif len(texto_limpo) == 10:
            texto_formatado = f"({texto_limpo[:2]}) {texto_limpo[2:6]}-{texto_limpo[6:]}"
        else:
            texto_formatado = "Número inválido"
        self.lineEdit_11.setText(texto_formatado)
        
    def buscar_proximo_codigo_loja(self):
        conexao = mysql.connector.connect(
            host='34.151.192.214',
            user='arthuraml',
            password='Ij{p=6$Y2Wits7bAo',
            database='bbcia'
        )
        cursor = conexao.cursor()
        cursor.execute("SELECT loja_cod FROM lojas ORDER BY loja_cod ASC")
        codigos = sorted([int(row[0]) for row in cursor])
        cursor.close()
        conexao.close()

        # Encontrando o primeiro "gap" na sequência de códigos, começando de 0
        for i in range(len(codigos)):
            if codigos[i] != i:  # Verifica se o código atual não corresponde ao índice
                return i
        return len(codigos)  # Se não houver "gap", retorna o próximo código após o último

    def iniciar_tabela_lojas(self):
        conexao = mysql.connector.connect(
            host='34.151.192.214',
            user='arthuraml',
            password='Ij{p=6$Y2Wits7bAo',
            database='bbcia'
        )

        cursor = conexao.cursor()
        cursor.execute("SELECT loja_cod, loja, empresa, cnpj, consumer_key, consumer_secret, access_token, access_token_secret, capint, total_nfe_mensal, telefone FROM lojas ORDER BY loja ASC")
        
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(11)  # Define o número de colunas
        self.tableWidget.setHorizontalHeaderLabels(['Cód.', 'Loja', 'Empresa', 'CNPJ', 'Consumer Key', 'Consumer Secret', 'Token', 'Token Secret', 'Capital?', 'Limite NFe', 'Telefone'])

        for row_number, row_data in enumerate(cursor):
            self.tableWidget.insertRow(row_number)
            for column_number, data in enumerate(row_data):
                if column_number == 8:  # Transforma 1 e 0 em 'Sim' e 'Não'
                    data = "Sim" if data == 1 else "Não"
                elif column_number == 10:
                    if data:  # Formata o telefone
                        telefone = data
                        if len(telefone) == 11:
                            telefone = f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}"
                        elif len(telefone) == 10:
                            telefone = f"({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}"
                        data = telefone
                    else:
                        data = "Não informado"
                elif column_number == 9:  # Formata o valor monetário
                    try:
                        valor_formatado = locale.currency(data, grouping=True, symbol=None)
                        data = valor_formatado
                    except ValueError:
                        pass  # Em caso de valor inválido, não faz nada
                item = QtWidgets.QTableWidgetItem(str(data))
                self.tableWidget.setItem(row_number, column_number, item)

        # Definindo as larguras das colunas de forma proporcional ou fixa
        # Por exemplo:
        self.tableWidget.setColumnWidth(0, 20)
        self.tableWidget.setColumnWidth(1, 120)
        self.tableWidget.setColumnWidth(2, 100)
        self.tableWidget.setColumnWidth(3, 100)
        self.tableWidget.setColumnWidth(4, 100)
        self.tableWidget.setColumnWidth(5, 100)
        self.tableWidget.setColumnWidth(6, 100)
        self.tableWidget.setColumnWidth(7, 100)
        self.tableWidget.setColumnWidth(8, 60)
        self.tableWidget.setColumnWidth(9, 80)
        self.tableWidget.setColumnWidth(10, 120)
        # Repita para as outras colunas conforme necessário

        cursor.close()
        conexao.close()


    def salvar_loja(self):
        conexao = mysql.connector.connect(
            host='34.151.192.214',
            user='arthuraml',
            password='Ij{p=6$Y2Wits7bAo',
            database='bbcia'
        )
        cursor = conexao.cursor()
        num_rows = self.tableWidget.rowCount()

        for row in range(num_rows):
            loja_cod = self.tableWidget.item(row, 0).text()
            loja = self.tableWidget.item(row, 1).text()
            empresa = self.tableWidget.item(row, 2).text()
            cnpj = self.tableWidget.item(row, 3).text()
            consumer_key = self.tableWidget.item(row, 4).text()
            consumer_secret = self.tableWidget.item(row, 5).text()
            access_token = self.tableWidget.item(row, 6).text()
            access_token_secret = self.tableWidget.item(row, 7).text()
            capint = 1 if self.tableWidget.item(row, 8).text() == 'Sim' else 0
            
            # Aqui ocorre a conversão correta para o formato esperado pelo MySQL
            total_nfe_mensal_text = self.tableWidget.item(row, 9).text()
            total_nfe_mensal_text = total_nfe_mensal_text.replace('.', '').replace(',', '.')
            try:
                total_nfe_mensal = float(total_nfe_mensal_text)
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "Valor Inválido", f"Valor inválido para total_nfe_mensal na linha {row + 1}")
                continue

            telefone = self.tableWidget.item(row, 10).text()
            telefone = re.sub(r'\D', '', telefone)  # Remove tudo que não é dígito
            if len(telefone) == 11:
                telefone = f"({telefone[:2]}) {telefone[2:7]}-{telefone[7:]}"
            elif len(telefone) == 10:
                telefone = f"({telefone[:2]}) {telefone[2:6]}-{telefone[6:]}"
            
            query = "SELECT COUNT(*) FROM lojas WHERE (loja = %s OR cnpj = %s) AND loja_cod != %s"
            cursor.execute(query, (loja, cnpj, loja_cod))
            if cursor.fetchone()[0] > 0:
                QtWidgets.QMessageBox.warning(self, "Cadastro Existente", f"Não é possível atualizar a loja {loja} para um CNPJ ou nome já existente em outro cadastro.")
                continue

            query = """
            UPDATE lojas SET 
                loja = %s,
                empresa = %s,
                cnpj = %s,
                consumer_key = %s,
                consumer_secret = %s,
                access_token = %s,
                access_token_secret = %s,
                capint = %s,
                total_nfe_mensal = %s,
                telefone = %s
            WHERE loja_cod = %s
            """
            cursor.execute(query, (loja, empresa, cnpj, consumer_key, consumer_secret, access_token, access_token_secret, capint, total_nfe_mensal, telefone, loja_cod))

        conexao.commit()
        cursor.close()
        conexao.close()
        QtWidgets.QMessageBox.information(self, "Atualização de Cadastro", "Cadastro de Lojas atualizado com sucesso!")
        proximo_codigo = self.buscar_proximo_codigo_loja()
        self.label_10.setText(str(proximo_codigo))
        self.iniciar_tabela_lojas()

    def deletar_loja(self):
        selected_items = self.tableWidget.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(self, "Seleção", "Selecione uma loja para excluir.")
            return

        selected_row = self.tableWidget.currentRow()
        loja_cod = self.tableWidget.item(selected_row, 0).text()
        loja_nome = self.tableWidget.item(selected_row, 1).text()

        reply = QtWidgets.QMessageBox.question(self, "Confirmar Exclusão", f"Tem certeza que deseja excluir o cadastro da loja {loja_nome}?",
                                            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            conexao = mysql.connector.connect(
                host='34.151.192.214',
                user='arthuraml',
                password='Ij{p=6$Y2Wits7bAo',
                database='bbcia'
            )
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM lojas WHERE loja_cod = %s", (loja_cod,))
            conexao.commit()
            cursor.close()
            conexao.close()

            self.tableWidget.removeRow(selected_row)
            QtWidgets.QMessageBox.information(self, "Exclusão de Cadastro", f"Cadastro da loja {loja_nome} excluído com sucesso!")
            proximo_codigo = self.buscar_proximo_codigo_loja()
            self.label_10.setText(str(proximo_codigo))

    def cadastrar_loja(self):
        # Coleta os dados dos inputs
        loja = self.lineEdit_4.text()
        loja_cod = self.label_10.text()
        empresa = self.lineEdit_5.text()
        cnpj_input = self.CNPJ_line.text()
        total_nfe_mensal = self.lineEdit_10.text()
        consumer_key = self.lineEdit_6.text()
        consumer_secret = self.lineEdit_8.text()
        access_token = self.lineEdit_9.text()
        access_token_secret = self.lineEdit_7.text()
        telefone = self.lineEdit_11.text()

        # Remove caracteres de formatação do CNPJ (pontos, barra e traço)
        cnpj_input = re.sub(r'\D', '', cnpj_input)  # Remove tudo que não é dígito

        # Remove caracteres não numéricos do total_nfe_mensal, exceto a vírgula
        total_nfe_mensal = re.sub(r'[^\d,]', '', total_nfe_mensal)
        # Converte o total_nfe_mensal para float, substituindo vírgula por ponto
        try:
            if total_nfe_mensal:
                total_nfe_mensal = float(total_nfe_mensal.replace(',', '.'))
            else:
                total_nfe_mensal = 0.0
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Valor Inválido", "Por favor, insira um valor válido para o total mensal de NF-e.")
            return

        # Verifica se todos os campos estão preenchidos
        if not all([loja, empresa, cnpj_input, consumer_key, consumer_secret, access_token, access_token_secret]):
            QtWidgets.QMessageBox.warning(self, "Dados Incompletos", "Por favor, preencha todos os dados para efetuar o cadastro")
            return

        # Validação do CNPJ
        if not cnpj.validate(cnpj_input):
            QtWidgets.QMessageBox.warning(self, "CNPJ Inválido", "O CNPJ fornecido não é válido. Por favor, verifique.")
            return

        # Verifica a seleção do radioButton
        if self.radioButton.isChecked():
            capint = 1
        elif self.radioButton_2.isChecked():
            capint = 0
        else:
            QtWidgets.QMessageBox.warning(self, "Seleção Obrigatória", "Seleciona se a loja é da capital ou interior")
            return

        # Abre a conexão com o banco de dados
        conexao = mysql.connector.connect(
            host='34.151.192.214',
            user='arthuraml',
            password='Ij{p=6$Y2Wits7bAo',
            database='bbcia'
        )
        cursor = conexao.cursor()

        # Verificação de duplicatas
        query = "SELECT COUNT(*) FROM lojas WHERE loja_cod = %s OR loja = %s OR cnpj = %s"
        cursor.execute(query, (loja_cod, loja, cnpj_input))
        if cursor.fetchone()[0] > 0:
            QtWidgets.QMessageBox.warning(self, "Cadastro Existente", "Cadastro já existente. Não é possível duplicar")
            conexao.close()
            return

        # Monta e executa a consulta SQL para inserir os dados
        query = """
        INSERT INTO lojas (loja_cod, loja, empresa, cnpj, consumer_key, consumer_secret, access_token, access_token_secret, capint, total_nfe_mensal, telefone) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (loja_cod, loja, empresa, cnpj_input, consumer_key, consumer_secret, access_token, access_token_secret, capint, total_nfe_mensal, telefone))

        # Efetiva as mudanças no banco de dados
        conexao.commit()
        cursor.close()
        conexao.close()

        # Limpa os campos de entrada após o cadastro
        self.lineEdit_4.clear()
        self.lineEdit_5.clear()
        self.CNPJ_line.clear()
        self.lineEdit_10.clear()
        self.lineEdit_6.clear()
        self.lineEdit_8.clear()
        self.lineEdit_9.clear()
        self.lineEdit_7.clear()
        self.lineEdit_11.clear()

        # Atualiza a tabela e o label com o próximo código de loja
        self.iniciar_tabela_lojas()
        proximo_codigo = self.buscar_proximo_codigo_loja()
        self.label_10.setText(str(proximo_codigo))

        # Exibe uma mensagem de sucesso ao usuário
        QtWidgets.QMessageBox.information(self, "Cadastro de Loja", f"Nova loja {loja} cadastrada com sucesso!")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    dialog = StoreLogic()
    dialog.show()
    sys.exit(app.exec_())