import os
import re
import json
import discord
import logging
import requests
import aiohttp
from utils import *
from bs4 import BeautifulSoup
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix='/', intents = intents
)

roles_terraria = {"mago":"🪄 Mago","invocador":"🐉 Invocador","tanque":"🛡️ Guardián", "distancia":"🏹 Distancia"}

# Idiomas soportados por la wiki de Terraria
supported_languages = {
    "es": "es",    # Español
    "en": "en",    # Inglés
    # "pt": "pt-br", # Portugués (Brasil)
    # "fr": "fr",    # Francés
    # "de": "de",    # Alemán
    # "ru": "ru",    # Ruso
    # "it": "it",    # Italiano
    # "pl": "pl",    # Polaco
    # "zh": "zh",    # Chino
    # "ja": "ja",    # Japonés
}

# Guardar idioma por servidor
guild_languages = {}
url_base = None

def get_wiki_base_url(msg):
    if msg == "en":
        return "https://terraria.fandom.com/wiki"
    else:
        return f"https://terraria.fandom.com/{msg}/wiki"

@bot.command()
async def idioma(ctx, *, msg):
    global url_base
    if msg not in supported_languages:
        await ctx.send("❌ Idioma no soportado. Usa uno de los siguientes: " + ", ".join(supported_languages.keys()))
        return

    url_base = get_wiki_base_url(msg)
    await ctx.send(f"✅ Idioma de la wiki cambiado a: **{msg}**")


@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} está listo y conectado a Discord!')

@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to the server {member.name}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    await bot.process_commands(message)

@bot.command()
async def saludar(ctx):
    await ctx.send(f"Hola {ctx.author.mention}! Como estas?")

@bot.command()
async def asignar(ctx, *, msg):
    key = next((k for k in roles_terraria if k.lower() in msg.lower()), None)
    if key:
        role_name = roles_terraria[key]
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            await ctx.author.add_roles(role)
            await ctx.send(f"{ctx.author.mention} ahora es un {role_name}, ¡Buena suerte!")
        else:
            await ctx.send("No se encontró el rol en el servidor.")
    else:
        await ctx.send("No especificaste un rol válido. Opciones: " + ", ".join(roles_terraria.keys()))

@asignar.error
async def asignar_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Por favor, especifica un rol válido. Opciones: " + ", ".join(roles_terraria.keys()))
    else:
        await ctx.send("Ocurrió un error al intentar asignar el rol. Por favor, inténtalo de nuevo.")

@bot.command()
async def quitar(ctx, *, msg):
    key = next((k for k in roles_terraria if k.lower() in msg.lower()), None)
    if key:
        role_name = roles_terraria[key]
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            await ctx.author.remove_roles(role)
            await ctx.send(f"{ctx.author.mention} ya NO es un {role_name}")
        else:
            await ctx.send("No se encontró el rol en el servidor.")
    else:
        await ctx.send("No especificaste un rol válido. Opciones: " + ", ".join(roles_terraria.keys()))

@quitar.error
async def quitar_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Por favor, especifica un rol válido. Opciones: " + ", ".join(roles_terraria.keys()))
    else:
        await ctx.send("Ocurrió un error al intentar quitar el rol. Por favor, inténtalo de nuevo.")

