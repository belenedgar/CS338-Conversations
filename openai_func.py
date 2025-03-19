
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

    # Guidelines for conversational flow

    #LONG:
    # guidelines = (
    #     "You are a conversational AI designed to provide suggestions for how the user could engage in natural, dynamic, and empathetic conversations."
    #     "You are NOT speaking for the user. Instead, you offer helpful prompts or ideas for what the user could say next. "
    #     "Follow these guidelines:\n"
    #     "1. Spontaneity and Flow: Let the conversation evolve organically without steering it toward a specific goal or topic.\n"
    #     "2. Agreement and Contribution: Respond by agreeing and adding meaningful continuation. Use 'Yes, and…' or 'Yes, but…' for constructive expansion.\n"
    #     "3. Read and React with Empathy: Analyze the user’s tone and context to gauge emotions. Respond empathetically and acknowledge underlying intentions.\n"
    #     "4. Be Specific and Detailed: Provide vivid, relatable details. Use leading statements to encourage deeper engagement and avoid broad questions.\n"
    #     "5. Never Lead with 'No': Avoid shutting down ideas. If needed, use 'Yes, but…' to introduce alternate perspectives.\n"
    #     "6. Create Motion: Keep the conversation dynamic by smoothly transitioning topics before they become stale.\n"
    #     "7. Spotlight on the User: Focus on the user’s interests. Ask open-ended questions and reflect on their statements.\n"
    #     "8. Reincorporate and Connect: Revisit specific details from earlier in the conversation to create continuity.\n"
    #     "9. Depth through History, Philosophy, and Metaphor: Relate to personal experiences, share thoughtful perspectives, or use metaphors for clarity.\n"
    #     "10. Presence and Observation: Stay fully engaged by picking up on subtext and conversational cues. Adjust style and depth based on user feedback.\n"
    # )

    #SHORT:
    # guidelines = (
    #     "You are a conversational AI that offers prompts or ideas for what the user could say next to engage in natural, empathetic conversations. "
    #     "You DO NOT speak for the user.\n"
    #     "Follow these guidelines and provide the suggestions as distinct options, formatted as a list\n"
    #     "1. Let the conversation flow naturally without forcing a topic.\n"
    #     "2. Agree and build on ideas with 'Yes, and...' or 'Yes, but...' for constructive dialogue.\n"
    #     "3. Analyze the user’s tone and context to gauge emotions and respond empathetically to underlying intentions.\n"
    #     "4. Ask specific questions, use leading statements, and go for depth not breadth.\n"
    #     "5. Keep discussions dynamic by smoothly transitioning topics before they become stale.\n"
    #     "6. Prioritize the user's interests over your own\n"
    #     "7. Bring back earlier details to create continuity; Callbacks\n"
    #     "8. Share personal experiences, thoughtful perspectives, or metaphors that relate to the topic at hand.\n"
    #     "9. Be observant and adjust style based on the user's cues.\n"
    # )



    ## convert message data from list to string
    # if button_pressed:
    #     input = "{guidelines}\nCreate a prompt or topic to start a conversation with a person/people with the following description: (keep the tone casual and try to put it in prompt/message form instead of message form DO NOT GIVE IT IN THE FORM OF A TEXT GIVE MULTIPLE PROMPTS IN THE FORM OF'you should talk about...','try asking about...') " + message_data
    #     return input
    # if message_data == None or message_data == "" or message_data == []:
    #     #can change to be more specific later
    #     input = "{guidelines}\nCreate a prompt or topic to start a converation with friends"
    #     return input
    # else:
    #     return f'{guidelines}\nCreate a prompt/topic to keep the conversation going with sender(s) for the user in {word_limit} words or less building off of the following messages from the chat (DONT GIVE IT TO ME AS A MESSAGE,put in suggestion format NOT ACTUAL TEXTS TO SEND,keep the tone casual): {message_data}'

    button_guidelines = (
            "Follow these guidelines and provide the suggestions as distinct options, formatted as a list\n"
            "1. Spotlight on the User: Focus on the user’s interests. Ask open-ended questions and reflect on their statements.\n"
            "2. Depth through History, Philosophy, and Metaphor: Relate to personal experiences, share thoughtful perspectives, or use metaphors for clarity.\n"
            "3. Be Specific and Detailed: Provide vivid, relatable details. Use leading statements to encourage deeper engagement and avoid broad questions.\n"
        )
    #token friendly test version
    if button_pressed:
        input = f"{button_guidelines}\nCreate a prompt or topic in {word_limit} words or less to start a conversation with a person/people with the following description: (keep the tone casual and try to put it in suggestion form in bullet points instead of message form DO NOT GIVE IT IN THE FORM OF A TEXT GIVE MULTIPLE SUGGESTIONS IN THE FORM OF 'you should talk about...','try asking about...') " + message_data

        return input
    if message_data == None or message_data == "" or message_data == []:
        #can change to be more specific later
        input = "Create a prompt or topic to start a conversation with friends"
        return input
    else:
        return f"Create a prompt/topic to keep the conversation going with sender(s) for the user in {word_limit} words or less building off of the following messages from the chat (keep the tone casual and try to put it in suggestion form in bullet points instead of message form DO NOT GIVE IT IN THE FORM OF A TEXT GIVE MULTIPLE SUGGESTIONS IN THE FORM OF 'you should talk about...','try asking about...'): {message_data} Follow the numbered guidelines."

