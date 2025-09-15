from datetime import datetime
import customtkinter
from tkinter import filedialog
from converter import Converter
import os
import io
from PIL import Image, ImageTk
import fitz  # PyMuPDF
import threading
import requests
import webbrowser
import json

# --- Configurações de Atualização ---
VERSAO_ATUAL = "1.5.1" 
# SUBSTITUA PELA URL REAL DO SEU GIST "RAW"
URL_VERSAO = "https://gist.githubusercontent.com/MuriloAEFV/e8f38e34d14ec3224c4706c84ea60ac8/raw/291fb05b21be15a5b297c9abff2fd4d3b8f16b17/gistfile1.txt"

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")


# --- Janela de Visualização ---
class PreviewWindow(customtkinter.CTkToplevel):
    def __init__(self, parent, data, file_format):
        super().__init__(parent)
        self.parent = parent
        self.data = data
        self.file_format = file_format
        
        self.title(f"Visualização - {file_format.upper()}")
        self.geometry("800x600")
        self.grab_set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.button_frame = customtkinter.CTkFrame(self)
        self.button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.download_button = customtkinter.CTkButton(self.button_frame, text="Fazer Download", command=self.download)
        self.download_button.pack(side="right", padx=5)
        
        self.close_button = customtkinter.CTkButton(self.button_frame, text="Fechar", command=self.destroy)
        self.close_button.pack(side="right", padx=5)

        self.display_content()

    def display_content(self):
        if self.file_format in ['csv', 'xml', 'ofx']:
            # --- PREVENÇÃO DE TRAVAMENTO POR ARQUIVO GRANDE ---
            # Limite de 5MB para preview de texto
            MAX_PREVIEW_SIZE = 5 * 1024 * 1024 
            
            if isinstance(self.data, str) and len(self.data) > MAX_PREVIEW_SIZE:
                # Cria um frame centralizado para o aviso
                center_frame = customtkinter.CTkFrame(self)
                center_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
                center_frame.grid_rowconfigure(0, weight=1)
                center_frame.grid_columnconfigure(0, weight=1)
                
                label = customtkinter.CTkLabel(center_frame, text=f"Arquivo muito grande para visualização ({len(self.data) / (1024*1024):.1f} MB).\n\nUse o botão 'Fazer Download'.", text_color="orange", font=("", 14))
                label.grid(row=0, column=0, sticky="nsew")
            else:
                textbox = customtkinter.CTkTextbox(self)
                textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
                textbox.insert("0.0", self.data)
                textbox.configure(state="disabled")

        elif self.file_format == 'jpg':
            try:
                # --- LÓGICA MELHORADA PARA MÚLTIPLAS PÁGINAS ---
                scrollable_frame = customtkinter.CTkScrollableFrame(self)
                scrollable_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
                
                # Verifica se 'data' é uma lista (de pdf_to_jpg) ou um único item
                image_list = self.data if isinstance(self.data, list) else [self.data]

                for image_bytes in image_list:
                    pil_image = Image.open(io.BytesIO(image_bytes))
                    ctk_image = customtkinter.CTkImage(light_image=pil_image, dark_image=pil_image, size=pil_image.size)
                    
                    image_label = customtkinter.CTkLabel(scrollable_frame, image=ctk_image, text="")
                    image_label.pack(pady=10, padx=10, expand=True)

            except Exception as e:
                self.parent.log(f"Erro ao exibir imagem: {e}")

        elif self.file_format == 'pdf':
            try:
                pdf_doc = fitz.open(stream=self.data, filetype="pdf")
                scrollable_frame = customtkinter.CTkScrollableFrame(self)
                scrollable_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
                
                for page_num in range(len(pdf_doc)):
                    page = pdf_doc.load_page(page_num)
                    pix = page.get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    
                    ctk_image = customtkinter.CTkImage(light_image=img, dark_image=img, size=img.size)
                    page_label = customtkinter.CTkLabel(scrollable_frame, image=ctk_image, text="")
                    page_label.pack(pady=10, padx=10)
                
                pdf_doc.close()
            except Exception as e:
                self.parent.log(f"Erro ao renderizar preview do PDF: {e}")

    def download(self):
        self.parent.save_converted_file(self.data, self.file_format)
        self.destroy()


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Conversor de Arquivos v{VERSAO_ATUAL}")
        self.geometry("700x550")
        self.converter = Converter()
        self.input_file_path = ""
        self.converted_data = None
        self.to_format = ""

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.file_frame = customtkinter.CTkFrame(self)
        self.file_frame.grid(row=0, column=0, padx=20, pady=20, sticky="ew")
        self.file_frame.grid_columnconfigure(1, weight=1)
        self.select_button = customtkinter.CTkButton(self.file_frame, text="Selecionar Arquivo de Origem", command=self.select_file)
        self.select_button.grid(row=0, column=0, padx=10, pady=10)
        self.input_file_label = customtkinter.CTkLabel(self.file_frame, text="Nenhum arquivo selecionado", anchor="w")
        self.input_file_label.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        self.options_frame = customtkinter.CTkFrame(self)
        self.options_frame.grid(row=1, column=0, padx=20, pady=0, sticky="ew")
        self.options_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)
        self.from_label = customtkinter.CTkLabel(self.options_frame, text="Converter De:")
        self.from_label.grid(row=0, column=0, padx=10, pady=10)
        self.from_optionmenu = customtkinter.CTkOptionMenu(self.options_frame, values=["OFX", "CSV", "PDF", "JPG", "XML"])
        self.from_optionmenu.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
        self.from_optionmenu.set("OFX")
        self.to_label = customtkinter.CTkLabel(self.options_frame, text="Para:")
        self.to_label.grid(row=0, column=2, padx=10, pady=10)
        self.to_optionmenu = customtkinter.CTkOptionMenu(self.options_frame, values=["CSV", "PDF", "XML", "OFX", "JPG"])
        self.to_optionmenu.grid(row=0, column=3, padx=10, pady=10, sticky="ew")
        self.to_optionmenu.set("CSV")

        self.log_textbox = customtkinter.CTkTextbox(self, state="disabled")
        self.log_textbox.grid(row=2, column=0, padx=20, pady=20, sticky="nsew")
        
        self.convert_button = customtkinter.CTkButton(self, text="Converter e Visualizar", command=self.run_conversion, height=40)
        self.convert_button.grid(row=3, column=0, padx=20, pady=(10, 20), sticky="ew")

        self.log("Bem-vindo! Selecione um arquivo para começar.")
        self.check_for_updates()

    def select_file(self):
        from_format = self.from_optionmenu.get().lower()
        filetypes = {'ofx': [("Extrato OFX", "*.ofx")],'csv': [("Arquivo CSV", "*.csv")],'pdf': [("Arquivo PDF", "*.pdf")],'jpg': [("Imagem JPG", "*.jpg;*.jpeg")],'xml': [("Arquivo XML", "*.xml")],}
        current_filetypes = filetypes.get(from_format, [])
        current_filetypes.append(("Todos os arquivos", "*.*"))
        self.input_file_path = filedialog.askopenfilename(filetypes=current_filetypes)
        if self.input_file_path:
            self.input_file_label.configure(text=os.path.basename(self.input_file_path))
            self.log(f"Arquivo selecionado: {self.input_file_path}")
        else:
            self.input_file_label.configure(text="Nenhum arquivo selecionado")

    def run_conversion(self):
        if not self.input_file_path:
            self.log("Erro: Por favor, selecione um arquivo de origem primeiro.")
            return

        from_format = self.from_optionmenu.get().lower()
        self.to_format = self.to_optionmenu.get().lower()

        self.log(f"Processando conversão de {from_format.upper()} para {self.to_format.upper()}...")
        self.update()

        try:
            conversion_function_name = f"{from_format}_to_{self.to_format}"
            if not hasattr(self.converter, conversion_function_name):
                raise NotImplementedError(f"A conversão de {from_format.upper()} para {self.to_format.upper()} não é suportada.")
            
            conversion_function = getattr(self.converter, conversion_function_name)
            self.converted_data = conversion_function(self.input_file_path)
            
            self.log("Conversão concluída. Abrindo visualização...")
            PreviewWindow(self, self.converted_data, self.to_format)

        except (Exception, NotImplementedError) as e:
            self.log(f"Erro na conversão: {e}")

    def save_converted_file(self, data, to_format):
        output_path = filedialog.asksaveasfilename(defaultextension=f".{to_format}", filetypes=[(f"{to_format.upper()} files", f"*.{to_format}"), ("All files", "*.*")])
        if not output_path:
            self.log("Salvamento cancelado pelo usuário."); return

        try:
            if isinstance(data, list):
                base_dir, base_name = os.path.dirname(output_path), os.path.splitext(os.path.basename(output_path))[0]
                if to_format == 'jpg':
                     # Se o formato de saída for JPG, salva apenas a primeira imagem no local exato
                     with open(output_path, 'wb') as f: f.write(data[0])
                     self.log(f"Sucesso! Imagem salva em: {output_path}")
                     # Se houver mais imagens, avisa o usuário (embora o preview agora mostre todas)
                     if len(data) > 1:
                         self.log(f"Aviso: O PDF original tinha {len(data)} páginas. Apenas a primeira foi salva como '{os.path.basename(output_path)}'.")
                         self.log(f"Para salvar todas, escolha um nome base (ex: 'pagina') e o app salvará 'pagina_1.jpg', 'pagina_2.jpg'...")
                else:
                    # Este caso 'else' é improvável para 'list', mas mantido por segurança
                    for i, img_bytes in enumerate(data):
                        page_path = os.path.join(base_dir, f"{base_name}_pagina_{i+1}.jpg")
                        with open(page_path, 'wb') as f: f.write(img_bytes)
                    self.log(f"Sucesso! {len(data)} páginas salvas na pasta: {base_dir}")
            
            elif isinstance(data, str):
                with open(output_path, 'w', encoding='utf-8') as f: f.write(data)
                self.log(f"Sucesso! Arquivo salvo em: {output_path}")
            
            elif isinstance(data, bytes):
                with open(output_path, 'wb') as f: f.write(data)
                self.log(f"Sucesso! Arquivo salvo em: {output_path}")
        
        except Exception as e:
            self.log(f"Erro ao salvar o arquivo: {e}")

    def log(self, message):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n\n")
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    # --- Funções do Sistema de Atualização ---
    def check_for_updates(self):
        update_thread = threading.Thread(target=self._update_checker_thread, daemon=True)
        update_thread.start()

    def _update_checker_thread(self):
        try:
            response = requests.get(URL_VERSAO, timeout=5)
            response.raise_for_status()
            data = response.json()
            latest_version = data.get("version")
            download_url = data.get("url")

            if latest_version and download_url and latest_version > VERSAO_ATUAL:
                self.log(f"Nova versão encontrada: {latest_version}")
                self.after(0, self.show_update_dialog, latest_version, download_url)

        except requests.exceptions.RequestException as e:
            # Erro acontece silenciosamente, sem poluir o log da UI.
            print(f"Falha ao verificar atualização (silencioso): {e}")
            pass
        except json.JSONDecodeError:
            # Erro acontece silenciosamente, sem poluir o log da UI.
            print("Falha ao ler JSON da versão (silencioso)")
            pass

    def show_update_dialog(self, new_version, download_url):
        dialog = customtkinter.CTkToplevel(self)
        dialog.title("Atualização Disponível")
        dialog.geometry("400x150")
        dialog.grab_set()
        dialog.resizable(False, False)

        dialog.grid_columnconfigure(0, weight=1)

        label = customtkinter.CTkLabel(dialog, text=f"Uma nova versão ({new_version}) está disponível!", font=("", 16))
        label.grid(row=0, column=0, padx=20, pady=20)

        update_button = customtkinter.CTkButton(dialog, text="Atualizar Agora", command=lambda: self.start_update(download_url))
        update_button.grid(row=1, column=0, padx=20, pady=10)

    def start_update(self, url):
        self.log(f"Abrindo link de download: {url}")
        webbrowser.open(url)

if __name__ == "__main__":
    app = App()
    app.mainloop()