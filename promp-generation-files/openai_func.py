
from openai import OpenAI

def create_openai_input(message_data,word_limit):

    """
    Helper function to create question to send thru OpenAI API incorporating message_data
    word_limit = how many words should the returned prompt be (int)?
    """

    ## convert message data from list to string
    if message_data == None or message_data == "":
        #can change to be more specific later
        input = "Create a prompt or topic to start a converation with friends"
        return input
    else:
        return f'Create a prompt/topic to keep the conversation going with sender for the user in {word_limit} words or less building off of the following messages from the chat: {message_data}'

def get_prompt(message_data,client,max_tokens):

    """
    Uses OpenAI API to generate a prompt based on message_data
    Outputs prompt as string
    Takes in message_data (need to turn this into a str), client(connection to OpenAI), and max_tokens to use per call
    """
    # Do some data cleaning before sending as prompt here
    # ensure message data is in string format
    # Clarify which messages are from sender and which are from user
    
    #call create_openai_input()
    input = create_openai_input(message_data,20)
    print("input",input)
    if input == None or input == "":
        print("Unable to retrieve input based on data")
        return
  
    #send prompt to chatgpt with call
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        store = True,
        max_tokens = max_tokens,
        messages = [
            
            {"role": "user", "content": input} 
        ]
    )
    content = completion.choices[0].message.content
    return content

#set up client for openai
client = OpenAI(api_key="Enter token here(in google doc)")

print(get_prompt('["Sender:Hey guys hows it going","Sender:I have so much homework :(( ","Sender:I am hungry"]',client,100))
