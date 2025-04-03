import pandas as pd

# Загрузка исходного файла
df = pd.read_excel("generated_dataset.xlsx")

# Сортировка по ИНН и дате
df = df.sort_values(by=["ИНН", "Дата_утверждения"])

# Применение оконных функций
df["prev_zone"] = df.groupby("ИНН")["Зона"].shift(1)
df["next_zone"] = df.groupby("ИНН")["Зона"].shift(-1)
df["next_date"] = df.groupby("ИНН")["Дата_утверждения"].shift(-1)

# Фильтрация по смене зоны
df["zone_change"] = df["Зона"] != df["prev_zone"]
zone_transitions = df[df["zone_change"].fillna(True)].copy()

# Нумерация шагов переходов
zone_transitions["step"] = zone_transitions.groupby("ИНН").cumcount() + 1

# Сохранение
zone_transitions.to_csv("processed_transitions_dataset.csv", index=False)