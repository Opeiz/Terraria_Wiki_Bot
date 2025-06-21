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

url_base = 'https://terraria.fandom.com/es/wiki'

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
async def hello(ctx):
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

    type_of_table = soup.find('h2', class_="mw-headline" )
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
    if embed_table['recipes']:
        status.append("🔨 Se puede fabricar")
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
        title=f"{item_name}",
        description=f"{' | '.join(status)}\n\n{description}",
        color=discord.Color.orange()
    ).set_thumbnail(url=get_item_icon(str(content_div)))


    if tipo_de_elemento == "Enemigo" or tipo_de_elemento == "Jefe":
        
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
        drop_section = aside.find_all(attrs={'data-source': 'deja'})
        for drop_div in drop_section:
            # Buscar el enlace y el nombre del objeto
            link_tag = drop_div.find('a')
            obj_name = link_tag.get_text(strip=True) if link_tag else drop_div.get_text(strip=True)
            obj_link = f"https://terraria.fandom.com{link_tag['href']}" if link_tag and link_tag.has_attr('href') else None
            # Buscar la probabilidad en el siguiente div hermano
            prob_text = ""
            next_div = drop_div.find_next_sibling('div')
            if next_div:
                prob_match = re.search(r'(\d+(\.\d+)?%)', next_div.get_text())
                if prob_match:
                    prob_text = prob_match.group(1)
                else:
                    prob_text = next_div.get_text(strip=True)
            else:
                prob_text = "Desconocida"

            # Formatear
            if obj_link:
                drops.append({'name': obj_name, 'link': obj_link, 'prob': prob_text if prob_text else "Desconocida"})
            else:
                drops.append({'name': obj_name, 'link': None, 'prob': prob_text if prob_text else "Desconocida"})

        if drops:
            drop_lines = []
            for d in drops:
                if d['link']:
                    drop_lines.append(f"[{d['name']}]({d['link']}) — **{d['prob']}**")
                
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
                    if qty is not None and str(qty) != "1":
                        ingredients_text += f"[{ing['name']}]({ing['link']}) x{qty}\n"
                    else:
                        ingredients_text += f"[{ing['name']}]({ing['link']})\n"
                embed.add_field(
                    name=f"🗎 Receta {i+1}",
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

@bot.command()
async def ayuda(ctx):
    embed = discord.Embed(
        title="Comandos disponibles",
        description="Aquí tienes una lista de comandos que puedes usar:",
        color=discord.Color.green()
    )
    embed.add_field(name="/hello", value="Saluda al bot.", inline=False)
    embed.add_field(name="/asignar <rol>", value="Asigna un rol de Terraria. Opciones: " + ", ".join(roles_terraria.keys()), inline=False)
    embed.add_field(name="/quitar <rol>", value="Quita un rol de Terraria. Opciones: " + ", ".join(roles_terraria.keys()), inline=False)
    embed.add_field(name="/buscar <objeto>", value="Busca información de creación de un objeto en la wiki de Terraria.", inline=False)
    embed.add_field(name="/ayuda", value="Muestra este mensaje de ayuda.", inline=False)
    await ctx.send(embed=embed)


bot.run(token, log_handler=handler, log_level=logging.DEBUG)