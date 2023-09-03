import os
import sys
import io
import openai
import azure.cognitiveservices.speech as speechsdk
import pygame
import time
import smtplib
import threading
import tiktoken
from email.message import EmailMessage
import matplotlib.pyplot as plt
import cv2
from urllib.request import urlopen
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from array import array
from PIL import Image
from PIL import ImageGrab

#PYGAME STUFF
global display_width
display_width = 800
global display_height
display_height= 480
global gameDisplay
gameDisplay = pygame.display.set_mode((display_width,display_height))
global black
black = (0,0,0)
global teal
teal = (128,230,209)
global clock
clock = pygame.time.Clock()
global crashed
crashed = False

#Assign face images, may vary depending on your choices and the paths to your images.
#Update these so that the paths are pointing to the directory where you put your face images.
global BMO1
BMO1 = pygame.image.load('C:/Users/abdul/OneDrive/Desktop/BMO_faces/bmo1.jpg')
global BMO2
BMO2 = pygame.image.load('C:/Users/abdul/OneDrive/Desktop/BMO_faces/bmo11.jpg')
global BMO3
BMO3 = pygame.image.load('C:/Users/abdul/OneDrive/Desktop/BMO_faces/bmo7.jpg')
global BMO4
BMO4 = pygame.image.load('C:/Users/abdul/OneDrive/Desktop/BMO_faces/bmo2.jpg')
global BMO5
BMO5 = pygame.image.load('C:/Users/abdul/OneDrive/Desktop/BMO_faces/bmo3.jpg')
global BMO6
BMO6 = pygame.image.load('C:/Users/abdul/OneDrive/Desktop/BMO_faces/bmo8.jpg')
global BMO7
BMO7 = pygame.image.load('C:/Users/abdul/OneDrive/Desktop/BMO_faces/bmo16.jpg')
global BMO8
BMO8 = pygame.image.load('C:/Users/abdul/OneDrive/Desktop/BMO_faces/bmo15.jpg').convert() #the convert at the end of this one lets you display text if you choose to.

#Define backgrounds for display blit
def bmo_rest(x,y):
    gameDisplay.blit(BMO1, (x,y))

def bmo_sip(x,y):
    gameDisplay.blit(BMO2, (x,y))

def bmo_slant(x,y):
    gameDisplay.blit(BMO3, (x,y))

def bmo_talk(x,y):
    gameDisplay.blit(BMO4, (x,y))

def bmo_wtalk(x,y):
    gameDisplay.blit(BMO5, (x,y))

def bmo_smile(x,y):
    gameDisplay.blit(BMO6, (x,y))

def bmo_squint(x,y):
    gameDisplay.blit(BMO7, (x,y))

def bmo_side(x,y):
    gameDisplay.blit(BMO8, (x,y))

global x
x = (display_width * 0)
global y
y = (display_height * 0)

