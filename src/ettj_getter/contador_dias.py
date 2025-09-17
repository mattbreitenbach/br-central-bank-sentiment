import pandas as pd
import pandas_market_calendars as mcal
from datetime import datetime


MONTH_CODES = {"F": 1,
               "G": 2,
               "H": 3,
               "J": 4,
               "K": 5,
               "M": 6,
               "N": 7,
               "Q": 8,
               "U": 9,
               "V": 10,
               "X": 11,
               "Z": 12}


start_date = datetime.strptime("01/01/1990", "%d/%m/%Y")
end_date = datetime.strptime("01/01/2070", "%d/%m/%Y")
DUS_DF = mcal.get_calendar("BMF").schedule(
    start_date=start_date, end_date=end_date)
DCS_DF = pd.date_range(start=start_date, end=end_date,
                       freq="D").to_frame(index=True, name="date")


def get_first_du_month(month: str, year: str) -> datetime:
    """
    Retorna o primeiro dia útil do dado o mês e ano, usando como base o calendario da B3.

    Args:
        month (str): mês de busca.
        year (str): ano de busca.

    Returns:
        datetime.datetime: data do primeiro dia útil, em formato datetime.
    """
    dus_month = DUS_DF[(DUS_DF.index.month == int(month))
                       & (DUS_DF.index.year == int(year))]
    first_du_month = dus_month.index[0]
    return first_du_month.to_pydatetime()


def get_last_du_month(month: str, year: str) -> datetime:
    """
    Retorna o último dia útil do dado o mês e ano, usando como base o calendário da B3.

    Args:
        month (str): mês de busca.
        year (str): ano de busca.

    Returns:
        datetime.datetime: data do último dia útil, em formato datetime.
    """
    dus_month = DUS_DF[(DUS_DF.index.month == int(month))
                       & (DUS_DF.index.year == int(year))]
    last_du_month = dus_month.index[-1]
    return last_du_month.to_pydatetime()


def get_third_friday_du_month(month: str, year: str) -> datetime:
    """
    Retorna a terceira sexta-feira do mês, usando como base o calendário da B3. Caso seja feirado no dia, retorna dia útil anterior.

    Args:
        month (str): mês de busca.
        year (str): ano de busca.

    Returns:
        datetime.datetime: terceira sexta-feira, em formato datetime.
    """
    dcs_month = DCS_DF[(DCS_DF.index.month == int(month))
                       & (DCS_DF.index.year == int(year))]
    dcs_month["wd"] = dcs_month.index.weekday
    dcs_month = dcs_month[dcs_month["wd"] == 4]
    third_friday = dcs_month.index[2]

    if third_friday not in DUS_DF.index:
        dus_ate = DUS_DF[DUS_DF.index < third_friday]
        return dus_ate.index[-1].to_pydatetime()

    else:
        return third_friday.to_pydatetime()


def get_wednesday_closest_fifteen(month: str, year: str) -> datetime:
    """
    Retorna a quarta-feira mais proxima do dia 15 do mês, usando como base o calendário da B3. Caso seja feirado no dia, retorna o proximo dia útil .

    Args:
        month (str): mês de busca.
        year (str): ano de busca.

    Returns:
        datetime.datetime: quarta-feira mais proxima do dia 15, em formato datetime.
    """
    dcs_month = DCS_DF[(DCS_DF.index.month == int(month))
                       & (DCS_DF.index.year == int(year))]
    dcs_month["wd"] = dcs_month.index.weekday
    wednesdays = dcs_month[dcs_month["wd"] == 2]

    wednesdays["dist_fifteen"] = abs(15 - wednesdays.index.day)

    closest_wednesday = wednesdays.sort_values(by=("dist_fifteen")).index[0]

    if closest_wednesday not in DUS_DF.index:
        dus_depois = DUS_DF[DUS_DF.index > closest_wednesday]
        return dus_depois.index[0].to_pydatetime()

    else:
        return closest_wednesday.to_pydatetime()


def get_fifteen(month: str, year: str) -> datetime:
    """
    Retorna o dia 15 do mês, usando como base o calendário da B3. Caso seja feirado no dia, retorna o proximo dia útil .

    Args:
        month (str): mês de busca.
        year (str): ano de busca.

    Returns:
        datetime.datetime: dia 15, em formato datetime.
    """
    dus_month = DUS_DF[(DUS_DF.index.month == int(month))
                       & (DUS_DF.index.year == int(year))]

    if month < 10:
        month = f"0{month}"
    dia_15 = datetime.strptime(f"15/{month}/{year}", "%d/%m/%Y")

    dus_month = dus_month[dus_month.index >= dia_15]

    return dus_month.index[0].to_pydatetime()


