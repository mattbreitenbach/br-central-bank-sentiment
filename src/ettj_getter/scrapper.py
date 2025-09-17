from datetime import datetime
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import pandas_market_calendars as mcal


def baixar_ajuste_bmf(data: str = False) -> pd.DataFrame:
    """
    Faz e webscraping e retorna a tabela de ajustes do site da BMF (Bolsa de Mercadorias e Futuros), para a data desejada, como um DataFrame do Pandas.

    Args:
        data (str, opcional): Data de referência para a tabela de ajustes no formato 'dd/mm/aaaa'.
            Se não for especificada ou for igual a "today", a função buscará os ajustes do dia atual.

    Returns:
        pd.DataFrame: DataFrame contendo a tabela de ajustes com as colunas extraídas da página web.
    """

    dados = []

    url_adicional = ""
    if data:
        url_adicional = f"?txtData={data}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    req = Request(f"https://www2.bmf.com.br/pages/portal/bmfbovespa/boletim1/Ajustes1.asp{url_adicional}", headers=headers)
    url = urlopen(req)

    soup = BeautifulSoup(url.read(), 'html.parser')

    tabela = soup.find("table", id="tblDadosAjustes")
    tr = tabela.find_all('tr')
    for t in tr:
        dados.append(t.text.split('\n'))

    if len(dados) < 3:
        raise ValueError("Verifique a data.")

    df = pd.DataFrame(dados[1:], columns=dados[0])
    df.Mercadoria = df.Mercadoria.replace("", np.nan)
    df.Mercadoria = df.Mercadoria.ffill()
    df.Mercadoria = df.Mercadoria.str.strip()
    df.drop("", axis=1, inplace=True)

    colunas_to_format = [
        "Preço de Ajuste Anterior",
        "Preço de Ajuste Atual",
        "Variação",
        "Valor do Ajuste por Contrato (R$)"]
    for coluna in colunas_to_format:
        df[coluna] = df[coluna].str.replace(
            ".", "", regex=False).str.replace(",", ".").astype(float)

    df["Mercadoria"] = df["Mercadoria"].str.strip().str.replace(r'\s+',
                                                                ' ', regex=True)
    df["Vct"] = df["Vct"].str.replace(" ", "")

    if not data:
        azul = soup.find_all("td", {"class": "TXT_Azul"})[1]
        data = azul.text[-11:-1]
    data_obj = datetime.strptime(data, "%d/%m/%Y").date()
    df.insert(0, "Data Pregão", data_obj)

    return df


def baixar_ajuste_bmf_multiplos_dias(data_inicial: str, data_final: str, excludes: list[str] = []) -> pd.DataFrame:
    """
    Baixa e retorna a tabela de ajustes da BMF para um intervalo de datas especificado, excluindo datas opcionais, se fornecidas.

    Args:
        data_inicial (str): Data de início do período no formato 'dd/mm/aaaa'.
        data_final (str): Data de fim do período no formato 'dd/mm/aaaa'.
        excludes (list, opcional): Lista de datas no formato 'dd/mm/aaaa' a serem excluídas do processamento.

    Returns:
        pd.DataFrame: DataFrame contendo os dados consolidados dos ajustes para o período solicitado.
    """

    data_inicial = datetime.strptime(data_inicial, "%d/%m/%Y")
    data_final = datetime.strptime(data_final, "%d/%m/%Y")

    calendario = mcal.get_calendar("BMF")
    du_periodo = calendario.schedule(
        start_date=data_inicial, end_date=data_final)

    du_periodo = du_periodo.index.to_list()
    du_periodo = [day.strftime("%d/%m/%Y") for day in du_periodo]

    if len(excludes) > 0:
        du_periodo = [day for day in du_periodo if day not in excludes]

    df_list = []

    for day in du_periodo:
        try:
            df_temp = baixar_ajuste_bmf(day)
            df_list.append(df_temp)
        except:
            continue

    df = pd.concat(df_list, ignore_index=True) if df_list else pd.DataFrame()

    return df
