import streamlit as st
import pandas as pd
import re
import locale
from nltk.corpus import stopwords
from collections import Counter

def process_text(text, num_words):
    """Processa o texto e retorna as palavras mais frequentes, formatadas com centralização e numeração."""
    # Encontrar todas as palavras no texto e filtrar stopwords
    words = re.findall(r'\b\w+\b', text.lower())
    words = [word for word in words if word not in stopwords.words('portuguese')]
    counter = Counter(words)
    most_common = counter.most_common(num_words)
    total_words = sum(counter.values())

    # Mensagem de depuração
    st.write("Palavras mais comuns:", most_common)
    st.write("Total de palavras:", total_words)
    
    # Criar DataFrame com as palavras mais comuns
    df = pd.DataFrame(most_common, columns=["Palavra", "Quantidade"])
    df["Percentual"] = (df["Quantidade"] / total_words) * 100
    df.index = df.index + 1

    # Formatando as colunas Quantidade e Percentual
    df['Quantidade'] = df['Quantidade'].apply(lambda x: locale.format_string("%d", x, grouping=True))
    df['Percentual'] = df['Percentual'].apply(lambda x: locale.format_string("%.2f%%", x))

    # Definindo estilo para a tabela
    df_styled = df.style.set_properties(**{'text-align': 'center'})
    df_styled = df_styled.set_properties(subset=['Palavra'], **{'text-align': 'left'})
    df_styled = df_styled.set_table_styles([
        {'selector': 'thead th', 'props': [('text-align', 'center')]},
        {'selector': 'tbody th', 'props': [('text-align', 'center')]}
    ]).set_table_attributes('style="width:90%;"')

    return df_styled

# Teste da função com uma string de exemplo
if __name__ == "__main__":
    example_text = "Este é um exemplo de texto para testar a função de processamento de texto."
    st.write(process_text(example_text, 5))
