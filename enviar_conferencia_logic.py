from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from enviar_conferencia_ui import Ui_Dialog
import geopandas as gpd
import mysql.connector
from mysql.connector import Error

class ConferenciaLogic(QtWidgets.QDialog, Ui_Dialog):
    def __init__(self, parent=None):
        super(ConferenciaLogic, self).__init__(parent)
        self.setupUi(self)
        self.pushButton.clicked.connect(self.analisar_arquivo)
        self.pushButton_2.clicked.connect(self.enviar_conferencia)
        self.file_path = None  # Adiciona um atributo para armazenar o caminho do arquivo

    def analisar_arquivo(self):
        self.file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo DBF", "", "DBF Files (*.dbf)")
        if self.file_path:
            try:
                gdf = gpd.read_file(self.file_path)
                num_produtos = len(gdf)
                nome_loja = gdf['RAZAO'].iloc[0] if 'RAZAO' in gdf.columns else 'Desconhecido'
                self.textBrowser.setText(f"{num_produtos} produtos prontos para conferência. Loja: {nome_loja}")
            except Exception as e:
                self.textBrowser.setText(f"Erro ao ler o arquivo: {e}")

    def enviar_conferencia(self):
        senha = self.lineEdit.text()  # Lê o valor da senha do QLineEdit
        if not senha:  # Verifica se a senha não foi inserida
            QMessageBox.warning(self, "Senha Necessária", "Para enviar a conferência é necessário escolher uma senha")
            return 

        if self.file_path:
            try:
                gdf = gpd.read_file(self.file_path)
                conn = mysql.connector.connect(host='34.151.192.214', user='arthuraml', password='Ij{p=6$Y2Wits7bAo', database='bbcia')
                cursor = conn.cursor()
                
                total_rows = len(gdf)
                self.textBrowser.setText("Iniciando o envio de dados...")
                QtWidgets.QApplication.processEvents()

                last_percent_update = -1
                for i, row in enumerate(gdf.iterrows(), start=1):
                    percent_complete = int((i / total_rows) * 100)
                    try:
                        cursor.execute("INSERT INTO conferencia (loja, razao, data, codigo, produto, unidade, estoque_esperado, preco, senha) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                                    (row[1]['LOJA'], row[1]['RAZAO'], row[1]['DATA'], row[1]['CODIGO'], row[1]['NOME'], row[1]['UNID'], row[1]['ESTOQ'], row[1]['PRECO'], senha))
                    except mysql.connector.Error as err:
                        if err.errno == 1062:
                            self.textBrowser.append("Conferência já enviada")
                            QtWidgets.QApplication.processEvents()
                            break
                        else:
                            raise
                    if percent_complete >= last_percent_update + 5:
                        self.textBrowser.append(f"Enviando dados... {percent_complete}% completo")
                        QtWidgets.QApplication.processEvents()
                        last_percent_update = percent_complete

                conn.commit()
                self.textBrowser.append("Conferência enviada com sucesso")
            except Exception as e:
                self.textBrowser.append(f"Erro ao enviar a conferência: {e}")
            finally:
                if conn.is_connected():
                    cursor.close()
                    conn.close()
        else:
            self.textBrowser.setText("Por favor, selecione um arquivo antes de tentar enviar.")

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = ConferenciaLogic()
    window.show()
    sys.exit(app.exec_())
