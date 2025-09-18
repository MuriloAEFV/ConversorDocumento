Conversor de Documentos
Um aplicativo de desktop versátil e fácil de usar, desenvolvido para simplificar a conversão entre diversos formatos de documentos financeiros e de imagem. Com uma interface gráfica intuitiva, o usuário pode converter arquivos com poucos cliques, visualizar o resultado antes de salvar e receber notificações sobre novas versões.

Funcionalidades Principais
Interface Gráfica Simples: Construído com customtkinter, o aplicativo oferece uma experiência de usuário limpa e moderna.

Visualização Integrada: Antes de salvar o arquivo convertido, uma janela de pré-visualização é exibida, permitindo verificar o resultado. Para arquivos de texto grandes, o app protege o usuário contra travamentos, sugerindo o download direto.

Conversões Suportadas:

Financeiras:

OFX para CSV, PDF e XML

CSV para OFX e PDF

Imagem e Documento:

PDF para JPG (com suporte a múltiplas páginas)

JPG para PDF

Robusto Processamento de OFX: O sistema consegue lidar com arquivos OFX que possuem problemas comuns de codificação (encoding), comuns em extratos de alguns bancos.

Validação de Dados: Ao converter de CSV para OFX, o aplicativo valida as colunas essenciais (data, descricao, valor) e seus formatos, prevenindo a geração de arquivos inválidos.

Sistema de Atualização Automática: O programa verifica, de forma assíncrona, se há uma nova versão disponível e notifica o usuário, fornecendo o link para download.

Funções Não Implementadas: O código deixa claro quais conversões ainda não foram implementadas, como XML para OFX/CSV e CSV para XML, devido à complexidade e variabilidade dos formatos XML.

Tecnologias e Bibliotecas
O projeto utiliza as seguintes bibliotecas Python para realizar suas funcionalidades:

Interface Gráfica: customtkinter

Manipulação de OFX: ofxparse

Análise e Manipulação de Dados: pandas

Geração e Leitura de PDF: PyMuPDF (fitz) e reportlab

Manipulação de Imagens: Pillow (PIL)

Criação de XML: xml.etree.ElementTree (biblioteca padrão)

Requisições Web (Atualizações): requests


Empacotamento para Executável: O arquivo .spec indica o uso do PyInstaller para criar o executável do Windows. 

Estrutura do Projeto
ConversorDocumento-main/
├── main.py               # Lógica da interface gráfica (GUI) e fluxo principal
├── converter.py          # Classe com toda a lógica de conversão de arquivos
├── requirements.txt      # Lista de dependências do projeto
├── icone.ico             # Ícone utilizado no executável
├── ConversorDeArquivos.spec # Arquivo de configuração do PyInstaller
└── .gitignore            # Arquivos e pastas a serem ignorados pelo Git
Como Usar
Seleção de Arquivos:

Inicie o aplicativo.

Selecione o formato de origem no menu "Converter De:".

Clique em "Selecionar Arquivo de Origem" para escolher o documento.

Escolha do Destino:

Selecione o formato para o qual deseja converter no menu "Para:".

Conversão:

Clique em "Converter e Visualizar".

Uma nova janela mostrará o resultado.

Se estiver satisfeito, clique em "Fazer Download" na janela de visualização para salvar o novo arquivo.

Instalação (Para Desenvolvedores)
Para executar o projeto a partir do código-fonte, siga estes passos:

Clone o repositório:

Bash

git clone https://github.com/seu-usuario/ConversorDocumento-main.git
cd ConversorDocumento-main
Crie e ative um ambiente virtual (recomendado):

Bash

python -m venv venv
# No Windows
venv\Scripts\activate
# No macOS/Linux
source venv/bin/activate
Instale as dependências:

Bash

pip install -r requirements.txt
Execute o aplicativo:

Bash

python main.py
Compilação (Gerando o .exe)
O projeto está configurado para ser compilado em um único executável usando PyInstaller. Para gerar o arquivo ConversorDeArquivos.exe, instale o PyInstaller (pip install pyinstaller) e execute o seguinte comando no terminal, a partir da pasta raiz do projeto:

Bash

pyinstaller ConversorDeArquivos.spec
