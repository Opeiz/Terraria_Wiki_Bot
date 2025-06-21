# Terraria Wiki Bot

Terraria Wiki Bot es un bot de Discord que te permite buscar información sobre objetos, accesorios, armas y más directamente desde la Wiki de Terraria.  
Actualmente, el bot funciona mejor con accesorios, armas, objetos y algunos otros tipos de ítems.

> **Nota:** Por ahora, el bot solo funciona en español. Próximamente estará disponible en inglés.

## Comandos Disponibles

| Comando                | Descripción                                                                                  |
|------------------------|----------------------------------------------------------------------------------------------|
| `/hello`               | Saluda al bot.                                                                               |
| `/asignar <rol>`       | Asigna un rol de Terraria. Opciones: mago, invocador, tanque, distancia.                    |
| `/quitar <rol>`        | Quita un rol de Terraria. Opciones: mago, invocador, tanque, distancia.                     |
| `/buscar <objeto>`     | Busca información de creación de un objeto en la wiki de Terraria.                           |
| `/ayuda`               | Muestra el mensaje de ayuda con todos los comandos disponibles.                              |

## Preconfiguración

1. Ingresa a la [página de desarrolladores de Discord](https://discord.com/developers) y accede con tu cuenta.
2. Haz clic en **"New Application"** para crear una nueva aplicación.
3. Asigna un nombre a tu bot y guarda los cambios.
5. Activa las opciones **"Message Content Intent"** y **"Server Members Intent"** en la configuración de privilegios del bot.  
6. Asegúrate de que la opción **"Public Bot"** esté activada para que otros puedan invitar el bot a sus servidores.  
7. Copia el **Token** del bot, lo necesitarás para configurar el archivo `.env` más adelante.
8. Una vez que hayas copiado el token, crea un archivo llamado `.env` en la raíz del proyecto y escribe la siguiente línea (reemplazando `tu_token` por el token real de tu bot):

    ```
    DISCORD_TOKEN=tu_token
    ```

    > ⚠️ **Importante:** ¡No compartas tu token con nadie! Es la contraseña que permite acceder y controlar tu bot.

## Configuración de permisos (OAuth2)

1. En el panel de tu aplicación de Discord, ve a la sección **OAuth2 URL Generator**.
2. Marca los siguientes scopes:
    - `bot`
3. En la sección **Bot Permissions**, selecciona los permisos recomendados para el bot, por ejemplo:
    - `Manage Roles`
    - `View Channels`
    - `Send Messages`
    - `Create Public Threads`
    - `Send Messages in Threads`
    - `Manage Messages`
    - `Manage Threads`
    - `Embed Links`
    - `Attach Files`
    - `Read Message History`
    - `Use External Emojis`
    - `Add Reactions`
    - `Create Polls`
4. Copia la URL generada y pégala en tu navegador para invitar el bot a tu servidor de Discord.

## Puesta en marcha

¡Listo! Ahora solo tienes que agregar el bot a tu servidor de Discord usando la URL generada y lanzar el código.  
Recuerda: es necesario ejecutar el bot para que funcione correctamente en tu servidor.

## Instalación

1. Clona el repositorio:
   ```sh
   git clone https://github.com/tu-usuario/Terraria_Wiki_Bot.git
   cd Terraria_Wiki_Bot
   ```
2. Instala las dependencias:
   ```sh
   pip install -r requirements.txt
   ```
3. Ejecuta el bot:
   ```sh
   python main.py
   ```
