#CREDIT: Richard Shwabe
import settings
import discord 
from discord.ext import commands
import utils
from openai import OpenAI
from openai_func import get_prompt
# for timeout errors
import asyncio
from textblob import TextBlob
import asyncio 
from datetime import datetime, timezone

#GLOBALS 
logger = settings.logging.getLogger("bot")
client = OpenAI(api_key=settings.OPENAI_API_TOKEN)
#Tracks if a suggestion was just sent using the !button feature
promptSent = False
#keeps track of active threads in discord guild
threads = {}
#Keeps track of most recent feedback from user from !button
last_feedback = ""

class SimpleView(discord.ui.View):
    #added an init function to take in the bot_client in order to receive + respond to user messages after button presses
    def __init__(self,bot_client,timeout):
        super().__init__() # ensures parent class discord.ui.View is initialized before adding custom init
        self.bot_client = bot_client # store bot_client instance
        self.timeout = timeout
        self.foo= None
        
    #foo : bool = None # moved to init fun
    async def disable_all_items(self):
        for item in self.children:
            item.disabled = True
        await self.message.edit(view=self)
    
    async def on_timeout(self) -> None:
        await self.message.channel.send("Timedout")
        await self.disable_all_items()
    

    @discord.ui.button(label="Get Suggestion", 
                       style=discord.ButtonStyle.primary)
    async def hello(self, interaction: discord.Interaction, button: discord.ui.Button):
        global threads
        threads[interaction.user.id] = interaction.channel

        # prompt user to explain who they are talking to
        await interaction.response.send_message("Describe who you are trying to start a conversation with. The more specific you are, the better I can help you!")
        #function to ensure the message came from the intended user + the correct channel
        def check(message):
            return message.author == interaction.user and message.channel == interaction.channel
        try:
            #save user's response and generate a prompt based on it 
            user_response = await self.bot_client.wait_for("message",check = check, timeout = 50.0) # timeout is set to 50 sec
            global last_feedback
            input_text = user_response.content
            if last_feedback != "":
                    feedback="TAKE INTO CONSIDERATION THIS feedback WHEN MAKING THE TEXT PROMPT:"+last_feedback
                    # last_feedback=""
            else:
                feedback = ""
            
            prompt = get_prompt(input_text, client, 500,feedback=feedback,button_pressed=True)
            global promptSent
            promptSent = True
            # print("prompt sent = ",promptSent)
            await interaction.followup.send("Here are some suggestions to start up the conversation: \n"+prompt)
            # print("prompt sent = ",promptSent)
            


        except asyncio.TimeoutError:
          #IF USER TAKES TOO LONG TO RESPOND, TIME OUT
          await interaction.followup.send("Button Response Timed out")    
        self.foo = True
        self.stop()
        
    @discord.ui.button(label="Give Feedback", 
                       style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
    
        await interaction.response.send_message("Please enter your feedback on BanterBuddy here. The more specific you are, the better I can help you!")
        # Take in user input 
        def check(message):
            return message.author == interaction.user and message.channel == interaction.channel
        try:
            #save user's response and generate a prompt based on it 
            user_feedback = await self.bot_client.wait_for("message",check = check, timeout = 50.0) # timeout is set to 50 sec
            blob = TextBlob(user_feedback.content)
            sentiment = blob.sentiment.polarity  # Sentiment value between -1 (negative) and 1 (positive)
            # Send a response based on sentiment analysis result

            if sentiment > 0:
                #This message is positive!
                await interaction.followup.send("Thank you for your feedback! We are glad you are enjoying using BanterBuddy and will use your feedback to make sure you continue to enjoy using our system :) ")
            elif sentiment < 0:
                #negative!
                await interaction.followup.send("Im sorry to hear that, your feedback will be used to improve our system and ensure you have a better experience in the future")
            else:
               #neutral!
               await interaction.followup.send("Your feedback will be used to improve your experience in the future with BanterBuddy")
             ##FEEDBACK INCORPORATION
            global last_feedback
            last_feedback = user_feedback.content
            # print(last_feedback)
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
    #TO-DO: need to add more factors from google doc(timestamp, attaching userid to messages)
    return points



async def create_private_threads(bot):
    channel_id = 1333890688357499003  # Hardcorded to user's(our) main channel ID, will not work for multiple channels
    channel = bot.get_channel(channel_id)

    if channel is None:
        print(f"Error: Channel with ID {channel_id} not found.")
        return

    print("Starting create_private_threads...")
    for guild in bot.guilds:
        for member in guild.members: #loops through members, so doesn't move on until user says yes/no or it times out
            # print(f"Processing guild: {guild.name}")
            # print(f"Guild Member Count: {len(guild.members)}")
            if not member.bot:
                print(f" Attempting thread for: {member.name}")
                try:
                    thread = await channel.create_thread(
                        name=f"BanterBuddy - {member.display_name}",
                        type=discord.ChannelType.private_thread
                    )
                    await thread.add_user(member)
                    #Greet Users, explain what BanterBuddy is + how to utilize his functionalities
                    await thread.send("Hello, I'm BanterBuddy, a conversational assistant! My job is to keep up with the chat in the main channel so I can detect when the conversation is dying down. When I start to see the conversation lull, I'll step in by sending you suggestions on how you can keep the conversation going based on the messages in the main channel. You can also request my help on-demand by sending **!button** to our private thread and I'll send you suggestions for what to say.")
                   
                    threads[member.id] = thread
                    print("done")
                except discord.Forbidden:
                    print(f"Cannot create thread for {member.name} in {guild.name}")
                except Exception as e:
                    print(f"Error creating thread for {member.name}: {e}")


def run():
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    ("notified all members")
    
    last_message_time = {}
    channel_data = {}
    #check if last message was sent an hour ago
    GAP_THRESHOLD = 3600
    #keep track of messages in channel
    messages = []
    global threads
    #Track reason for suggestion being sent
    lull_type = 0

    bot = commands.Bot(command_prefix="!", intents=intents)

    #resets everything necessary after sending a suggestion to the user
    def clear_everything(channel_id):
        global promptSent
        nonlocal lull_type
        messages.clear()
        #reset all params across channels
        for id in channel_data.keys():
            channel_data[id]["threshold"] = 0
            channel_data[id]["m_count"] = 0
            channel_data[channel_id]["point_added"] = False
            print("reset",channel_id,"to false")

        # print("reset threshold and m count")
        last_message_time.clear()
        lull_type = 0
        promptSent = False
        #clears messages array to only track relevant messages from chat
        messages.clear()
        # Reset threshold and message count
        channel_data[channel_id]["threshold"] = 0
        channel_data[channel_id]["m_count"] = 0

    """
    for timestamp functionality. an async background function to periodically check each channel for inactivity
    """
    async def inactivity_checker(channel,channel_id): 
        nonlocal lull_type
        while True: 
                
            await asyncio.sleep(10) #check every 10 secs
            #if message.author.bot: 
            #return 

            #if button was pressed for a suggestion, reset everything (thresholds,messages,etc)
            global promptSent
            if promptSent == True:
                # lull_type = 0
                clear_everything(channel_id)

            
            if channel_id in last_message_time and channel.type != discord.ChannelType.private_thread: 
                current_time = datetime.now(timezone.utc)
                gap_seconds = (current_time - last_message_time[channel_id]).total_seconds()
                #check if last message sent was an hour ago 
                if gap_seconds > GAP_THRESHOLD and not channel_data[channel_id].get("point_added", False):
                    #if yes, add a point
                    channel_data[channel_id]["threshold"] += 1
                    lull_type += 1
                    # print("Lull type: ", lull_type)
                    # print(f"[Auto-check] Added 1 point for inactivity in channel {channel_id} (gap: {gap_seconds} seconds)")
                    m_count = channel_data[channel_id]["m_count"]
                    threshold = channel_data[channel_id]["threshold"]
                    print(f"Channel {channel_id}: m_count: {m_count}, threshold: {threshold}")
                    channel_data[channel_id]["point_added"] = True   #update last message time to avoid adding points repeatedly 
                    if channel_data[channel_id]["threshold"] > 4:
                        #check if user already has separate private channel and set thread to that
                        id = 527169750028255242#int(messages[-1]['user_id'])
                        print("User ID:", id, "\n")
                        if threads.get(id):
                            print("user_id already in threads\n")
                            thread = threads[id]
                        else:
                            #otherwise create new private thread
                            print("creating new thread...\n")
                            thread = await channel.create_thread(
                                name = f"{id}'s Private Thread",
                                type=discord.ChannelType.private_thread
                                
                            )
                            print("created thread\n")
                            threads[id] = thread
                            print("Updated Threads:", threads)
                            user_to_invite = bot.get_user(id)
                            await thread.add_user(user_to_invite)
                            # print("Adding user to thread\n")
                        prompt = get_prompt(messages, client, 500)
                        if lull_type > 0:
                            # print("Lull due to inactivity")
                            await thread.send("It looks like the flow of conversation is slowing down, try these suggestions to get the conversation back up and running: " + prompt)
                        else:
                            # print("Lull due to message content")
                            await thread.send("Here are some suggestions to start some more meaningful conversations: " + prompt)
                        promptSent = True
                        clear_everything(channel_id)

    #buzzwords to look for in messages
    buzzwords = {"k", "mhm", "sure", "yea", "true", "sounds good", "sg", "oh", "wow", "lmao", "no",
             "yes", "thats crazy", "thats cool", "yup", "gtg", "lol", "cool", "lit", "bet", "true", "gotcha", "facts",
             "ok", "okay", "yeah", "yup", "chill", "solid", "sick", "dope", "smh", "dead", "period", "periodt", "good", "fine", "interesting"}
    
    
    @bot.event 
    async def on_ready():
        await utils.load_videocmds(bot)
        await create_private_threads(bot) #when bot starts running-- sends message to each member

    @bot.event
    async def on_message(message):
        nonlocal lull_type
        global promptSent
        nonlocal lull_type
        
        # Ignore bot messages to prevent infinite loops
        if message.author.bot:
            return
        
        channel_id = message.channel.id  # Get the channel ID
        # add channel_id to channel_data if nto already there
        if channel_id not in channel_data and message.channel.type != discord.ChannelType.private_thread: #for a specific channel keeps track of "lull data"
            channel_data[channel_id] = {"m_count": 0, "threshold": 0}

            bot.loop.create_task(inactivity_checker(message.channel,channel_id))
      
        #ignore messages from private threads
        if message.channel.type == discord.ChannelType.private_thread:
            await bot.process_commands(message)
            # print("NOT TRACKING MESSAGES FROM PRIVATE THREADS")
            return
        message.content = message.content.lower()

        #track who sent messages
        user_id = message.author.id
        # print(user_id)
    
        current_time = message.created_at  
        # set last_message_time to current_time
        last_message_time[channel_id] = current_time 
        channel_data[channel_id]["point_added"] = False 

        await bot.process_commands(message)

        if message.content != "!button" and message.channel.type != discord.ChannelType.private_thread:
            #NOTE channel_id was previoously not being stored correctly
            messages.append({'message': message.content, 'user_id': str(user_id), 'channel_id': channel_id})

        # #if message was NOT sent in private thread, check if we need to send a prompt
        # updating "points"
        channel_data[channel_id]["m_count"] += 1
        lull_result = lull_algorithm(message.content, buzzwords) #call helper function
        channel_data[channel_id]["threshold"] += lull_result
        #keep track of main reason for lull detection going off
        if lull_result:
                lull_type -= 1

        m_count = channel_data[channel_id]["m_count"]
        threshold = channel_data[channel_id]["threshold"]

        # log to keep track of current message count and threshold
        # print(f"Channel {channel_id}: m_count: {m_count}, threshold: {threshold}")
        global last_feedback
        ## ------Oh No System:-----(consecutive messages)
        if (len(messages) >= 3):
            
            #get last three users and channels in message array
            last_three_users = [message['user_id'] for message in messages[-3:]]
            last_three_channels = [message['channel_id'] for message in messages[-3:]]
            #check if the users and channels are equal
            if (len(set(last_three_users)) == 1 and len(set(last_three_channels)) == 1):
                if last_feedback != "":
                    feedback="TAKE INTO CONSIDERATION THIS feedback WHEN MAKING THE TEXT PROMPT:"+last_feedback
                    # last_feedback=""
                else:
                    feedback = ""
                prompt = get_prompt(messages,client,500, 'oh no', feedback=feedback)
                # Hard code to send to Admin [ENTER USER'S DISCORD USER_ID HERE]
                user_id = 527169750028255242
                #check if user already has separate private channel and set thread to that
                if user_id in threads:
                    thread = threads[user_id]
                else:
                    #otherwise create new private thread
                    user = bot.get_user(527169750028255242)
                    thread = await message.channel.create_thread(
                        name = f"{user.display_name}'s Private Thread",
                        type=discord.ChannelType.private_thread
                    )
                    threads[user_id] = thread
                    user_to_invite = user
                    await thread.add_user(user_to_invite)
                print(threads)
                #send prompt to user's individual thread
                await thread.send("Here are some suggestions to encourage more back-and-forth engagement: " +prompt)
                #clear all
                clear_everything(channel_id)
                print(channel_data)
                return

        # ----Lull Point System-----
        if threshold > 4:
          #Add last feedback from user into get_prompt
            if last_feedback != "":
                    feedback="TAKE INTO CONSIDERATION THIS feedback WHEN MAKING THE TEXT PROMPT:"+last_feedback
                    # last_feedback=""
            else:
                feedback = ""
            #check if user already has separate private channel and set thread to that
            user_id = 527169750028255242 # Send to Admin
            if user_id in threads:
                thread = threads[user_id]
            else:
                #otherwise create new private thread
                user = bot.get_user(527169750028255242)
                thread = await message.channel.create_thread(
                    name = f"{user.display_name}'s Private Thread",
                    type=discord.ChannelType.private_thread
                    
                )
                threads[user_id] = thread
                user_to_invite = user # bot.get_user(527169750028255242)
                await thread.add_user(user_to_invite)
            print(threads)
            #send prompt to user's individual thread
            if lull_type > 0:
                # print("Lull due to inactivity")
                prompt = get_prompt(messages, client, 500, 'inactivity', feedback=feedback)
                await thread.send("It looks like the flow of conversation is slowing down, try these suggestions to get the conversation back up and running: " + prompt)
            else:
                # print("Lull due to message content")
                prompt = get_prompt(messages, client, 500, 'message content', feedback=feedback)
                await thread.send("Here are some suggestions to start some more meaningful conversations: " + prompt)
            #reset everything after sending suggestion
            clear_everything(channel_id)
        #if 10 messages have been sent without intervention, convo is going well! reset thresholds
        if m_count == 10:
            channel_data[channel_id]["threshold"] = 0
            channel_data[channel_id]["m_count"] = 0
            lull_type = 0
        # Ensure other bot commands still work
        await bot.process_commands(message)
    
    @bot.command()
    #looks for when user presses button
    async def button(ctx): #name of user command
        #initialize buttons with init function defined in class
        view = SimpleView(bot_client=bot,timeout=50)
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
    
    @bot.command() 
    async def short_message(channel):
        await channel.send("You sent a short message! Try adding more details.")
         
        
    bot.run(settings.DISCORD_API_SECRET, root_logger=True)

if __name__ == "__main__":
    run()