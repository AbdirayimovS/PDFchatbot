# BISMILLAH
import random
import sys
import time
import os
import shutil
import threading


from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QProgressDialog
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QDir


from chatbotCore import ChatBotCompositor
from ingest import main as do_ingesting

class Worker(QObject):
    finished = pyqtSignal()  # Signal to indicate the task completion

    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs

    def run(self):
        self.function(*self.args, **self.kwargs)  # Call the passed function
        self.finished.emit()  # Emit the finished signal




class InputWidget:
    def __init__(self, widget, chatWidget, parent=None):
        self.chatDisplay = chatWidget.findChild(QtWidgets.QTextEdit, "chatDisplay")
        self.displayChatbotMessage = None # it will initialized in the main class
        self.chatbot = None
        self.parent = parent
        self.messageInput = widget.findChild(QtWidgets.QLineEdit, "messageInput") #TODO
        self.sendButton = widget.findChild(QtWidgets.QPushButton, "sendButton")
        self.attatchFileLabel = widget.findChild(QtWidgets.QPushButton, "attatchFileLabel")

        self.sendButton.clicked.connect(self.sendMessage)
        self.attatchFileLabel.clicked.connect(self.attatchFile)

        self.workerSetup()

    @staticmethod
    def checkFileFormats(mimeData):
        allowedExtensions = [
            '.csv', '.docx', '.doc', '.enex', '.eml', '.epub', '.html', 
            '.md', '.msg', '.odt', '.pdf', '.pptx', '.ppt', '.txt'
        ]
        for url in mimeData.urls():
            if any(url.toLocalFile().lower().endswith(ext) for ext in allowedExtensions):
                return True
        return False

    def processFile(self, file_path):
        # Here you can add the logic to process the file
        # For demonstration, just display the file path in the chat
        self.saveFile(file_path)
        self.runDoIngesting()
    
    def saveFile(self, file_path):
        save_location = "source_documents/"
        filename = os.path.basename(file_path)

        destination_path = os.path.join(save_location, filename)
        try:
            shutil.copy(file_path, destination_path)
        except Exception as e:
            print(f"Error saving file: {e}")

    def attatchFile(self):
        # Define the file filter
        fileFilter = "CSV (*.csv);;" \
                    "Word Document (*.docx *.doc);;" \
                    "EverNote (*.enex);;" \
                    "Email (*.eml);;" \
                    "EPub (*.epub);;" \
                    "HTML File (*.html);;" \
                    "Markdown (*.md);;" \
                    "Outlook Message (*.msg);;" \
                    "Open Document Text (*.odt);;" \
                    "Portable Document Format (PDF) (*.pdf);;" \
                    "PowerPoint Document (*.pptx *.ppt);;" \
                    "Text file (UTF-8) (*.txt)"
        
        # Open a file dialog and print the selected file path
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self.parent, "Load File", "", fileFilter, options=options)
        if fileName:
            self.processFile(fileName)

    def sendMessage(self):
        message = self.messageInput.text().strip()
        if message:
            self.chatDisplay.append(f"[{time.time()}]You: {message}\n")
            self.messageInput.clear()
            answer, docs = self.chatbot(message)
            docs = []
            chatbot_response = f"[{time.time()}]Bot: {answer}\n{self.formatDocs(docs)}"
            self.displayChatbotMessage(chatbot_response)

    def formatDocs(self, docs):
        output_text = ""
        for document in docs:
            output_text += "\n> " + document.metadata["source"] + ":"
            output_text += document.page_content
        return output_text
    
    def showProgressDialog(self):
        self.progressDialog = QProgressDialog("Creating new vectorstore\nMay take some time", "Cancel", 0, 0, self.parent)
        self.progressDialog.setWindowModality(Qt.WindowModal)
        self.progressDialog.setMinimumDuration(0)  # Show immediately
        self.progressDialog.setCancelButton(None)  # Remove the cancel button
        self.progressDialog.setRange(0, 0)  # Indeterminate mode
        self.progressDialog.show()

    def workerSetup(self):
        self.worker = Worker(do_ingesting)  # Assuming do_ingesting takes no arguments
        self.worker.finished.connect(self.completeDoIngesting)
    
    def completeDoIngesting(self):
        self.progressDialog.cancel()
        self.parent.settings_widget.listFilesInDirectory()

    def runDoIngesting(self):
        self.showProgressDialog()
        self.thread = threading.Thread(target=self.worker.run)
        self.thread.start()