@bot.command()
async def buscar(ctx, *, msg):
    item_name = msg.replace(' ', '_').capitalize()
    url = f"{url_base}/{item_name}"

    page = requests.get(url)

    if page.status_code != 200:
        await ctx.send("❌ No se encontró el objeto en la wiki de Terraria. Revisa el nombre y vuelve a intentarlo.")
        return

    soup = BeautifulSoup(page.content, 'html.parser')

    # Buscar si existe una sección "Creacion" o "Usos"
    section_type = None
    for h2 in soup.find_all('h2'):
        span = h2.find('span', class_="mw-headline")
        if span and span.get('id') in ["Creacion", "Usos", "Creación"]:
            section_type = span.get('id')
            break
    # print(f"Tipo de sección: {section_type}")

    tables = soup.find_all('table', class_="terraria cellborder recipes sortable")
    content_div = soup.find('div', class_="mw-content-ltr mw-parser-output")
    aside = content_div.find('aside') if content_div else None

    precio_compra, vendido_por = se_puede_comprar(str(content_div))
    # print(f"Precio de compra: {purchase_price}, Vendido por: {sold_by}")
    encontrado_en = se_puede_encontrar(str(content_div))
    # print(f"Encontrado en: {encontrado_en}")
    dropeado_por, proba_dropeo = se_puede_dropear(str(content_div))
    # print(f"Dejado por enemigos: {dropped_by}, Probabilidad de drop: {drop_chance}")
    tipo_de_elemento = obtener_tipo_de_elemento(str(content_div))
    # print(f"Tipo de elemento: {tipo_de_elemento}")
    embed_table = create_embed_table(str(content_div))
    # print(f"Tabla de creación: {embed_table}")


    # Determine status summary
    status = []
    if vendido_por is not None:
        status.append("🛒 Se puede comprar")
    if encontrado_en:
        status.append("🔎 Se puede encontrar")
    if proba_dropeo is not None:
        status.append("🎲 Lo dejan enemigos")
    if embed_table['recipes'] and section_type in ["Creacion", "Creación"]:
        status.append("🔨 Se puede fabricar")
    if embed_table['recipes'] and section_type == "Usos":
        status.append("🧪 Se usa para fabricar")
    if not status:
        status.append("")

    # Get item description
    paragraph = []
    if aside:
        for sibling in aside.next_siblings:
            if isinstance(sibling, str) and not sibling.strip():
                continue
            if hasattr(sibling, 'name') and sibling.name == 'table':
                break
            if hasattr(sibling, 'name'):
                text = sibling.get_text(separator=" ", strip=True)
                if text:
                    paragraph.append(text)
            else:
                if isinstance(sibling, str):
                    text = sibling.strip()
                    if text:
                        paragraph.append(text)
    description = " ".join(paragraph)
    description = re.sub(r'\s+\.', '.', description)
    description = re.sub(r'\s{2,}', ' ', description)
    description = description.strip()

    # Create the embed
    embed = discord.Embed(
        title=f"{msg.capitalize()}",
        description=f"{' | '.join(status)}\n\n{description}",
        color=discord.Color.orange()
    ).set_thumbnail(url=get_item_icon(str(content_div)))


    if tipo_de_elemento == "Enemigo" or tipo_de_elemento == "Jefe" or tipo_de_elemento == "Monstruo":
        
        vida = aside.find(attrs={'data-source': 'vida'})
        bioma = aside.find(attrs={'data-source': 'biomas'})
        subtipo = aside.find(attrs={'data-source': 'subtipo'})
        dano = aside.find(attrs={'data-source': 'daño'})
        defensa = aside.find(attrs={'data-source': 'defensa'})

        embed.add_field(
            name="🧟 Información del enemigo",
            value=(
            f"🔀 **Subtipo:** {subtipo.get_text().split()[1] if subtipo else 'N/A'}\n"
            f"🌎 **Bioma:** {bioma.get_text().split()[1] if bioma else 'Desconocido'}\n"
            f"❤️ **Vida:** {vida.get_text().split()[1] if vida else 'Desconocida'}\n"
            f"⚔️ **Daño:** {dano.get_text().split()[1] if dano else 'Desconocido'}\n"
            f"🛡️ **Defensa:** {defensa.get_text().split()[1] if defensa else 'Desconocida'}"
            ),
            inline=False
        )

        # Mostrar los objetos que deja el enemigo y sus probabilidades de drop
        drops = []
        # Find all drop and money divs in the aside
        drop_money_divs = aside.find_all("div", class_="pi-smart-data-value")
        i = 0
        while i < len(drop_money_divs):
            div = drop_money_divs[i]
            data_source = div.get("data-source", "")
            # Handle money drop
            if data_source == "dinero":
                # Get the amount and coin type (text + img alt)
                amount = div.get_text(" ", strip=True)
                img = div.find("img")
                coin = img["alt"] if img and img.has_attr("alt") else ""
                money_name = f"{amount} {coin}".strip()
                # Try to get probability from next div if it is also dinero
                prob_text = "Desconocida"
                if i + 1 < len(drop_money_divs) and drop_money_divs[i + 1].get("data-source", "") == "dinero":
                    prob_text = drop_money_divs[i + 1].get_text(" ", strip=True)
                    i += 1
                drops.append({'name': money_name, 'link': None, 'prob': prob_text})
            # Handle item drop
            elif data_source == "deja":
                # Try to get item name and link
                link_tag = div.find("a", title=True)
                obj_name = link_tag.get("title") if link_tag else div.get_text(" ", strip=True)
                obj_link = f"https://terraria.fandom.com{link_tag['href']}" if link_tag and link_tag.has_attr('href') and link_tag['href'].startswith("/") else None
                # Try to get probability from next div if it is also deja
                prob_text = "Desconocida"
                if i + 1 < len(drop_money_divs) and drop_money_divs[i + 1].get("data-source", "") == "deja":
                    prob_div = drop_money_divs[i + 1]
                    prob_text = prob_div.get_text(" ", strip=True)
                    i += 1
                drops.append({'name': obj_name, 'link': obj_link, 'prob': prob_text})
            i += 1

        if drops:
            drop_lines = []
            for d in drops:
                if d['link']:
                    drop_lines.append(f"[{d['name']}]({d['link']}) — **{d['prob']}**")
                else:
                    drop_lines.append(f"{d['name']} — **{d['prob']}**")
            embed.add_field(
                name="🎁 Objetos que deja y probabilidad",
                value="\n".join(drop_lines),
                inline=False
            )

    else:
        # Add purchase info
        if vendido_por:
            compra_info = ""
            compra_info += f"**Precio:** {precio_compra}\n" if precio_compra else ""
            compra_info += f"**Vendido por:** {vendido_por}\n" if vendido_por else ""
            embed.add_field(
                name="🛒 Compra",
                value=compra_info.strip() if compra_info else "Disponible para comprar.",
                inline=False
            )

        # Add found info
        if encontrado_en:
            encontrado_info = f"**Ubicación:** {encontrado_en}"
            embed.add_field(
                name="🔎 Encontrado en",
                value=encontrado_info,
                inline=False
            )

        # Add dropped by info
        if dropeado_por:
            dropped_text = "**Enemigos:**\n" + "\n".join(dropeado_por)
            if proba_dropeo:
                dropped_text += f"\n**Probabilidad:** {proba_dropeo}"
            embed.add_field(
                name="🎲 Dejado por enemigos",
                value=dropped_text,
                inline=False
            )

        # Add crafting info
        if embed_table['recipes']:
            for i, recipe in enumerate(embed_table['recipes']):
                ingredients_text = ""
                for ing in recipe:
                    # If 'quantity' is present and not 1, show it; if missing or 1, omit
                    qty = ing.get('quantity')

                    if qty is not None and str(qty) != "?":
                        ingredients_text += f"[{ing['name']}]({ing['link']}) x{qty}\n"
                    else:
                        ingredients_text += f"[{ing['name']}]({ing['link']})\n"

                if section_type == "Usos":
                    embed.add_field(
                        name=f"🧪 Uso {i + 1}: **{embed_table['result']['name']}**",
                        value=ingredients_text.strip(),
                        inline=False
                    )
                elif section_type in ["Creacion", "Creación"]:
                    embed.add_field(
                        name=f"🔨 Receta {i + 1}",
                        value=ingredients_text.strip(),
                        inline=False
                    )
                
            stations = embed_table['stations']
            unique_stations = {}
            for st in stations:
                link = st['link']
                name = st['name'].strip() if st['name'] else ""
                if link not in unique_stations:
                    unique_stations[link] = name if name else "Enlace directo"
                elif name:
                    unique_stations[link] = name
            if unique_stations:
                station_text = ""
                for link, name in unique_stations.items():
                    station_text += f"[{name}]({link})\n"
                station_text = station_text.strip()
            else:
                station_text = "No se encontraron estaciones."
            embed.add_field(
                name="🏗️ Estación de creación",
                value=station_text,
                inline=False
            )

        if not (precio_compra or encontrado_en or dropeado_por or embed_table['recipes']):
            embed.add_field(
                name="❓ ¿Cómo se obtiene?",
                value="No se encontró información sobre cómo obtener este objeto.",
                inline=False
            )        

    await ctx.send(embed=embed)

