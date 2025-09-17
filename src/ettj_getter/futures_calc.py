import pandas as pd


def calc_taxa_local(preco_ajuste: float, du: int) -> float:
    """
    Calcula a taxa de juros anualizada para contratos locais, funciona para DI1 e DAP.
    A taxa é calculada com base no preço de ajuste do contrato e no número de dias úteis até o vencimento.

    Args:
        preco_ajuste (float): O preço de ajuste do contrato futuro.
        du (int): Dias úteis até o vencimento do contrato.

    Returns:
        float: Taxa de juros anualizada na base 252 dias úteis.
    """
    taxa_local = ((100000/float(preco_ajuste))**(252/du)) - 1
    return taxa_local


def calc_taxa_local_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula a taxa de juros anualizada para contratos locais, funciona para DI1 e DAP, em um DataFrame.

    Args:
        df (pd.DataFrame): DataFrame contendo as colunas:
            - 'preco_ajuste' (float): O preço de ajuste do contrato futuro.
            - 'du"' (int): Dias úteis até o vencimento do contrato.

    Retorna:
        pd.DataFrame: O DataFrame original com a nova coluna 'taxa' contendo as taxas calculadas.
    """
    df = df[df["du"] > 0]
    df["taxa"] = df.apply(lambda row: calc_taxa_local(
        row["preco_ajuste"], row["du"]), axis=1)
    return df
