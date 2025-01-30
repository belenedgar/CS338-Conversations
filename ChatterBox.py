#CREDIT: Richard Shwabe

import settings
import discord 
from discord.ext import commands
import utils
    
logger = settings.logging.getLogger("bot")

class SimpleView(discord.ui.View):
    
    foo : bool = None
    
    async def disable_all_items(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)
    
    async def on_timeout(self) -> None:
        await self.message.channel.send("Timedout")
        await self.disable_all_items()
    
    @discord.ui.button(label="Prompt", 
                       style=discord.ButtonStyle.success)
    async def hello(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Example prompt here")
        self.foo = True
        self.stop()
        
    @discord.ui.button(label="Feedback", 
                       style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Good or Bad?")
        self.foo = False
        self.stop()
        
def run():
    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    @bot.event 
    async def on_ready():
        await utils.load_videocmds(bot)

    @bot.event
    async def on_message(message):
        # Ignore bot messages to prevent infinite loops
        if message.author.bot:
            return

        #track who sent message
        user_id = message.author.id
        # Get message length
        message_length = len(message.content)
        # Get message timestamp
        timestamp = message.created_at  # This is in UTC time

        # Send a response with the message length and timestamp
        await message.channel.send(f"Your message is {message_length} characters long. Sent at {timestamp} UTC.")

        if message_length < 20:
            await short_message(message.channel)


        # Ensure other bot commands still work
        await bot.process_commands(message)
    
    @bot.command()
    async def button(ctx): #name of user command
        view = SimpleView(timeout=50)
        # button = discord.ui.Button(label="Click me")
        # view.add_item(button)
        
        message = await ctx.send(view=view)
        view.message = message
        
        await view.wait()
        await view.disable_all_items()
        
        if view.foo is None:
            logger.error("Timeout")
            
        elif view.foo is True:
            logger.error("Ok")
            
        else:
            logger.error("cancel")

    @bot.command() #can later change this to be a call to OpenAI
    async def short_message(channel):  # Modified to accept the channel as a parameter
        await channel.send("You sent a short message! Try adding more details.")
        
        
        
    bot.run(settings.DISCORD_API_SECRET, root_logger=True)

if __name__ == "__main__":
    run()

