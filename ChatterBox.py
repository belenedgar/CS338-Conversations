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
    
    @bot.command()
    async def button(ctx):
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
        
        
        
    bot.run(settings.DISCORD_API_SECRET, root_logger=True)

if __name__ == "__main__":
    run()



# import discord
# from discord.ext import commands

# # Set up the bot with a command prefix
# bot = commands.Bot(command_prefix="!")

# # Event when the bot is ready
# @bot.event
# async def on_ready():
#     print(f'Logged in as {bot.user}')

# # Command to display a message
# @bot.command()
# async def hello(ctx):
#     await ctx.send('Hello, world!')

# # Run the bot
# bot.run('MTMzMzg5NjIxNzUyNDA0MzkyNw.GtTZKx.8hwyUS_rHIemH7WXl0pf8A31Ihw6qk2aUmFpXs')
