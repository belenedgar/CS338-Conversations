
from openai import OpenAI

def create_openai_input(message_data,word_limit,button_pressed=False):

    """ Helper function to create question to send thru OpenAI API incorporating message_data
    Args:
        message_data : string or array of strings of context to pass into OpenAI API to generate prompt
        word_limit : how many words should the returned prompt be (int)?
        button_pressed : Optional param preset to False, can be set to True to return prompt correlating to button press (bool)
    Returns: 
        question to pass into openai call (str)

    """

    ## convert message data from list to string
    if button_pressed:
        input = "Create a prompt or topic to start a converation with a person/people with the following description: "+message_data
        return input
    if message_data == None or message_data == "" or message_data == []:
        #can change to be more specific later
        input = "Create a prompt or topic to start a converation with friends"
        return input
    else:
        return f'Create a prompt/topic to keep the conversation going with sender(s) for the user in {word_limit} words or less building off of the following messages from the chat (DONT GIVE IT TO ME AS A MESSAGE,put in suggestion format): {message_data}'

def get_prompt(message_data,client,max_tokens,button_pressed=False):

    """ Uses OpenAI API to generate a prompt based on message_data
    Args:
        Takes in message_data (need to turn this into a str), client(connection to OpenAI), and max_tokens to use per call
        Also optionally takes in button_pressed bool 
    Returns:
        Outputs prompt as string
    """
    # Do some data cleaning before sending as prompt here
    # ensure message data is in string format
    # Clarify which messages are from sender and which are from user
    
    #call create_openai_input()
    if button_pressed:
        input = create_openai_input(message_data,50,button_pressed=True)
    else:
        input = create_openai_input(message_data,50)
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
client = OpenAI(api_key="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")

# testing
#print(get_prompt('["Sender:Hey guys hows it going","Sender:I have so much homework :(( ","Sender:I am hungry"]',client,100))
