# data_preparation.py

import pandas as pd

def prepare_dataset(uploaded_file):
    df = pd.read_excel(uploaded_file)

    df = df.sort_values(by=["ИНН", "Дата_утверждения"])
    df["prev_zone"] = df.groupby("ИНН")["Зона"].shift(1)
    df["next_zone"] = df.groupby("ИНН")["Зона"].shift(-1)
    df["next_date"] = df.groupby("ИНН")["Дата_утверждения"].shift(-1)
    df["zone_change"] = df["Зона"] != df["prev_zone"]

    zone_transitions = df[df["zone_change"].fillna(True)].copy()
    zone_transitions["step"] = zone_transitions.groupby("ИНН").cumcount() + 1

    # Сохраняем как CSV
    zone_transitions.to_csv("processed_transitions_dataset.csv", index=False)
    return zone_transitions