def add_dia_vencimento_df(df: pd.DataFrame, metodo_venc: str) -> pd.DataFrame:
    """
    Em um df, no formato do banco de dados, adiciona a coluna "vencimento_dt", com a data de vencimento do contrato.

    Args:
        df (pd.DataFrame): DataFrame contendo contratos futuros. A coluna "vencimento" deve estar no formato da CME "<M><YY>".
        metodo_venc (str): Método para determinar a data de vencimento. As opções disponíveis são:
            - 'prim_du': Primeiro dia útil do mês.
            - 'ult_du': Último dia útil do mês.
            - 'terceira_sexta': Terceira sexta-feira do mês.
            - 'quarta_prox_quinze': Quarta-feira mais próxima do dia 15.
            - 'dia_15': dia 15 do mês.

    Returns:
        pd.DataFrame: df original, com a coluna de vencimento.
    """
    df["mes_vcto"] = df["vencimento"].str[0]
    df["mes_vcto"] = df["mes_vcto"].map(MONTH_CODES)
    df["ano_vcto"] = "20" + df["vencimento"].str[1:]

    if metodo_venc == "prim_du":
        df["vencimento_dt"] = df.apply(lambda row: get_first_du_month(
            row["mes_vcto"], row["ano_vcto"]), axis=1)
    elif metodo_venc == "ult_du":
        df["vencimento_dt"] = df.apply(lambda row: get_last_du_month(
            row["mes_vcto"], row["ano_vcto"]), axis=1)
    elif metodo_venc == "terceira_sexta":
        df["vencimento_dt"] = df.apply(lambda row: get_third_friday_du_month(
            row["mes_vcto"], row["ano_vcto"]), axis=1)
    elif metodo_venc == "quarta_prox_quinze":
        df["vencimento_dt"] = df.apply(lambda row: get_wednesday_closest_fifteen(
            row["mes_vcto"], row["ano_vcto"]), axis=1)
    elif metodo_venc == "dia_15":
        df["vencimento_dt"] = df.apply(lambda row: get_fifteen(
            row["mes_vcto"], row["ano_vcto"]), axis=1)

    df = df.drop(["mes_vcto", "ano_vcto"], axis=1)
    return df


def calc_du(dia_1: datetime, dia_n: datetime) -> int:
    """
    Retorna a diferença de dias úteis entre 2 datas. Contando o primeiro dia mas não o último dia.

    Args:
        dia_1 (datetime): primeiro dia, no caso do sistema, o dia do pregão.
        dia_n (datetime): último dia, no caso do sistema, o dia do vencimento.

    Returns:
        int: quantidade de dias úteis entre as duas datas.
    """
    dias_distancia = DUS_DF[(DUS_DF.index > dia_1) & (
        DUS_DF.index <= dia_n)].index.to_list()
    return len(dias_distancia)


def calc_du_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Em um df, no formato do banco de dados, já com a coluna 'vencimento_dt', adiciona a coluna 'du', com quantos dias úteis até o vencimento do contrato.

    Args:
        df (pd.DataFrame): no formato do banco de dados, já com a coluna 'vencimento_dt'.

    Returns:
        pd.DataFrame: df original, com a coluna 'du'.
    """
    df["du"] = df.apply(lambda row: calc_du(
        row["data_pregao"], row["vencimento_dt"]), axis=1)
    return df


def calc_dc(dia_1: datetime, dia_n: datetime):
    """
    Retorna a diferença de dias corridos entre 2 datas. Contando o primeiro dia mas não o último dia.

    Args:
        dia_1 (datetime): primeiro dia, no caso do sistema, o dia do pregão.
        dia_n (datetime): último dia, no caso do sistema, o dia do vencimento.

    Returns:
        int: quantidade de dias corridos entre as duas datas.
    """
    dias_distancia = DCS_DF[(DCS_DF.index > dia_1) & (
        DCS_DF.index <= dia_n)].index.to_list()
    return len(dias_distancia)


def calc_dc_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Em um df, no formato do banco de dados, já com a coluna 'vencimento_dt', adiciona a coluna 'dc', com quantos dias corridos até o vencimento do contrato.

    Args:
        df (pd.DataFrame): no formato do banco de dados, já com a coluna 'vencimento_dt'.

    Returns:
        pd.DataFrame: df original, com a coluna 'dc'.
    """
    df["dc"] = df.apply(lambda row: calc_dc(
        row["data_pregao"], row["vencimento_dt"]), axis=1)
    return df
