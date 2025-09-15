import csv
from datetime import datetime
from ofxparse import OfxParser
import pandas as pd
import xml.etree.ElementTree as ET
import fitz
from PIL import Image
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

class Converter:
    # --- FUNÇÃO AUXILIAR ROBUSTA PARA LER OFX ---
    def _parse_ofx_robust(self, input_path):
        """
        Função auxiliar para ler um arquivo OFX de forma robusta,
        lidando com erros de encoding comuns em bancos.
        """
        try:
            # TENTATIVA 1: Modo padrão (binário). O ofxparse deve ler o header.
            with open(input_path, 'rb') as f:
                return OfxParser.parse(f)
        except (UnicodeDecodeError, LookupError, ET.ParseError) as e:
            # TENTATIVA 2: Falha. O banco pode estar mentindo no encoding (ex: diz US-ASCII mas usa LATIN-1).
            # Vamos forçar a decodificação com latin-1, que é permissivo.
            try:
                with open(input_path, 'rb') as f:
                    raw_data = f.read()
                
                # 'latin-1' (ISO-8859-1) não falha, 'replace' troca bytes ruins por '?'
                decoded_string = raw_data.decode('latin-1', errors='replace')
                
                # Passa a string decodificada para o parser
                string_io = io.StringIO(decoded_string)
                return OfxParser.parse(string_io)
            except Exception as e_fallback:
                # Se falhar mesmo assim, o arquivo está muito corrompido.
                raise ValueError(f"Falha ao processar OFX. Tentativa padrão falhou ({e}) e fallback também falhou ({e_fallback}).")

    def ofx_to_csv(self, input_path):
        # USA A FUNÇÃO ROBUSTA
        ofx = self._parse_ofx_robust(input_path)
        
        account = ofx.account
        statement = account.statement
        transactions = [{'data': t.date.strftime('%Y-%m-%d'), 'descricao': t.memo, 'valor': t.amount, 'id': t.id} for t in statement.transactions]
        df = pd.DataFrame(transactions)
        return df.to_csv(index=False, sep=';', decimal=',')

    def csv_to_ofx(self, input_path):
        # Tenta ler com UTF-8, se falhar, tenta com Latin-1
        try:
            df = pd.read_csv(input_path, sep=';', decimal=',', encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(input_path, sep=';', decimal=',', encoding='latin-1')
        
        if not all(col in df.columns for col in ['data', 'descricao', 'valor']):
            raise ValueError("Erro: O CSV precisa ter as colunas 'data', 'descricao' e 'valor'.")

        # --- VALIDAÇÃO DE 'VALOR' ---
        # 1. Limpa a coluna 'valor' de caracteres não numéricos (R$, espaços, ".")
        df['valor'] = df['valor'].astype(str).str.replace(r'[R$\s.]', '', regex=True)
        # 2. Converte para numérico, tratando vírgula como decimal.
        df['valor'] = pd.to_numeric(df['valor'].str.replace(',', '.'), errors='coerce')
        # 3. Verifica se alguma linha falhou na conversão
        if df['valor'].isnull().any():
            raise ValueError("Erro: A coluna 'valor' contém dados não numéricos que não puderam ser convertidos.")

        # --- VALIDAÇÃO DE 'DATA' ---
        # Tenta converter a data. 'dayfirst=True' trata 'dd/mm/YYYY'.
        df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
        if df['data'].isnull().any():
            raise ValueError("Erro: A coluna 'data' contém formatos de data inválidos que não puderam ser lidos.")

        # ... (Restante da lógica do CSV para OFX) ...
        ofx_content = "OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nSECURITY:NONE\nENCODING:USASCII\nCHARSET:1252\nCOMPRESSION:NONE\nOLDFILEUID:NONE\nNEWFILEUID:NONE\n\n<OFX>\n  <SIGNONMSGSRSV1>\n    <SONRS>\n      <STATUS>\n        <CODE>0</CODE>\n        <SEVERITY>INFO</SEVERITY>\n      </STATUS>\n      <DTSERVER>{date_now}</DTSERVER>\n      <LANGUAGE>POR</LANGUAGE>\n    </SONRS>\n  </SIGNONMSGSRSV1>\n  <BANKMSGSRSV1>\n    <STMTTRNRS>\n      <TRNUID>1</TRNUID>\n      <STATUS>\n        <CODE>0</CODE>\n        <SEVERITY>INFO</SEVERITY>\n      </STATUS>\n      <STMTRS>\n        <CURDEF>BRL</CURDEF>\n        <BANKACCTFROM>\n          <BANKID>000</BANKID>\n          <ACCTID>00000-0</ACCTID>\n          <ACCTTYPE>CHECKING</ACCTTYPE>\n        </BANKACCTFROM>\n        <BANKTRANLIST>\n          <DTSTART>{start_date}</DTSTART>\n          <DTEND>{end_date}</DTEND>\n          {transactions}\n        </BANKTRANLIST>\n      </STMTRS>\n    </STMTTRNRS>\n  </BANKMSGSRSV1>\n</OFX>"
        transaction_template = "\n          <STMTTRN>\n            <TRNTYPE>{trntype}</TRNTYPE>\n            <DTPOSTED>{dtposted}</DTPOSTED>\n            <TRNAMT>{trnamt}</TRNAMT>\n            <FITID>{fitid}</FITID>\n            <MEMO>{memo}</MEMO>\n          </STMTTRN>"
        transactions_str = ""
        
        for index, row in df.iterrows():
            trans_type = "CREDIT" if row['valor'] >= 0 else "DEBIT"
            transactions_str += transaction_template.format(trntype=trans_type, dtposted=row['data'].strftime('%Y%m%d%H%M%S'), trnamt=f"{row['valor']:.2f}", fitid=f"{row['data'].strftime('%Y%m%d')}{index}", memo=row['descricao'])
        
        start_date, end_date = df['data'].min().strftime('%Y%m%d%H%M%S'), df['data'].max().strftime('%Y%m%d%H%M%S')
        return ofx_content.format(date_now=datetime.now().strftime('%Y%m%d%H%M%S'), start_date=start_date, end_date=end_date, transactions=transactions_str)

    def pdf_to_jpg(self, input_path):
        doc = fitz.open(input_path)
        images_bytes = [page.get_pixmap().tobytes("jpeg") for page in doc]
        if not images_bytes: raise ValueError("Não foi possível extrair imagens do PDF.")
        return images_bytes

    def jpg_to_pdf(self, input_path):
        try:
            image = Image.open(input_path)
        except Exception:
            raise ValueError(f"O arquivo '{input_path.split('/')[-1]}' não é um formato de imagem válido (JPG, PNG, etc.).")
        
        if image.mode == 'RGBA': image = image.convert('RGB')
        pdf_bytes = io.BytesIO()
        image.save(pdf_bytes, "PDF", resolution=100.0)
        return pdf_bytes.getvalue()

    # --- NOVAS FUNÇÕES IMPLEMENTADAS ---

    def _create_pdf_from_dataframe(self, df, title):
        """Função auxiliar para criar um PDF a partir de um DataFrame do Pandas."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        elements = []
        elements.append(Paragraph(title, styles['h1']))
        
        data = [df.columns.to_list()] + df.values.tolist()
        
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        
        table = Table(data)
        table.setStyle(style)
        
        elements.append(table)
        doc.build(elements)
        
        return buffer.getvalue()

    def ofx_to_pdf(self, input_path):
        """NOVO: Converte um arquivo OFX para um relatório em PDF."""
        # USA A FUNÇÃO ROBUSTA
        ofx = self._parse_ofx_robust(input_path)
        
        transactions = [{'Data': t.date.strftime('%d/%m/%Y'), 'Descrição': t.memo, 'Valor': f"{t.amount:.2f}"} for t in ofx.account.statement.transactions]
        df = pd.DataFrame(transactions)
        
        return self._create_pdf_from_dataframe(df, "Extrato OFX")

    def csv_to_pdf(self, input_path):
        """NOVO: Converte um arquivo CSV para um relatório em PDF."""
        try:
            df = pd.read_csv(input_path, sep=';', decimal=',', encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(input_path, sep=';', decimal=',', encoding='latin-1')
        
        return self._create_pdf_from_dataframe(df, "Relatório CSV")

    def ofx_to_xml(self, input_path):
        """NOVO: Converte um arquivo OFX para um XML simples."""
        # USA A FUNÇÃO ROBUSTA
        ofx = self._parse_ofx_robust(input_path)
        
        root = ET.Element("ExtratoOFX")
        account = ofx.account
        
        for t in account.statement.transactions:
            transacao = ET.SubElement(root, "Transacao")
            ET.SubElement(transacao, "Data").text = t.date.strftime('%Y-%m-%d')
            ET.SubElement(transacao, "Descricao").text = t.memo
            ET.SubElement(transacao, "Valor").text = str(t.amount)
            ET.SubElement(transacao, "ID").text = t.id
            
        tree = ET.ElementTree(root)
        xml_bytes = io.BytesIO()
        tree.write(xml_bytes, encoding='utf-8', xml_declaration=True)
        return xml_bytes.getvalue().decode('utf-8')

    # --- Funções que permanecem não implementadas (por complexidade) ---
    def xml_to_ofx(self, input_path):
        raise NotImplementedError("Função XML para OFX não implementada (XML pode ter formatos variados).")
        
    def xml_to_csv(self, input_path):
        raise NotImplementedError("Função XML para CSV não implementada (XML pode ter formatos variados).")
        
    def csv_to_xml(self, input_path):
        raise NotImplementedError("Função CSV para XML não implementada (Estrutura de destino do XML não definida).")