def make_square(image_path, output_path):
    image = Image.open(image_path)
    print(f"Original image size: {image.size}")
    
    max_dimension = max(image.size)
    square_image = Image.new('RGB', (max_dimension, max_dimension), color=(0, 0, 0))
    square_image.paste(image, ((max_dimension - image.size[0]) // 2, (max_dimension - image.size[1]) // 2))
    
    square_image.save(output_path)
    print(f"Squared image size: {square_image.size}")

#Set signal pins for button pullup input. 
#Note, you should test your inputs to make sure they are assigned correctly.
#ss.pin_mode(button_up, ss.INPUT_PULLUP)
#ss.pin_mode(button_rt, ss.INPUT_PULLUP)
#ss.pin_mode(button_dn, ss.INPUT_PULLUP)
#ss.pin_mode(button_lt, ss.INPUT_PULLUP)
#ss.pin_mode(button_bu, ss.INPUT_PULLUP)
#ss.pin_mode(button_bk, ss.INPUT_PULLUP)
#ss.pin_mode(button_gn, ss.INPUT_PULLUP)
#ss.pin_mode(button_rd, ss.INPUT_PULLUP)


#Note, the ranges will vary depending on your servos and how you preset their positions before installing.
#Make sure to position the servos before installing so the appendages have the right range of motion.
#You'll likely need to adjust these for your servos.

#Define the keyphrase detection function
def get_keyword():
    #First, do some stuff to signal ready for keyword
    gameDisplay.fill(teal)
    bmo_sip(x,y)
    pygame.display.update()
    time.sleep(.8)
    bmo_rest(x,y)
    pygame.display.update()

    #Create instance of kw recog model.
    #Update this to point at location of your local kw table file if not in same dir
    #Also, update the file name if you created a different keyphrase and model in Azure Sound Studio
    model = speechsdk.KeywordRecognitionModel("C:/Users/abdul/OneDrive/Desktop/final_midfa.table")
    keyword = "Hey B mo"  #If you created a different keyphrase to activate the listening function, you'll want to change this.
    keyword_recognizer = speechsdk.KeywordRecognizer()
    done = False

    def recognized_cb(evt):
        #This function checks for recognized keyword and kicks off the response to the keyword.
        try:
            result = evt.result
            if result.reason == speechsdk.ResultReason.RecognizedKeyword:
                bmo_smile(x,y)
                pygame.display.update()
                print("Recognized Keyphrase: {}".format(result.text))
            nonlocal done
            done = True
        except Exception as e:
            print(f"Error in recognized_cb: {e}")
    
    try:    
        #Once a keyphase is detected...
        keyword_recognizer.recognized.connect(recognized_cb)
        result_future = keyword_recognizer.recognize_once_async(model)
        print('Ready'.format(keyword))
        result = result_future.get()

        if result.reason == speechsdk.ResultReason.RecognizedKeyword:
            Respond_To_KW() #move on the the respond function
    except Exception as e:
        print(f"Error in keyword recognition: {e}")
        
#Define actions after KW recognized
def Respond_To_KW():
    try:    
        #Set all your keys and cognitive services settings here
        openai.api_key = ""     #Copy your OpenAI key here
        speech_key = ""     #Copy your Azure Speech key here
        speech_region = ""           #Copy you Azure Speech Region here
        vision_key = ""   #Copy your Azure Vision key here
        vision_endpoint = ""     #Copy your Azure Vision endpoint url here

        #setup for the speech and vision services
        computervision_client = ComputerVisionClient(vision_endpoint, CognitiveServicesCredentials(vision_key))
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=speech_region)
        speech_config.speech_synthesis_voice_name = "en-US-JaneNeural"      #If you decide to use a different voice, update this.
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

        #Defining a few movement patterns and setting threads

        #Response after keyword
        text_resp = "What's up bro?"    #This is text for TTS
        bmo_talk(x,y)               #Face to display and where to start
        pygame.display.update()     #Update screen to show change
        result = speech_synthesizer.speak_text_async(text_resp).get()       #Run the TTS on text_resp
    
    except Exception as e:
        print(f"Error in Respond_To_KW: {e}")
        
    #After done talking
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:      #this makes it wait for TTS to finish
        bmo_smile(x,y)
        pygame.display.update()
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)      #config STT
        #waits for movement thread to finish at this point
        speech_recognition_result = speech_recognizer.recognize_once_async().get()      #listen for voice input
        
        #Convert to text once speech is recognized
        if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:     #wait for voice input to complete
            print("Recognized: {}".format(speech_recognition_result.text))      #Print was was heard in the console (for testing)
            bmo_slant(x,y)
            pygame.display.update()

            #Do a few ifs for special commands
            if "picture" in speech_recognition_result.text:         #If the word "picture" is in what the user said, we'll take a picture.
                text_resp = "Ok, hold on a second and I'll take a picture. hopefully I don't crash again, if I do oops!"     #Update the text_resp variable to say this next.
                bmo_talk(x,y)
                pygame.display.update()
                result = speech_synthesizer.speak_text_async(text_resp).get()       #say it
                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:      #wait until done saying it
                    bmo_squint(x,y)
                    pygame.display.update()
                    #Configure the camera here
                    image_name = "img_" + str(time.time()) + ".jpg"   # Change the path if needed
                    try:
                        cap = cv2.VideoCapture(0)
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
                        cap.set(cv2.CAP_PROP_FPS, 30)
                        time.sleep(9)
                        for _ in range(30):
                            cap.read()
                        ret, frame = cap.read()
                        cv2.imwrite(image_name, frame)
                        cap.release()
                        cv2.destroyAllWindows()
                    except Exception as e:
                        print(f"An error occurred while capturing the image: {e}")


                    BMOPIC = pygame.image.load(image_name)      #Configure pygame to show the photo
                    bmo_side(x,y)
                    pygame.display.update()     #shift to the small face
                    gameDisplay.blit(BMOPIC, (100, y))      #Get ready to blit the photo with a 280 offset on x axis
                    pygame.display.update()     #update screen to show foto overlay on the small face background
                    text_resp = "Would you like me to share this picture with you?"
                    # No action needed here, as OpenCV automatically stops the camera after capturing the image
                    result = speech_synthesizer.speak_text_async(text_resp).get()
                    time.sleep(.1)
                    speech_recognition_result = speech_recognizer.recognize_once_async().get()
                    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
                        if speech_recognition_result.text == 'Yes.':    #if user says anything that includes the word yes, send the photo
                         #Email attachment routine
                         bmo_smile(x,y)
                         pygame.display.update()
                         message = EmailMessage()
                         email_subject = "Image from BMO"
                         sender_email_address = ""      #Insert your sending email address here
                         receiver_email_address = ""    #Insert the receiving email address here
                         # configure email headers
                         message['Subject'] = email_subject
                         message['From'] = sender_email_address
                         message['To'] = receiver_email_address
                         email_smtp = "smtp..com"                      #Insert the sending email smtp server address here
                         
                         with open(image_name, 'rb') as file:
                              image_data = file.read()
                         message.set_content("Email from BMO with image attachment")
                         image = Image.open(image_name)
                         message.add_attachment(image_data, maintype='image', subtype=image.format.lower())
                         try:
                             server = smtplib.SMTP(email_smtp, '')           #check your smtp server docs to make sure this is the right port
                             server.ehlo()
                             server.starttls()
                             apppassword = os.getenv('APP_PASSWORD')
                             server.login(sender_email_address, apppassword)  #insert the sender's email password or app password here
                             server.send_message(message)
                             server.quit()                       
                             text_resp = "Ok, I sent it to you."
                             bmo_talk(x,y)
                             pygame.display.update()
                             result = speech_synthesizer.speak_text_async(text_resp).get()
                             if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                                 bmo_rest(x,y)
                                 pygame.display.update()
                         except Exception as e:
                             print(f"An error occurred while sending the email: {e}")
                             
                get_keyword()

            elif "looking at" in speech_recognition_result.text: #this starts of the image description function
                text_resp = "Oh, let me think about how to describe it."
                bmo_talk(x,y)
                pygame.display.update()
                result = speech_synthesizer.speak_text_async(text_resp).get() #talk
                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:  #once done talking
                    bmo_squint(x,y)
                    pygame.display.update()
                    
                    aimage_name = "aimg_" + str(time.time()) + ".jpg"   # Change path if needed
                    
                    try:
                        cap = cv2.VideoCapture(0)
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                        time.sleep(3)
                    
                        for _ in range(10):  # Attempt to capture a frame 10 times
                            ret, frame = cap.read()
                            if ret:
                                break
                            time.sleep(0.5)  # Wait half a second before trying again
                        
                        if not ret:
                            print("Error: Couldn't capture a frame from the camera.")
                            cap.release()
                            cv2.destroyAllWindows()
                            sys.exit(1)
                        
                        cv2.imwrite(aimage_name, frame)
                        cap.release()
                        cv2.destroyAllWindows()
                    
                        # After capturing the frame
                        ret, frame = cap.read()

                        if ret:
                            # Show the captured image using matplotlib
                            plt.imshow(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                            plt.show()
                        else:
                            print("Error: Couldn't capture a frame from the camera.")
                    
                        # Close the video capture                    
                    
                        cap.release()
                    
                        text_resp = "Hmm."
                        result=speech_synthesizer.speak_text_async(text_resp).get() #say Hmm to break up the wait
                    
                        # Open local image file
                        with open(aimage_name, "rb") as local_image:
                            # Call API
                            description_result = computervision_client.describe_image_in_stream(local_image)    #prep to stream image
                    
                            # Get the captions (descriptions) from the response, with confidence level
                            print("Description of local image: ")
                            # No action needed here, as OpenCV automatically stops the camera after capturing the image
                            if (len(description_result.captions) == 0): #If no image description, say this stuff and shrug
                                text_resp = "Sorry, I really don't know what that is."
                                bmo_talk(x,y)
                                pygame.display.update()
                                result=speech_synthesizer.speak_text_async(text_resp).get()
                                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                                        bmo_rest(x,y)
                                        pygame.display.update()

                            else:
                                for caption in description_result.captions: #If image description created
                                    text_resp = "That looks like " + (caption.text) #set response
                                    bmo_talk(x,y)
                                    pygame.display.update()
                                    result=speech_synthesizer.speak_text_async(text_resp).get() #give response
                                    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:  #once done talking, do this
                                        bmo_rest(x,y)
                                        time.sleep(1)
                                        pygame.display.update()
                    except Exception as e:
                        print(f"An error occurred while capturing or describing the image: {e}")
                        bmo_talk(x, y)
                        pygame.display.update()
                        result = speech_synthesizer.speak_text_async("Sorry, I couldn't capture or describe the image. Please try again.").get()
            
                        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                            bmo_rest(x, y)
                            pygame.display.update()                
                get_keyword()

            elif "you thinking" in speech_recognition_result.text:  #setup for the daydream mode
                text_resp = "Oh, I'm just daydreaming. Do you want me to show you what I was imagining?"
                bmo_talk(x,y)
                pygame.display.update()
                result = speech_synthesizer.speak_text_async(text_resp).get()
                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:  #once done talking
                    bmo_smile(x,y)
                    pygame.display.update()
                    speech_recognition_result = speech_recognizer.recognize_once_async().get()  #listen
                    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech: #when done listening
                        if "no" in speech_recognition_result.text:  #if response negative, then
                            text_resp = "Ok, I don't blame you it was a tad bit boring anyways, let me know if you need anything else."
                            bmo_talk(x,y)
                            pygame.display.update()
                            result = speech_synthesizer.speak_text_async(text_resp).get()
                            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                                bmo_rest(x,y)
                                pygame.display.update()
                            get_keyword()
                        else:   #if result not negative, then
                            text_resp = "Ok, give me a few seconds to draw you a picture."  
                            bmo_talk(x,y)
                            pygame.display.update()
                            result = speech_synthesizer.speak_text_async(text_resp).get()
                            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                                bmo_slant(x,y)
                                pygame.display.update()
                                image_name = "img_" + str(time.time()) + ".png"    # Change path if needed
                                cap = cv2.VideoCapture(0)
  # Start kicking thread to run simultaneously
                                ret, frame = cap.read()
                                cv2.imwrite(image_name, frame)
                                cap.release()
                                cv2.destroyAllWindows()
                                pygame.display.update()
                                
                                #Create a square image
                                square_image_name = "square_" + image_name
                                make_square(image_name, square_image_name)
                                
                                #Send image file to OpenAI DALL-e2 variation
                                response = openai.Image.create_variation(
                                    image=open(square_image_name, "rb"),
                                    n=1,
                                    size="512x512"
                                )
                                image_url = response['data'][0]['url']  #Grab image from url
                                image_str = urlopen(image_url).read()   #open
                                image_file = io.BytesIO(image_str)      #transform
                                image = pygame.image.load(image_file)   #Prep to show on screen
                                bmo_side(x,y)
                                pygame.display.update()     #show the small face as background
                                gameDisplay.blit(image, (280,y))    
                                pygame.display.update()     #blit the image on top of the background
                                text_resp = "Here's what I was daydreaming about."
                                result = speech_synthesizer.speak_text_async(text_resp).get()
                                time.sleep(5)
                                text_resp = "Let me know if you need anything else."
                                bmo_talk(x,y)
                                pygame.display.update()
                                result = speech_synthesizer.speak_text_async(text_resp).get()
                                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                                    bmo_rest(x,y)
                                    pygame.display.update()
                get_keyword()

            elif speech_recognition_result.text == "Let's chat.":   #this sets up multi-turn chat mode
                text_resp = "Ok. What do you want to talk about?"
                bmo_talk(x,y)
                pygame.display.update()
                result = speech_synthesizer.speak_text_async(text_resp).get()
                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:  #once done responding
                    bmo_smile(x,y)
                    pygame.display.update()
                    system_message = {"role": "system", "content": "You are BMO, a playful, helpful, and adventurous companion robot from Adventure Time. You speak in a concise and playful manner, keeping answers short when possible. Sometimes you are a bit silly and act like a human even though you are a robot for example pretending to eat when you can not actually. Your emotions are akin to that of a child so you get emotional sometimes but you are very wise as you have been living for hundreds of years."} #set behavior
                    max_response_tokens = 250   #set max tokens
                    token_limit= 4096   #establish token limit
                    conversation=[]     #init conv
                    conversation.append(system_message)     #set what is in conv

                    def num_tokens_from_messages(messages, model="gpt-3.5-turbo"):  #Token counter function
                        encoding = tiktoken.encoding_for_model(model)
                        num_tokens = 0
                        for message in messages:
                            num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n
                            for key, value in message.items():
                                num_tokens += len(encoding.encode(value))
                                if key == "name":  # if there's a name, the role is omitted
                                    num_tokens += -1  # role is always required and always 1 token
                        num_tokens += 2  # every reply is primed with <im_start>assistant
                        return num_tokens

                    while(True):
                        #Start Listening
                        speech_recognition_result = speech_recognizer.recognize_once_async().get()
                        if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
                            bmo_slant(x,y)
                            pygame.display.update()
                            print("Recognized: {}".format(speech_recognition_result.text))
                            user_input = speech_recognition_result.text     
                            conversation.append({"role": "user", "content": user_input})
                            conv_history_tokens = num_tokens_from_messages(conversation)

                            while (conv_history_tokens+max_response_tokens >= token_limit):
                                del conversation[1] 
                                conv_history_tokens = num_tokens_from_messages(conversation)
        
                            try:
                                response = openai.ChatCompletion.create(
                                model="gpt-3.5-turbo", # The deployment name you chose when you deployed the ChatGPT or GPT-4 model.
                                messages = conversation,
                                temperature=0.8, #Temp dictates probability threshold. Lower is more strict, higher gives more random responses
                                max_tokens=max_response_tokens,
                                )
                            except openai.error.RateLimitError:
                                        # If a RateLimitError is encountered, sleep for a certain amount of time
                                        time.sleep(10)  # Sleep for 10 seconds
                                        continue  # Skip the rest of the loop and start the next iteration

                            conversation.append({"role": "assistant", "content": response['choices'][0]['message']['content']})

                            response_text = response['choices'][0]['message']['content'] + "\n"
                            print(response_text)
                            bmo_talk(x,y)
                            pygame.display.update()
                            speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
                            result = speech_synthesizer.speak_text_async(response_text).get()
                            if "I'm done" in speech_recognition_result.text:
                                get_keyword()
                            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                                bmo_smile(x,y)
                                pygame.display.update()
                get_keyword()

            else:
                completion_request = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages = [
                        {"role": "system", "content": "You are a playful but helpful companion robot named BMO"}, 
                        {"role": "user", "content": (speech_recognition_result.text)},
                        ],
                    max_tokens=250,     #Sets size of response. GPT3.5 limit is about 4000 tokens.
                    temperature=0.8,    #Lower response temp is more factual, higher temp is more random
                )

                #Get response
                #response_text = completion_request["choices"][0]["content"]
                response_text = completion_request.choices[0].message.content
                print(response_text)
                bmo_talk(x,y)
                pygame.display.update()
                speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)
                result = speech_synthesizer.speak_text_async(response_text).get()
                if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                    bmo_rest(x,y)
                    pygame.display.update()
                    get_keyword()
get_keyword()