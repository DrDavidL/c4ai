
# This code is a Streamlit application that uses OpenAI's GPT-3.5-turbo model to simulate a conversation about colon cancer screening. 
# The user can ask a question and the assistant responds based on the context provided. The conversation history is stored in the session state 
# and is displayed in an expander. If the conversation exceeds 4000 tokens, the middle part of the conversation is summarized using the 
# GPT-3.5-turbo model. The application also includes a password check to restrict access.


# Import required libraries
import openai
import streamlit as st
from openai import OpenAI
import base64
import time

# Define a function to check if the password entered by the user is correct
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        # If the password entered by the user matches the correct password
        if st.session_state["password"] == st.secrets["password"]:
            # Set the password_correct flag to True
            st.session_state["password_correct"] = True
            # Remove the password from the session state as it's no longer needed
            # del st.session_state["password"]
        else:
            # If the password is incorrect, set the password_correct flag to False
            st.session_state["password_correct"] = False

    # If this is the first run of the app, or if the password was incorrect
    if "password_correct" not in st.session_state or not st.session_state["password_correct"]:
        # Show a password input field
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        # Display a message to contact David for the password
        st.write("*Please contact David Liebovitz, MD if you need an updated password for access.*")
        # Return False as the password is not correct or not yet entered
        return False
    else:
        # If the password is correct, return True
        return True

# Define a function to summarize a text using the GPT-3.5-turbo model
def summarize(text):
    # Send a message to the model asking it to summarize the text
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Please summarize the following text capturing topics covered: {text}"}
        ]
    )
    # Return the content of the model's response
    return response['choices'][0]['message']['content']

@st.cache_data
def talk(model, voice, input):
        return client.audio.speech.create(
                    model= model,
                    voice = voice,
                    input = input,
                )