# @bot.command()
# async def mision(ctx, *, msg):
#     if not msg:
#         await ctx.send("❌ Por favor, proporciona el nombre de un objeto para la misión.")
#         return

#     # Buscar el objeto principal en la wiki y obtener su receta
#     item_name = msg.replace(' ', '_').capitalize()
#     url = f"{url_base}/{item_name}"
#     page = requests.get(url)
#     if page.status_code != 200:
#         await ctx.send("❌ No se encontró el objeto en la wiki de Terraria. Revisa el nombre y vuelve a intentarlo.")
#         return

#     soup = BeautifulSoup(page.content, 'html.parser')
#     content_div = soup.find('div', class_="mw-content-ltr mw-parser-output")
#     if not content_div:
#         await ctx.send("❌ No se pudo analizar la página del objeto.")
#         return

#     # Recursivamente obtener todos los ingredientes y cantidades (considerando todas las recetas)
#     def get_ingredients(item, qty_needed=1, visited=None):
#         if visited is None:
#             visited = set()
#         item_key = item.lower()
#         if item_key in visited:
#             return {}
#         visited.add(item_key)

#         # Buscar receta del objeto en su propia página
#         item_name = item.replace(' ', '_').capitalize()
#         url = f"{url_base}/{item_name}"
#         page = requests.get(url)
#         if page.status_code != 200:
#             return {item: qty_needed}
#         soup = BeautifulSoup(page.content, 'html.parser')
#         content_div = soup.find('div', class_="mw-content-ltr mw-parser-output")
#         if not content_div:
#             return {item: qty_needed}