class DialogWidget:
    def __init__(self, widget):
        self.init_typing()
        self.chatDisplay = widget.findChild(QtWidgets.QTextEdit, "chatDisplay")

    def init_typing(self):
        self.current_message = ""
        self.message_index = 0
        self.typing_timer = QTimer()
        self.typing_timer.timeout.connect(self.simulateTyping)

    @property
    def typing_speed_ms(self):
        x = random.randint(80, 120)
        return x
    
    def simulateTyping(self):
        if self.message_index < len(self.current_message):
            next_char = self.current_message[self.message_index] + " "
            styled_char = self.applyRandomStyle(next_char)
            self.chatDisplay.moveCursor(QTextCursor.End)
            self.chatDisplay.insertHtml(styled_char)
            self.message_index += 1
            if self.message_index == 1:  # Start the timer on the first character
                self.typing_timer.start(self.typing_speed_ms)
        else:
            self.typing_timer.stop()
            self.message_index = 0
            self.chatDisplay.append("")

    def applyRandomStyle(self, char):
        # Define font weights and background colors
        weights = ['normal', 'bold', 'lighter']
        colors = ['#F0F8FF', '#FAEBD7', '#F5F5DC', '#F5FFFA']  # Light, readable background colors
        weight = random.choice(weights)
        bg_color = random.choice(colors)
        styled_char = f"<span style='font-weight:{weight}; background-color:{bg_color};'>{char}</span>"
        return styled_char
    
    def displayChatbotMessage(self, message):
        self.current_message = message.split()
        self.message_index = 0
        self.typing_timer.start(self.typing_speed_ms)


class SettingsWidget:
    def __init__(self, widget):
        self.folderListView = widget.findChild(QtWidgets.QListView, "listView")
        self.modelComboBox = widget.findChild(QtWidgets.QComboBox, "comboBox")
        self.initModels()

    def listFilesInDirectory(self, directory="source_documents"):
        # List all files in the specified directory
        self.file_system_model = QtWidgets.QFileSystemModel()
        folderPath = QDir.current().absoluteFilePath("source_documents")
        self.file_system_model.setRootPath(folderPath)
        self.folderListView.setModel(self.file_system_model)
        self.folderListView.setRootIndex(self.file_system_model.index(folderPath))

    def initModels(self):
        self.models = {"llama2:latest": ChatBotCompositor(model_name="llama2:latest"),
                       "llama2-uncensored:latest": ChatBotCompositor(model_name="llama2-uncensored:latest"),
                       "pdfLlama": ChatBotCompositor(model_name="pdfLlama")}
        self.currentModel = next(iter(self.models.values()))

        for modelName in self.models.keys():
            self.modelComboBox.addItem(modelName)

        self.modelComboBox.activated[str].connect(self.modelSelected)

    def modelSelected(self, text):
        self.currentModel = self.models[text]
        print("Current model is ", self.currentModel)
    


class ChatBotInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        # Load the UI
        self.initUI()
        self.initWidgets()
    
    def initWidgets(self):
        self.settings_widget = SettingsWidget(self.findChild(QtWidgets.QWidget, "settingsPage1"))
        self.input_widget = InputWidget(self.findChild(QtWidgets.QWidget, "InputWidget"),
                                        self.findChild(QtWidgets.QWidget, "chatWidget"), 
                                        self)
        self.dialog_widget = DialogWidget(self.findChild(QtWidgets.QWidget, "chatWidget"))
        self.settings_widget.listFilesInDirectory()

        self.input_widget.displayChatbotMessage = self.dialog_widget.displayChatbotMessage
        self.input_widget.chatbot = self.settings_widget.currentModel

    def initUI(self):
        uic.loadUi('UI/mainwindow.ui', self)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            self.input_widget.sendMessage()  # Programmatically "click" the button
        else:
            super().keyPressEvent(event)  # Handle other keyPress events as usual
    
    def dragEnterEvent(self, e):
        print("Dragging")
        if e.mimeData().hasUrls() and self.checkFileFormats(e.mimeData()):
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        print("DROPPING")
        for url in e.mimeData().urls():
            file_path = url.toLocalFile()
            self.input_widget.processFile(file_path)
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ChatBotInterface()
    window.show()
    sys.exit(app.exec_())
