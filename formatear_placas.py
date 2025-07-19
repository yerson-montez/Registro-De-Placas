import pandas as pd

def formatear_placa(placa):
    placa = str(placa).upper().replace("-", "").strip()
    if len(placa) == 6:
        return placa[:3] + '-' + placa[3:]
    elif len(placa) == 7 and placa[:3].isalpha() and placa[3:].isdigit():
        return placa[:3] + '-' + placa[3:]
    else:
        return placa  # No se modifica si no cumple formato

def formatear_csv():
    df = pd.read_csv("registro.csv", encoding="utf-8-sig")
    df['placa'] = df['placa'].apply(formatear_placa)
    df.to_csv("registro.csv", index=False, encoding="utf-8-sig")
    print("✅ Placas del CSV actualizadas a formato ABC-123")

if __name__ == "__main__":
    formatear_csv()
