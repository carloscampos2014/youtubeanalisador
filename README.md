# 🌊 Analisador de Palavras para Canais do YouTube  

Este é um aplicativo desenvolvido em **Python** utilizando **Streamlit**, que permite analisar as palavras mais utilizadas nos vídeos de um canal do YouTube.  

⚠️ **IMPORTANTE:** Este projeto foi **gerado integralmente por IA generativa**, com apenas pequenas interferências humanas para ajustes e validação.  

---

## 🚀 Funcionalidades  

✅ Extrai **transcrições de vídeos** do YouTube.  
✅ Analisa as palavras mais frequentes (excluindo stopwords).  
✅ Exibe estatísticas detalhadas dos vídeos (visualizações, likes, etc.).  
✅ Permite exportar os resultados em **PDF**.  
✅ Interface intuitiva feita com **Streamlit**.  

---

## 🛠️ Tecnologias Utilizadas  

- **Python** 🐍  
- **Streamlit** (para a interface)  
- **Google YouTube API** (para obter dados dos canais)  
- **YouTube Transcript API** (para extrair transcrições)  
- **NLTK** (para processamento de texto)  
- **Pandas** (para manipulação de dados)  
- **ReportLab** (para geração de PDFs)  

---

## 🧩 Pré-requisitos  

Antes de começar, certifique-se de ter o seguinte instalado:  

- Python 3.7 ou superior

---

## 📂 Estrutura do Projeto  

```plaintext
analisador-youtube/
├── app.py
├── requirements.txt
├── README.md
└── .env.example

---

## 📺 Instalação  

1️⃣ Clone este repositório:  

```bash
git clone https://github.com/seu-usuario/analisador-youtube.git
cd analisador-youtube
```

2️⃣ Instale as dependências:  

```bash
pip install -r requirements.txt
```

3️⃣ Configure a **chave da API do YouTube** criando um arquivo `.env` com o seguinte conteúdo:  

```bash
YOUTUBE_API_KEY=SUA_CHAVE_AQUI
```

4️⃣ Execute o projeto:  

```bash
streamlit run app.py
```

---

## 🎥 Interface  

O aplicativo apresenta uma interface simples, com **botões** para facilitar a interação:  

- **Visualizar** → Exibe a análise na tela.  
- **Exportar PDF** → Exporta os resultados para um arquivo PDF e permite baixar o resultado atraves de um botão **Baixar PD**

---

## 🎬 Exemplo de Uso  

1. Abra o aplicativo Streamlit.
2. Insira a URL do canal do YouTube.
3. Clique em "Visualizar" para exibir a análise na tela.
4. Clique em "Exportar PDF" para baixar os resultados em formato PDF.

---

## 🤖 Origem do Código  

Este código foi **totalmente gerado por inteligência artificial**, com **pequenas revisões humanas** para ajustes técnicos e estilização. Isso demonstra o potencial da IA na **automação do desenvolvimento de software**.  

---

## 📝 Licença  

Este projeto é de código aberto. Sinta-se à vontade para modificar e melhorar!  

📌 *Dúvidas ou sugestões? Entre em contato!*