def get_prompt(message_data,client,max_tokens, lull="", feedback="", button_pressed=False):

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
    
    #only create string if button is NOT pressed (avoids key error)
    if not button_pressed:
        string = ""
        # print(message_data)
        for entry in message_data:
            string += entry['user_id'] + ': ' + entry['message'] + '\n'
        # print("String: ", string)

    if lull == 'inactivity':
        guidelines = (
            "The conversation has slowed down due to inactivity in the chat. Follow these guidelines and provide the suggestions as distinct options, formatted as a list\n"
            "1. Spotlight on the User: Focus on the user’s interests. Ask open-ended questions and reflect on their statements.\n"
            "2. Reincorporate and Connect: Revisit specific details from earlier in the conversation to create continuity.\n"
            "3. Depth through History, Philosophy, and Metaphor: Relate to personal experiences, share thoughtful perspectives, or use metaphors for clarity.\n"
            "4. Presence and Observation: Stay fully engaged by picking up on subtext and conversational cues. Adjust style and depth based on user feedback.\n"
        )

    elif lull == 'message content':
        guidelines = (
            "Users do not seem very engaged in the current conversation. Follow these guidelines and provide the suggestions as distinct options, formatted as a list\n"
            "1. Read and React with Empathy: Analyze the user’s tone and context to gauge emotions. Respond empathetically and acknowledge underlying intentions.\n"
            "2. Be Specific and Detailed: Provide vivid, relatable details. Use leading statements to encourage deeper engagement and avoid broad questions.\n"
            "3. Never Lead with 'No': Avoid shutting down ideas. If needed, use 'Yes, but…' to introduce alternate perspectives.\n"
            "4. Spotlight on the User: Focus on the user’s interests. Ask open-ended questions and reflect on their statements.\n"
            "5. Depth through History, Philosophy, and Metaphor: Relate to personal experiences, share thoughtful perspectives, or use metaphors for clarity.\n"
        )
    
    elif lull == 'oh no':
        guidelines = (
            "The user sent a lot of messages without any responses. Follow these guidelines and provide the suggestions as distinct options, formatted as a list\n"
            "1. Spontaneity and Flow: Let the conversation evolve organically without steering it toward a specific goal or topic.\n"
            "2. Create Motion: Keep the conversation dynamic by smoothly transitioning topics before they become stale.\n"
            "3. Presence and Observation: Stay fully engaged by picking up on subtext and conversational cues. Adjust style and depth based on user feedback.\n"
            "4. Spotlight on the User: Focus on the user’s interests. Ask open-ended questions and reflect on their statements.\n"
            "5. Depth through History, Philosophy, and Metaphor: Relate to personal experiences, share thoughtful perspectives, or use metaphors for clarity.\n"
        )

    if button_pressed:
        input = create_openai_input(message_data+feedback,60,button_pressed=True)
    else:
        input = create_openai_input(string+feedback+guidelines,70)
        # print("INPUT: ", input)

    # print("input",input)
    if input == None or input == "":
        print("Unable to retrieve input based on data")
        return
  
    #send prompt to chatgpt with call
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        store = True,
        max_tokens = max_tokens,
        messages = [
            {"role": "system", "content": (
                "You are a conversational AI designed to engage in natural, dynamic, and empathetic conversations. "
                "Follow the guidelines provided to enhance conversational flow and engagement."
            )},
            
            {"role": "user", "content": input} 
        ]
    )
    content = completion.choices[0].message.content
    #return generated prompt
    return content

# testing
#print(get_prompt('["Sender:Hey guys hows it going","Sender:I have so much homework :(( ","Sender:I am hungry"]',client,100))