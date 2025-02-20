#CREDIT: Richard Shwabe
# TODO : give bot permission to create threads
import settings
import discord 
from discord.ext import commands
import utils
from openai import OpenAI
from openai_func import get_prompt
# for timeout errors
import asyncio
from textblob import TextBlob
    
logger = settings.logging.getLogger("bot")
client = OpenAI(api_key="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")


class SimpleView(discord.ui.View):
    #added an init function to take in the bot_client in order to receive + respond to user messages after button presses
    def __init__(self,bot_client,timeout):
        super().__init__() # ensures parent class discord.ui.View is initialized before adding custom init
        self.bot_client = bot_client # store bot_client instance
        self.timeout = timeout
        self.foo= None
        #TODO: might need to add self.threads here or change button function approach to send messages to user in private thread

    #foo : bool = None # moved to init func
    
    async def disable_all_items(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)
    
    async def on_timeout(self) -> None:
        await self.message.channel.send("Timedout")
        await self.disable_all_items()
    

    @discord.ui.button(label="Prompt", 
                       style=discord.ButtonStyle.primary)
    async def hello(self, interaction: discord.Interaction, button: discord.ui.Button):
        #TODO: MAKE SURE THE RESPONSE TO BUTTON DOES NOT GET ADDED TO DATA

        # prompt user to topics they like/ who they are talking to
        await interaction.response.send_message("Describe who you are trying to start a conversation with")
        #function to ensure the message came from the intended user + the correct channel
        def check(message):
            return message.author == interaction.user and message.channel == interaction.channel
        try:
            #save user's response and generate a prompt based on it 
            user_response = await self.bot_client.wait_for("message",check = check, timeout = 50.0) # timeout is set to 50 sec
            prompt = get_prompt(user_response.content, client, 100,button_pressed=True)
            #TODO : ADD CODE TO MESSAGE USER IN SEPARATE CHAT
            #send user prompts
            await interaction.followup.send("Here are some prompts to start up the conversation: \n"+prompt)

        except asyncio.TimeoutError:
          #IF USER TAKES TOO LONG TO RESPOND, TIME OUT
          #TODO : ADD CODE TO MESSAGE USER IN SEPARATE CHAT
          await interaction.followup.send("Button Response Timed out")    
        self.foo = True
        self.stop()
        
    @discord.ui.button(label="Feedback", 
                       style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        #TODO: Actually use feedback to improve system

        await interaction.response.send_message("Please enter your feedback on ChatterBox here:")
        #NEW: Take in user input 
        def check(message):
            return message.author == interaction.user and message.channel == interaction.channel
        try:
            #save user's response and generate a prompt based on it 
            user_feedback = await self.bot_client.wait_for("message",check = check, timeout = 50.0) # timeout is set to 50 sec
            blob = TextBlob(user_feedback.content)
            sentiment = blob.sentiment.polarity  # Sentiment value between -1 (negative) and 1 (positive)
            # Send a response with sentiment analysis result

            #TODO : ADD CODE TO MESSAGE USER IN SEPARATE CHAT
            if sentiment > 0:
                #This message is positive!

                await interaction.followup.send("Thank you for your feedback! We are glad you are enjoying using ChatterBox and will use your feedback to make sure you continue to enjoy using our system :) ")
                
            elif sentiment < 0:
                #negative!
                await interaction.followup.send("Im sorry to hear that, your feedback will be used to improve our system and ensure you have a better experience in the future")
            else:
               #neutral!
               await interaction.followup.send("Your feedback will be used to improve your experience in the future with ChatterBox")

        except asyncio.TimeoutError:
          #IF USER TAKES TOO LONG TO RESPOND, TIME OUT
          await interaction.followup.send("Button Response Timed out")   

        self.foo = False
        self.stop()

def lull_algorithm(message_content, buzzwords): #helper function for detecting lulls
    points = 0
    if message_content in buzzwords and len(message_content.split()) == 1: #specific low engagement response
        points += 3
    elif len(message_content.split()) < 5: #word count
        points += 1
    #TO-DO: need to add more factors from google doc
    return points


def run():
    intents = discord.Intents.default()
    intents.message_content = True
    
    data = []
    threads={}
    bot = commands.Bot(command_prefix="!", intents=intents)

    channel_data = {}
    buzzwords = {"k", "mhm", "sure", "yea", "sounds good", "sg", "oh", "wow", "lmao", "no",
             "yes", "thats crazy", "thats cool", "yup", "gtg"}
    
    @bot.event 
    async def on_ready():
        await utils.load_videocmds(bot)

    @bot.event
    async def on_message(message):
        channel_id = message.channel.id  # Get the channel ID

        if channel_id not in channel_data: #for a specific channel keeps track of "lull data"
            channel_data[channel_id] = {"m_count": 0, "threshold": 0}

        # Ignore bot messages to prevent infinite loops
        if message.author.bot:
            return
        #TODO : ADD CODE TO MESSAGE USER IN SEPARATE CHAT
        message.content = message.content.lower()
        #TODO: Update this to not track responses to the !button call
        if message.content != "!button":
            data.append(message.content)
        print(data)


        #track who sent messages
        user_id = message.author.id
        print(user_id)
        # Get message length
        message_length = len(message.content)
        # Get message timestamp
        timestamp = message.created_at  # This is in UTC time
        # await message.channel.send(f"Your message is {message_length} characters long. Sent at {timestamp} UTC." )
            # will be used for indicators of conversation lulls later ^^^

        # await message.channel.send(f"ALso here is your data: {data}")
        
        # updating "points"
        channel_data[channel_id]["m_count"] += 1
        channel_data[channel_id]["threshold"] += lull_algorithm(message.content, buzzwords) #call helper function

        m_count = channel_data[channel_id]["m_count"]
        threshold = channel_data[channel_id]["threshold"]

        # log to keep track of current message count and threshold
        print(f"Channel {channel_id}: m_count: {m_count}, threshold: {threshold}")
            
        #conversation lull threshold detected
        if threshold > 4:
            #check if timestamps are valid ?
                #maybe make a front end site with toggles to turn certain features on/off before running bot (only if we run out of stuff to add/have time lol)
            prompt = get_prompt(data, client, 50)
            #check if user already has separate private channel and set thread to that
            if user_id in threads:
                thread = threads[user_id]
            else:
                #otherwise create new private thread
                thread = await message.channel.create_thread(
                    name = f"{message.author}'s Private Thread",
                    type=discord.ChannelType.private_thread
                    
                )
                threads[user_id] = thread
                user_to_invite = message.author
                await thread.add_user(user_to_invite)
            print(threads)
            #send prompt to user's individual thread
            await thread.send("Here are some prompts for conversation based on messages in the chat:\n"+ prompt)
            
            #we should reset data here to be empty array again so we arent passing irrelevant messages to openai
            data.clear()
            # Reset threshold and message count
            channel_data[channel_id]["threshold"] = 0
            channel_data[channel_id]["m_count"] = 0
            # threshold = 0
            # m_count = 0

        if m_count == 10:
            channel_data[channel_id]["threshold"] = 0
            channel_data[channel_id]["m_count"] = 0
        

        # Ensure other bot commands still work
        await bot.process_commands(message)
    
    @bot.command()
    #looks for when user presses button
    async def button(ctx): #name of user command
        #initialize buttons with init function defined in class
        view = SimpleView(bot_client=bot,timeout=50)
        #NOTE:   insert prompt call here later for when user asks for prompt
        # TODO: maybe move prompt sending functionality to here
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
    async def short_message(channel):
        await channel.send("You sent a short message! Try adding more details.")
         
        
    bot.run(settings.DISCORD_API_SECRET, root_logger=True)

if __name__ == "__main__":
    run()

