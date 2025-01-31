import streamlit as st
import pandas as pd
import nltk
from nltk.corpus import stopwords
from collections import Counter
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import re

# Baixar stopwords do NLTK (apenas na primeira vez)
nltk.download('stopwords')

# Configuração da API do YouTube
YOUTUBE_API_KEY = "AIzaSyD_r42vGGfDbKFR9GOy10gFPzHNxme3O6M"  # Insira sua chave da YouTube Data API
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_channel_info(channel_id):
    """Obtém informações do canal."""
    try:
        request = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        )
        response = request.execute()
        if "items" in response and response["items"]:
            channel_info = response["items"][0]
            return {
                "title": channel_info["snippet"]["title"],
                "description": channel_info["snippet"]["description"],
                "subscriberCount": channel_info["statistics"].get("subscriberCount", "N/A"),
                "videoCount": channel_info["statistics"].get("videoCount", "N/A")
            }
    except Exception as e:
        st.error(f"Erro ao obter informações do canal: {e}")
        return None

def get_video_ids(channel_url, max_results=10):
    """Obtém o channelId a partir do @handle ou da URL padrão, e busca os vídeos."""
    
    # Verifica se a URL tem um handle (@NomeDoCanal)
    handle_match = re.search(r"@([\w-]+)", channel_url)
    
    if handle_match:
        handle = handle_match.group(1)
        try:
            request = youtube.channels().list(
                part="id",
                forHandle=f"@{handle}"
            )
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
        # Caso a URL contenha um channelId diretamente
        channel_id_match = re.search(r"channel/([a-zA-Z0-9_-]+)", channel_url)
        if channel_id_match:
            channel_id = channel_id_match.group(1)
        else:
            st.error("URL do canal inválida.")
            return [], None
    
    # Buscar informações do canal
    channel_info = get_channel_info(channel_id)
    
    # Agora que temos o channelId, buscar vídeos
    try:
        request = youtube.search().list(
            part="id,snippet",
            channelId=channel_id,
            maxResults=max_results,
            type="video"
        )
        response = request.execute()

        return [(item['id']['videoId'], item['snippet']['title'], item['snippet']['publishedAt']) for item in response.get('items', [])], channel_info
    
    except Exception as e:
        st.error(f"Erro ao buscar vídeos: {e}")
        return [], channel_info

def get_video_transcript(video_id):
    """Obtém a transcrição do vídeo, tentando diferentes métodos."""
    try:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'en'])
        except Exception:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)  # Tenta qualquer idioma disponível
        return " ".join([entry['text'] for entry in transcript])
    except Exception:
        return ""

def process_text(text, top_n):
    """Conta palavras mais usadas e calcula percentual."""
    text = text.lower()
    text = re.sub(r'[^a-zA-ZÀ-ÿ\s]', '', text)  # Remover pontuação e números
    words = text.split()
    stop_words = set(stopwords.words('portuguese'))
    words = [word for word in words if word not in stop_words]
    
    word_counts = Counter(words)
    total_words = sum(word_counts.values())
    
    df = pd.DataFrame(word_counts.most_common(top_n), columns=['Palavra', 'Frequência'])
    df['Percentual'] = (df['Frequência'] / total_words) * 100
    return df

def main():
    st.set_page_config(page_title="Analisador de Palavras - YouTube", layout="wide")
    st.sidebar.title("Configurações")
    channel_url = st.sidebar.text_input("Insira a URL do canal do YouTube:", "", placeholder="Exemplo: https://www.youtube.com/@canaltragicomico/")
    st.sidebar.write("Insira a URL do canal no formato válido, por exemplo, com @handle ou ID do canal.")
    num_words = st.sidebar.number_input("Quantidade de palavras mais usadas:", min_value=1, max_value=100, value=10)
    
    st.title("Analisador de Palavras de um Canal do YouTube")
    
    if st.sidebar.button("Analisar"):
        st.write("Buscando vídeos...")
        video_data, channel_info = get_video_ids(channel_url)
        
        if not video_data:
            st.error("Não foi possível obter vídeos do canal.")
            return
        
        if channel_info:
            st.subheader(f"Informações do canal: {channel_info['title']}")
            st.write(f"**Descrição:** {channel_info['description']}")
            st.write(f"**Inscritos:** {channel_info['subscriberCount']}")
            st.write(f"**Quantidade de vídeos:** {channel_info['videoCount']}")
        
        all_text = ""
        video_results = []
        
        for video_id, title, published_at in video_data:
            transcript = get_video_transcript(video_id)
            all_text += " " + transcript
            video_df = process_text(transcript, num_words)
            video_results.append((video_id, title, published_at, video_df))
        
        if not all_text.strip():
            st.error("Não foi possível obter legendas dos vídeos.")
            return
        
        channel_df = process_text(all_text, num_words)
        
        st.subheader("Palavras mais usadas no canal")
        st.dataframe(channel_df)
        
        st.subheader("Palavras mais usadas por vídeo")
        for video_id, title, published_at, df in video_results:
            st.write(f"#### {title} ({published_at})")
            st.dataframe(df)

if __name__ == "__main__":
    main()
