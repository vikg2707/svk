from flask import Flask, request
import pandas as pd
import random
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'

base_icons = [
    "pill", "first-aid-kit", "pharmacy-shop", "hospital-room", "syringe", "stethoscope"
]

icon_colors = [
    "4caf50", "2196f3", "ff9800", "f44336", "9c27b0"
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
  <meta charset="UTF-8">
  <title>СВК Фарм - Аптеки</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      background-color: #fffbea;
      padding: 20px;
    }}
    h1 {{
      text-align: center;
      color: #0057b7;
      text-shadow: 1px 1px 2px #ffd700;
    }}
    .pharmacy {{
      background: white;
      border-left: 6px solid #0057b7;
      border-radius: 8px;
      padding: 15px;
      margin-bottom: 15px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.1);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .pharmacy .info {{
      max-width: 80%;
    }}
    .pharmacy img {{
      width: 50px;
      height: 50px;
      margin-left: 15px;
      flex-shrink: 0;
    }}
    .drugs-list {{
      text-align: center;
      margin-top: 30px;
      margin-bottom: 30px;
    }}
    .drugs-list h2 {{
      color: #0057b7;
    }}
    .drugs-list a {{
      color: #0057b7;
      font-weight: bold;
      margin: 0 5px;
      font-size: 18px;
      text-decoration: none;
      cursor: pointer;
      user-select: none;
    }}
    .drugs-list a:hover {{
      text-decoration: underline;
      color: #003d99;
    }}
    form {{
      max-width: 400px;
      margin: 0 auto 10px auto;
      padding: 20px;
      background: white;
      border-radius: 8px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.1);
      text-align: center;
    }}
    form input[type="text"] {{
      width: 80%;
      padding: 10px;
      margin-bottom: 10px;
      font-size: 16px;
      border: 1px solid #ccc;
      border-radius: 4px;
    }}
    form button {{
      padding: 10px 20px;
      background-color: #0057b7;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 16px;
    }}
    form button:hover {{
      background-color: #003d99;
    }}
    .search-results {{
      max-width: 800px;
      margin: 10px auto 30px auto;
      background: white;
      border-left: 6px solid #ffd700;
      border-radius: 8px;
      padding: 15px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.1);
      text-align: center;
      font-size: 18px;
    }}
  </style>
</head>
<body>
  <h1>Аптеки СВК Фарм</h1>

  <form method="GET" action="/">
    <input type="text" name="search" placeholder="Пошук ліків" value="{search_query}" required>
    <button type="submit">Пошук</button>
  </form>

  <div class="search-results">
    {search_results_html}
  </div>

  {pharmacies_html}

  <div class="drugs-list">
    <h2>Асортимент</h2>
    {random_drugs_html}
  </div>

</body>
</html>
"""

def clean_drug_name_for_url(name: str) -> str:
    name = name.split("//")[0]
    stop_patterns = [
        r"пак\.?", r"табл\.?", r"капс\.?", r"крап\.?", r"мг", r"г", r"№", r"х", r"/",
        r"р\-н", r"р\-н д", r"розчин", r"амп", r"ін'єкц", r"ін'єкц\.", r"сусп", r"суспензія",
        r"мазь", r"крем", r"гель", r"пластир", r"спрей", r"крапл", r"свіч", r"свічки"
    ]

    words = name.split()
    stop_index = len(words)

    for i, w in enumerate(words):
        w_lower = w.lower()
        if re.search(r"\d", w_lower):
            stop_index = min(stop_index, i)
            continue
        for pattern in stop_patterns:
            if re.match(pattern, w_lower):
                stop_index = min(stop_index, i)
                break

    cleaned_name = " ".join(words[:stop_index]).strip()
    return cleaned_name if len(cleaned_name) >= 3 else name.strip()

@app.route("/", methods=["GET"])
def index():
    df_pharmacies = pd.read_excel("contacts.xlsx")
    records = df_pharmacies.to_dict(orient="records")

    pharmacy_blocks = ""
    for item in records:
        icon_name = random.choice(base_icons)
        icon_color = random.choice(icon_colors)
        icon_url = f"https://img.icons8.com/ios-filled/50/{icon_color}/{icon_name}.png"

        pharmacy_blocks += f"""
        <div class="pharmacy">
          <div class="info">
            <h3>{item.get("Назва аптеки", "")}</h3>
            <p><strong>Адреса:</strong> {item.get("Адреса", "")}</p>
            <p><strong>Телефон:</strong> {item.get("Телефон", "")}</p>
          </div>
          <img src="{icon_url}" alt="Іконка">
        </div>
        """

    df_drugs = pd.read_excel("drugs.xlsx")
    drugs_list = df_drugs["Назва ліків"].dropna().tolist()

    random_drugs = random.sample(drugs_list, min(10, len(drugs_list)))
    random_drugs_html = " ".join(
        f'<a href="https://tabletki.ua/uk/search/{clean_drug_name_for_url(drug).replace(" ", "%20")}/" target="_blank" rel="noopener noreferrer">{clean_drug_name_for_url(drug)}</a>'
        for drug in random_drugs
    )

    search_query = request.args.get("search", "").strip()
    search_results_html = ""

    if search_query:
        filtered_rows = df_drugs[df_drugs["Назва ліків"].str.lower().str.contains(search_query.lower(), na=False)]
        if not filtered_rows.empty:
            search_results_html = "<h2>Результати пошуку:</h2><ul style='list-style:none; padding:0;'>"
            for _, row in filtered_rows.head(20).iterrows():
                drug_name = str(row["Назва ліків"])
                price = row.get("Ціна", "Н/Д")
                url = f"https://tabletki.ua/uk/search/{clean_drug_name_for_url(drug_name).replace(' ', '%20')}/"
                search_results_html += f"<li><a href='{url}' target='_blank' rel='noopener noreferrer'>{clean_drug_name_for_url(drug_name)}</a> — <strong>{price}</strong></li>"
            search_results_html += "</ul>"
        else:
            search_results_html = "<p>Ліки не знайдені.</p>"

    return HTML_TEMPLATE.format(
        pharmacies_html=pharmacy_blocks,
        random_drugs_html=random_drugs_html,
        search_query=search_query,
        search_results_html=search_results_html
    )

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