def autoplay_local_audio(filepath: str):
    # Read the audio file from the local file system
    with open(filepath, 'rb') as f:
        data = f.read()
    b64 = base64.b64encode(data).decode()
    md = f"""
        <audio controls autoplay="false">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
    st.markdown(
        md,
        unsafe_allow_html=True,
    )

# If the conversation history is not yet in the session state, initialize it
if 'conversation_history' not in st.session_state:
    st.session_state['conversation_history'] = []

if 'current_response' not in st.session_state:
    st.session_state['current_response'] = ''
    
if 'current_audio_file' not in st.session_state:
    st.session_state['current_audio_file'] = ''

# Define the disclaimer text
disclaimer = """**Disclaimer:** This is a tool to provide information about topics discussed at the C4AI meeting. Your use of this tool accepts the following:   
1. This tool does not generate validated medical content. \n 
2. This tool is not a real doctor (or statistician). \n    
3. You will not take any medical action based solely on the output of this tool. \n   
"""

# Set the page configuration
st.set_page_config(page_title='Learn about C4AI Topics!', layout = 'centered', page_icon = ':stethoscope:', initial_sidebar_state = 'auto')

# Display the title of the page
st.title("Learn about C4AI Topics!")

# Display the version of the app
st.write("ALPHA version 0.5")
st.warning("Annotations are not yet working... and this heavily uses beta features from OpenAI (that might not always work), so please be patient! Please contact David if you have any questions or feedback.")

# Create an expander for the disclaimer
with st.expander('Important Disclaimer'):
    # Display the author of the app
    st.write("Author: David Liebovitz, MD, Northwestern University")

    # Display the disclaimer
    st.info(disclaimer)

# If the password is correct
if check_password():
    # Initialize the OpenAI client
    client = OpenAI()

    # Set the OpenAI API key
    openai.api_key = st.secrets["OPENAI_API_KEY"]

    # Display an input field to enter the user's name
    name = st.text_input("What is your name?")

    # Display a radio button to select the user's role
    role =st.radio("Start with the basics or jump quickly to advanced?", ["Basics", "Advanced"])

    # Set the mission of the assistant based on the user's role
    if role == "Basics":
        mission = "Your mission is to teach the user through analogies about machine learning, AI, and statistical analysis topics, emphasizing those covered in the provided context. Be friendly, fun, and helpful and try Feynman techniques and analogies. This is a very important mission for this user who is new to the topic. "
    if role == "Advanced":
        mission = "Your mission is to teach this advanced user about machine learning, AI, and statistical analysis topics, emphasizing those covered in the provided context. Be focused, brief, to the point. No disclaimers. This is a very important mission for this user who is trying to be maximally efficient. "

    # Display an input field to enter a question
    question = st.text_input("Ask a question", "Teach me about RAG.")

    # Initialize the total token count
    total_tokens = 0

    # When the Send button is clicked
    if st.button("Send"):
        try:
            # Add the user's message to the conversation history
            st.session_state.conversation_history.append(f'**{name}:** {question}')
            # Update the total token count
            total_tokens += len(question.split())

            # Create a new thread
            thread = client.beta.threads.create()

            # If the conversation exceeds 4000 tokens
            if total_tokens > 4000:
                # Summarize the middle part of the conversation
                with st.spinner("Summarizing the lengthy conversation..."):
                    summarized_text = summarize(' '.join(st.session_state.conversation_history[2:-2]))
                # Replace the middle part of the conversation with the summary
                st.session_state.conversation_history = st.session_state.conversation_history[:2] + [summarized_text] + st.session_state.conversation_history[-2:]

            # Send the user's message
            message = client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=st.session_state.conversation_history[-1]  # Use the most recent message
            )

            # Create a run with the assistant
            run = client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id =st.secrets["assistant_id"],
                instructions=f"Act as a polite friend to the user, {name}. Your critical mission: {mission}. Rely primarily on the files provided. If the topic isn't addressed in the files, indicate when you are using sources other than the context provided. Include source annotations. If the question (broadly) is fully unrelated to ML, AI, statistics, or material in the context, indicate that you are not able to answer off-topic questions.",
                tools=[{"type": "retrieval"}]
            )

            # Retrieve the run
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )

            # Initialize a counter for the number of attempts to retrieve the run
            counter = 0

            # While the run is not completed and the counter is less than 10
            with st.spinner("Waiting for the assistant to respond..."):
                while run.status != "completed" and counter < 10:
                    # Wait for 5 seconds
                    time.sleep(5)
                    # Retrieve the run again
                    run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
                    # Increment the counter
                    counter += 1
                
            # If the counter reached 10
            if counter == 10:
                # Display a message that the run timed out
                st.write("Run timed out")

            # List the messages in the thread
            messages = client.beta.threads.messages.list(
                thread_id=thread.id,
            )
            # st.write(f'here are the full messages {messages}')
            # For each message in the thread
            for message in messages.data:
                # If the message is from the assistant and it has content
                if message.role == 'assistant' and message.content:
                    # Add the assistant's response to the conversation history
                    st.session_state.conversation_history.append(f'**AI:** {message.content[0].text.value}')
                    # Update the total token count
                    total_tokens += len(message.content[0].text.value.split())

                    # Display the assistant's response
                    st.session_state.current_response = message.content[0].text.value
                    st.write(message.content[0].text.value)
                    # Find the annotation for the assistant's response
                    message_content = message.content[0].text
                    annotations = message_content.annotations
                    st.write(f'here are the annotations: {annotations}')
                    citations = []
                    # Iterate over the annotations and add footnotes
                    for index, annotation in enumerate(annotations):
                        # Replace the text with a footnote
                        message_content.value = message_content.value.replace(annotation.text, f' [{index}]')

                        # Gather citations based on annotation attributes
                        if (file_citation := getattr(annotation, 'file_citation', None)):
                            cited_file = client.files.retrieve(file_citation.file_id)
                            citations.append(f'[{index}] {file_citation.quote} from {cited_file.filename}')
                        elif (file_path := getattr(annotation, 'file_path', None)):
                            cited_file = client.files.retrieve(file_path.file_id)
                            citations.append(f'[{index}] Click <here> to download {cited_file.filename}')
                    st.write(citations)

        # If an exception occurred
        except Exception as e:
            # Display the exception
            st.write("An error occurred: ", str(e))
            
    # Create an expander for the conversation history
    with st.expander("Show conversation history"):
        # Display the conversation history
        convo_history = '\n\n'.join(st.session_state.conversation_history)
        st.markdown(convo_history)
        st.download_button('Download the conversation', convo_history, 'conversation.txt', 'text/plain')
    
    listen_to_answer = st.checkbox("Generate an audio version of the most recent response")
    if listen_to_answer:
        speech_file_path = "current_response.mp3"    
        if len(st.session_state.current_response) > 5:
            with st.spinner("Generating audio..."):
                audio_response = talk("tts-1", "alloy", st.session_state.current_response)
                audio_response.stream_to_file(speech_file_path)
            autoplay_local_audio(speech_file_path)
        else:
            st.write("Please ask a question first!")
    


