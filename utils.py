from bs4 import BeautifulSoup
import re

def parse_ingredients(cell):
    ingredients = []
    for li in cell.find_all('li'):
        name = li.get_text(strip=True)
        quantity_match = re.search(r'(\d+)$', name)
        quantity = quantity_match.group(1) if quantity_match else '?'
        
        if quantity != '?':
            name = name[: -len(quantity)].strip()

        img = li.find('img')['data-src']
        link = 'https://terraria.fandom.com' + li.find('a')['href']

        ingredients.append({
            'name': name,
            'quantity': quantity,
            'img': img,
            'link': link
        })
    return ingredients

def create_embed_table(html):
    soup = BeautifulSoup(html, 'html.parser')

    tables = soup.find_all('table', class_="terraria cellborder recipes sortable")

    if not tables:
        return {
            'result': None,
            'recipes': [],
            'stations': []
        }

    # Obtener filas de la tabla
    rows = tables[0].find_all('tr')[1:]

    result_name, result_img, result_link = None, None, None
    station_data = []
    recipe_variants = []

    for i, row in enumerate(rows):
        cells = row.find_all('td')
        

        # Primera fila: contiene resultado, ingredientes y estación
        if len(cells) == 3:
            result_cell, ingredient_cell, station_cell = cells

            # Parsear el resultado (solo una vez)
            if result_name is None:
                result_name = result_cell.get_text(strip=True)
                result_img = result_cell.find('img')['data-src']
                result_link = 'https://terraria.fandom.com' + result_cell.find('a')['href']

            # Parsear estaciones (solo una vez)
            if not station_data:
                for a in station_cell.find_all('a'):
                    name = a.get_text(strip=True)
                    img_tag = a.find('img')
                    img = img_tag['data-src'] if img_tag else None
                    link = 'https://terraria.fandom.com' + a['href']
                    station_data.append({
                        'name': name,
                        'img': img,
                        'link': link
                    })

            recipe_variants.append(parse_ingredients(ingredient_cell))

        # Filas siguientes: solo contienen variantes de ingredientes
        elif len(cells) == 1:
            ingredient_cell = cells[0]
            recipe_variants.append(parse_ingredients(ingredient_cell))

    return {
        'result': {
            'name': result_name,
            'img': result_img,
            'link': result_link
        },
        'recipes': recipe_variants,
        'stations': station_data
    }

def obtener_tipo_de_elemento(html):

    soup = BeautifulSoup(html, 'html.parser')

    content = soup.find('div', class_= "mw-content-ltr mw-parser-output")
    aside = content.find('aside')

    if aside:
        tipo = aside.find(attrs={'data-source': 'tipo'})
        return str(tipo.get_text().split()[1]) if tipo else None
    else:
        return None

def se_puede_comprar(html):

    soup = BeautifulSoup(html, 'html.parser')

    content = soup.find('div', class_="mw-content-ltr mw-parser-output")
    aside = content.find('aside')

    final_price = []
    vendido_por = None

    if aside:
        comprar_head = aside.find(attrs={'data-source': 'compra'})
        if comprar_head:
            comprar_div = comprar_head.find("div", class_="pi-data-value")
            if comprar_div:
                for span in comprar_div.find_all("span", style=lambda v: v and "white-space:nowrap" in v):
                    amount = span.get_text(strip=True).split()[0]
                    title = span['title']
                    coin_type = " ".join(title.split()[1:])
                    final_price.append(f"{amount} {coin_type}")

        comprado_head = aside.find(attrs={'data-source': 'comprado'})
        if comprado_head:
            comprado_div = comprado_head.find("div", class_="pi-data-value")
            if comprado_div:
                vendido_por = comprado_div.get_text(strip=True)
                vendido_por_a = comprado_div.find('a')
                if vendido_por_a:
                    vendido_por_link = 'https://terraria.fandom.com' + vendido_por_a['href']
                    vendido_por = f"[{vendido_por}]({vendido_por_link})"
                else:
                    vendido_por = f"{vendido_por}"
                
    return [final_price, vendido_por]

def se_puede_encontrar(html):

    soup = BeautifulSoup(html, 'html.parser')

    content = soup.find('div', class_="mw-content-ltr mw-parser-output")
    aside = content.find('aside')

    if aside:
        encontrar_head = aside.find(attrs={'data-source': 'encontrado'})
        if encontrar_head:
            encontrar_div = encontrar_head.find("div", class_="pi-data-value")
            if encontrar_div:
                encontrado_por = encontrar_div.get_text(strip=True)
                encontrado_por_a = encontrar_div.find('a')
                if encontrado_por_a:
                    encontrado_por_link = 'https://terraria.fandom.com' + encontrado_por_a['href']
                
                return f"[{encontrado_por}]({encontrado_por_link})"

def se_puede_dropear(html):
    soup = BeautifulSoup(html, 'html.parser')

    content = soup.find('div', class_="mw-content-ltr mw-parser-output")
    aside = content.find('aside')

    dropeado_por = []
    drop_chance = None

    if aside:
        dropear_head = aside.find(attrs={'data-source': 'dejado'})
        if dropear_head:
            dropear_div = dropear_head.find("div", class_="pi-data-value")
            if dropear_div:
                for a in dropear_div.find_all('a'):
                    name = a.get_text(strip=True)
                    href = a.get('href')
                    if name and href:
                        dropeado_por.append(f"[{name}](https://terraria.fandom.com{href})")

                text = dropear_div.get_text(separator=" ", strip=True)
                # Remove enemy names from text
                for a in dropear_div.find_all("a"):
                    text = text.replace(a.get_text(strip=True), "")
                # Clean up and extract chance
                text = text.strip()
                if text:
                    drop_chance = text

                return [dropeado_por, drop_chance]
    return [dropeado_por, drop_chance]

def get_item_icon(html):
    soup = BeautifulSoup(html, 'html.parser')
    content = soup.find('div', class_="mw-content-ltr mw-parser-output")
    aside = content.find('aside')

    if aside:
        icon = aside.find(attrs={'data-source': 'imagen'})
        if icon:
            a_tag = icon.find('a')
            if a_tag and a_tag.has_attr('href'):
                return a_tag['href']
    return None



