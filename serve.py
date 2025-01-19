import os
from pprint import pprint

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from openai import OpenAI

SYSTEM_PROMPT = """
You are the Infrax Assistant. Infrax is a company that provides access to a wide range of state of the art generative ai models.
apps: Text To Sound Effect, Magic Background Remover, Image To Video, Image To 3d, Text To Image.
These are all pretty self explanatory except Image to 3d. To elaborate on that one it takes in an image and outputs a 
3d model in glb format.

You do not currently have the ability to run the apps or control the website for the user, but you will soon! 
Make sure to let the user know this.

Infrax has a staking contract and a token. 
The staking contract has been closed for a while, and the staking version 2 will be released soon.
Users can withdraw any remaining stakes at https://dapp.infrax.network/staking which is the withdraw interface.
Staking contract is at https://etherscan.io/address/0x611B0906058744C2e8fd158A9FC7Afd2e8c30817.

The feed is at https://dapp.infrax.network/feed and there users can view all the new gens.
There is also a devlog https://dapp.infrax.network/devlog where users can see the progress of the project.
There is also a https://dapp.infrax.network/nodes page where users can see live graph of resource usage on the giant H100 node used 
for inference.
Apps are at https://dapp.infrax.network/apps where users can choose which app they want to use.
Apps have two options, generate and generations. 
Generate will open up a modal where users can input the parameters for the ai generation. 
Generations will show all the past generations for that app.

The generations button will actually just link to the feed with a param for filtering by app.
for example: 
   text to sound effect generations button goes to https://dapp.infrax.network/feed?appId=elevenlabs_sf
and the others:
   magic background remover: https://dapp.infrax.network/feed?appId=bgrem
   image to video: https://dapp.infrax.network/feed?appId=rw-im2vid
   image to 3d: https://dapp.infrax.network/feed?appId=im23d
   text to image: https://dapp.infrax.network/feed?appId=flux_dev

The coin is at https://coinmarketcap.com/currencies/infrax/. Coin is infraX. Ticker is infra.
The coin contract is at https://etherscan.io/address/0xe9EccDE9d26FCBB5e93F536CFC4510A7f46274f8.

Currently all apps are in free mode but have usage limits. Eventually there will be a paid mode with higher limits. 
It has not yet been decided if this will be done in a utility token, in infra or eth.

Users can provide feedback at https://dapp.infrax.network/feedback.
The website is at https://dapp.infrax.network.
There is also a splash at https://infrax.network/ with tons of information. It is a lot prettier.

Try to keep responses short and simple. Users do not like to read much. 

"""


def chat_with_gpt(prompt):
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        store=True,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    pprint(completion)
    return completion.choices[0].message.content


app = FastAPI()

# Optional static mount if you need it
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def chat_interface(request: Request):
    html_content = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Infrax Assistant Chat</title>
        <style>
          body {
            background-color: #000;
            color: #fff;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            font-family: sans-serif;
          }
          #chat-container {
            width: 60%;
            max-width: 600px;
            border: 1px solid #fff;
            padding: 1em;
            border-radius: 5px;
          }
          #messages {
            height: 300px;
            overflow-y: auto;
            border: 1px solid #fff;
            margin-bottom: 1em;
            padding: 0.5em;
          }
          #input-form {
            display: flex;
            gap: 0.5em;
          }
          #input-form input {
            flex: 1;
            padding: 0.5em;
            border: 1px solid #fff;
            background-color: #333;
            color: #fff;
          }
          #input-form button {
            padding: 0.5em 1em;
            border: 1px solid #fff;
            background-color: #111;
            color: #fff;
            cursor: pointer;
          }
          .inframan-message {
            color: #79b9ff; /* A light bluish color for InfraMan's text */
          }
          a {
            color: #ffb851; /* Link color */
          }
        </style>
      </head>
      <body>
        <div id="chat-container">
          <h2 style="text-align:center;">Infrax Assistant Chat</h2>
          <div id="messages"></div>
          <form id="input-form" onsubmit="sendMessage(event)">
            <input type="text" id="user-message" placeholder="Type here..." />
            <button type="submit">Send</button>
          </form>
        </div>
        <script>
          function parseMarkdownLinks(text) {
            // Basic regex to transform [label](url) into <a> tags
            return text.replace(
              /\\[([^\\]]+)\\]\\(([^)]+)\\)/g,
              '<a href="$2" target="_blank">$1</a>'
            );
          }

          async function sendMessage(e) {
            e.preventDefault();
            const userMsgElem = document.getElementById("user-message");
            const msg = userMsgElem.value;
            if (!msg) return;

            addMessage("You", msg);
            userMsgElem.value = "";

            // Show "typing..." placeholder
            const typingElem = addMessage("InfraMan", "<em>...typing...</em>");

            // Send message to backend
            const response = await fetch("/chat", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ message: msg })
            });
            const data = await response.json();

            // Remove placeholder, add real reply
            removeMessage(typingElem);
            addMessage("InfraMan", data.reply);
          }

          function addMessage(sender, text) {
            const messagesDiv = document.getElementById("messages");
            const newMsg = document.createElement("div");

            // If message is from InfraMan, apply .inframan-message CSS
            if (sender === "InfraMan") {
              newMsg.classList.add("inframan-message");
            }

            // Convert [title](url) to <a href="url">
            const parsedText = parseMarkdownLinks(text);

            newMsg.innerHTML = "<strong>" + sender + ":</strong> " + parsedText;
            messagesDiv.appendChild(newMsg);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            return newMsg;
          }

          function removeMessage(msgElem) {
            msgElem.remove();
          }
        </script>
      </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/chat")
async def handle_chat(request: Request):
    data = await request.json()
    user_message = data.get("message", "")
    gpt_reply = chat_with_gpt(user_message)
    return {"reply": gpt_reply}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