#         embed_table = create_embed_table(str(content_div))
#         recipes = embed_table['recipes']
#         if not recipes:
#             return {item: qty_needed}

#         # Sumar ingredientes de todas las recetas posibles
#         all_ingredients = {}
#         for recipe in recipes:
#             recipe_ings = {}
#             for ing in recipe:
#                 ing_name = ing['name']
#                 ing_qty = int(ing.get('quantity', 1)) if str(ing.get('quantity', 1)).isdigit() else 1
#                 sub_ings = get_ingredients(ing_name, ing_qty * qty_needed, visited.copy())
#                 for k, v in sub_ings.items():
#                     recipe_ings[k] = recipe_ings.get(k, 0) + v
#             # Sumar los ingredientes de esta receta a los totales
#             for k, v in recipe_ings.items():
#                 all_ingredients[k] = max(all_ingredients.get(k, 0), v)
#         return all_ingredients

#     ingredients = get_ingredients(msg)
#     if not ingredients:
#         await ctx.send("No se encontraron ingredientes para este objeto.")
#         return

#     # Crear embed con lista de ingredientes (tipo checklist)
#     embed = discord.Embed(
#         title=f"📝 Misión: Crear {msg.capitalize()}",
#         description="Lista de materiales necesarios:",
#         color=discord.Color.blue()
#     )
#     checklist = ""
#     for ing, qty in ingredients.items():
#         checklist += f"☐ {ing} x{qty}\n"
#     embed.add_field(name="Materiales", value=checklist, inline=False)
#     await ctx.send(embed=embed)


@bot.command()
async def ayuda(ctx):
    embed = discord.Embed(
        title="Comandos disponibles",
        description="Aquí tienes una lista de comandos que puedes usar:",
        color=discord.Color.green()
    )
    embed.add_field(name="/saludar", value="Saluda al bot.", inline=False)
    embed.add_field(name="/asignar <rol>", value="Asigna un rol de Terraria. Opciones: " + ", ".join(roles_terraria.keys()), inline=False)
    embed.add_field(name="/quitar <rol>", value="Quita un rol de Terraria. Opciones: " + ", ".join(roles_terraria.keys()), inline=False)
    embed.add_field(name="/buscar <objeto>", value="Busca información de creación de un objeto en la wiki de Terraria.", inline=False)
    embed.add_field(name="/ayuda", value="Muestra este mensaje de ayuda.", inline=False)
    await ctx.send(embed=embed)


bot.run(token, log_handler=handler, log_level=logging.DEBUG)