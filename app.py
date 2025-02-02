import streamlit as st
import pandas as pd
import nltk
from nltk.corpus import stopwords
from collections import Counter
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import re
from dotenv import load_dotenv
import os
from datetime import datetime
import locale
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from googleapiclient.errors import HttpError
import json

# Configurações iniciais
nltk.download('stopwords')
load_dotenv()

# Configurar o locale para o Brasil
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, '')

# Constantes
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

class YouTubeAnalyzer:
    def __init__(self):
        self.stop_words = set(stopwords.words('portuguese'))

    def get_channel_info(self, channel_id):
        """Obtém informações do canal."""
        try:
            request = youtube.channels().list(part="snippet,statistics", id=channel_id)
            response = request.execute()
            if "items" in response and response["items"]:
                channel_info = response["items"][0]
                return {
                    "title": channel_info["snippet"]["title"],
                    "description": channel_info["snippet"].get("description", "N/A"),
                    "subscriberCount": channel_info["statistics"].get("subscriberCount", "N/A"),
                    "videoCount": channel_info["statistics"].get("videoCount", "N/A")
                }
        except Exception as e:
            st.error(f"Erro ao obter informações do canal: {e}")
            return None

    def get_video_details(self, video_id):
        """Obtém detalhes do vídeo, incluindo visualizações, likes e dislikes."""
        try:
            request = youtube.videos().list(part="statistics", id=video_id)
            response = request.execute()
            if "items" in response and response["items"]:
                stats = response["items"][0]["statistics"]
                return {
                    "views": stats.get("viewCount", "N/A"),
                    "likes": stats.get("likeCount", "N/A"),
                    "dislikes": stats.get("dislikeCount", "N/A")
                }
        except Exception as e:
            st.error(f"Erro ao obter estatísticas do vídeo: {e}")
            return {"views": "N/A", "likes": "N/A", "dislikes": "N/A"}

    def get_video_ids(self, channel_url, max_results=10):
        """Obtém o channelId a partir do @handle ou da URL padrão, e busca os vídeos mais recentes."""
        handle_match = re.search(r"@([\w-]+)", channel_url)
        if handle_match:
            handle = handle_match.group(1)
            try:
                request = youtube.channels().list(part="id", forHandle=f"@{handle}")
                response = request.execute()
                if "items" in response and response["items"]:
                    channel_id = response["items"][0]["id"]
                else:
                    st.error("Não foi possível encontrar o canal.")
                    return [], None
            except Exception as e:
                st.error(f"Erro ao buscar channelId: {e}")
                return [], None
        else:
            channel_id_match = re.search(r"channel/([a-zA-Z0-9_-]+)", channel_url)
            if channel_id_match:
                channel_id = channel_id_match.group(1)
            else:
                st.error("URL do canal inválida.")
                return [], None

        channel_info = self.get_channel_info(channel_id)
        try:
            request = youtube.search().list(
                part="id,snippet",
                channelId=channel_id,
                maxResults=max_results,
                type="video",
                order="date"
            )
            response = request.execute()
            return [(item['id']['videoId'], item['snippet']['title'], datetime.strptime(item['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%SZ").strftime("%d/%m/%Y")) for item in response.get('items', [])], channel_info
        except HttpError as e:
            error_details = e.content.decode()
            try:
                error_json = json.loads(error_details)
                message = error_json['error']['message']
            except (json.JSONDecodeError, KeyError):
                message = error_details
            st.error(f"Erro ao buscar vídeos: {e}\nDetalhes: {message}")
            return [], channel_info

    def get_video_transcript(self, video_id):
        """Obtém a transcrição do vídeo, tentando diferentes métodos."""
        try:
            try:
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'en'])
            except Exception:
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([entry['text'] for entry in transcript])
        except Exception:
            st.error(f"Erro ao obter a transcrição do vídeo {video_id}: {e}")
            return None

    def process_text(self, text, num_words):
        """Processa o texto e retorna as palavras mais frequentes."""
        words = re.findall(r'\b\w+\b', text.lower())
        words = [word for word in words if word not in self.stop_words]
        counter = Counter(words)
        most_common = counter.most_common(num_words)
        total_words = sum(counter.values())

        df = pd.DataFrame(most_common, columns=["Palavra", "Quantidade"])
        df["Percentual"] = (df["Quantidade"] / total_words) * 100
        df.index = df.index + 1

        df['Quantidade'] = df['Quantidade'].apply(lambda x: locale.format_string("%d", x, grouping=True))
        df['Percentual'] = df['Percentual'].apply(lambda x: locale.format_string("%.2f%%", x))

        df_styled = df.style.set_properties(**{'text-align': 'center'})
        df_styled = df_styled.set_properties(subset=['Palavra'], **{'text-align': 'left'})
        df_styled = df_styled.set_table_styles([
            {'selector': 'thead th', 'props': [('text-align', 'center')]},
            {'selector': 'tbody th', 'props': [('text-align', 'center')]}
        ]).set_table_attributes('style="width:90%;"')

        return df_styled

class PDFGenerator:
    @staticmethod
    def generate_pdf(content_list, file_path):
        """Gera um PDF com o conteúdo fornecido."""
        doc = SimpleDocTemplate(file_path, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []

        title = "Analisador de Palavras para Canais do YouTube"
        elements.append(Paragraph(title, styles['Title']))
        elements.append(Spacer(1, 12))

        for item in content_list:
            if isinstance(item, str):
                elements.append(Paragraph(item, styles['Normal']))
                elements.append(Spacer(1, 12))
            elif isinstance(item, Table):
                elements.append(item)
                elements.append(Spacer(1, 12))

        doc.build(elements)

def main():
    st.set_page_config(page_title="Analisador de Palavras - YouTube", layout="wide")
    with open("spinner.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    st.sidebar.title("Configurações")
    channel_url = st.sidebar.text_input("Insira a URL do canal do YouTube:", "", placeholder="Exemplo: https://www.youtube.com/@canaltragicomico/")
    st.sidebar.write("Insira a URL do canal no formato válido, por exemplo, com @handle ou ID do canal.")
    num_words = st.sidebar.number_input("Quantidade de palavras mais usadas:", min_value=1, max_value=100, value=10)
    max_videos = st.sidebar.number_input("Quantidade de vídeos a analisar:", min_value=1, max_value=20, value=2)

    st.title("Analisador de Palavras para Canais do YouTube")

    col1, col2 = st.sidebar.columns(2)
    run_monitor = col1.button("Visualizar", key="monitor_button")
    run_export = col2.button("Exportar PDF", key="export_button")

    if run_monitor or run_export:
        st.empty()
        placeholder = st.empty()
        placeholder.markdown("""
            <div class="spinner-container">
                <div class="spinner"></div>
                <div class="spinner-text">Buscando vídeos...</div>
            </div>
        """, unsafe_allow_html=True)

        analyzer = YouTubeAnalyzer()
        video_data, channel_info = analyzer.get_video_ids(channel_url, max_results=max_videos)

        if not video_data:
            st.error("Não foi possível obter vídeos do canal.")
            placeholder.empty()
            return

        all_text = ""
        video_results = []

        for index, (video_id, title, published_at) in enumerate(video_data, start=1):
            placeholder.markdown(f"""
                <div class="spinner-container">
                    <div class="spinner"></div>
                    <div class="spinner-text">Analisando {index}º Vídeo com Título: {title}...</div>
                </div>
            """, unsafe_allow_html=True)

            transcript = analyzer.get_video_transcript(video_id)
            if transcript is None:
                placeholder.empty()
                return

            details = analyzer.get_video_details(video_id)
            all_text += " " + transcript
            video_df = analyzer.process_text(transcript, num_words)
            video_results.append((index, video_id, title, published_at, details, transcript, video_df))

        placeholder.empty()
        st.subheader("Resultados")

        if channel_info:
            st.subheader(f"Informações do canal: {channel_info['title']}")
            st.write(f"**Descrição:** {channel_info['description']}")
            st.write(f"**Inscritos:** {locale.format_string('%d', int(channel_info['subscriberCount']), grouping=True)}")
            st.write(f"**Quantidade de vídeos:** {locale.format_string('%d', int(channel_info['videoCount']), grouping=True)}")

        for index, video_id, title, published_at, details, transcript, df in video_results:
            dislikes_text = f" | Dislikes: {locale.format_string('%d', int(details['dislikes']), grouping=True)}" if details['dislikes'] != 'N/A' else ""
            st.write(f"### {index}. {title}")
            st.write(f"Data: {published_at} | Views: {locale.format_string('%d', int(details['views']), grouping=True)} | Likes: {locale.format_string('%d', int(details['likes']), grouping=True)}{dislikes_text}")
    
            # Exibir a transcrição em um expander
            with st.expander(f"Transcrição do vídeo"):
                st.write(transcript)
    
            st.markdown(df.set_table_styles([
                {'selector': 'thead th', 'props': [('text-align', 'center')]},
                {'selector': 'tbody th', 'props': [('text-align', 'center')]}
            ]).to_html(), unsafe_allow_html=True)

        if run_export:
            pdf_content = []
            for index, video_id, title, published_at, details, transcript, video_df in video_results:
                dislikes_text = f" | Dislikes: {locale.format_string('%d', int(details['dislikes']), grouping=True)}" if details['dislikes'] != 'N/A' else ""
                pdf_content.append(f"{index}. {title}")
                pdf_content.append(f"Data: {published_at} | Views: {locale.format_string('%d', int(details['views']), grouping=True)} | Likes: {locale.format_string('%d', int(details['likes']), grouping=True)}{dislikes_text}")

                table_data = [['#', 'Palavra', 'Quantidade', 'Percentual']]
                for idx, row in enumerate(video_df.itertuples(index=False, name=None), start=1):
                    table_data.append([idx, row[0], row[1], row[2]])

                table = Table(table_data, colWidths=[20, 240, 100, 100])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                pdf_content.append(table)

            if channel_info:
                pdf_content.insert(0, f"Quantidade de vídeos: {locale.format_string('%d', int(channel_info['videoCount']), grouping=True)}")
                pdf_content.insert(0, f"Inscritos: {locale.format_string('%d', int(channel_info['subscriberCount']), grouping=True)}")
                pdf_content.insert(0, f"**Descrição:** {channel_info['description']}")
                pdf_content.insert(0, f"Informações do canal: {channel_info['title']}")

            pdf_file_path = "resultados.pdf"
            PDFGenerator.generate_pdf(pdf_content, pdf_file_path)

            with open(pdf_file_path, "rb") as f:
                st.download_button("Baixar PDF", f, file_name="resultados.pdf", mime="application/pdf")

if __name__ == "__main__":
    main()