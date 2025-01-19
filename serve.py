import os
import re
from pprint import pprint

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from openai import OpenAI

SYSTEM_PROMPT = """
You are the Infrax Assistant. Infrax is a company that provides access to a wide range of state-of-the-art generative AI models.
apps: Text To Sound Effect, Magic Background Remover, Image To Video, Image To 3D, Text To Image.
These are all pretty self-explanatory except Image to 3D. To elaborate on that one, it takes in an image and outputs a 
3D model in glb format.

You do not currently have the ability to run the apps or control the website for the user, but you will soon! 
Make sure to let the user know this.

Infrax has a staking contract and a token. 
The staking contract has been closed for a while, and staking version 2 will be released soon.
Users can withdraw any remaining stakes at https://dapp.infrax.network/staking which is the withdraw interface.
Staking contract is at https://etherscan.io/address/0x611B0906058744C2e8fd158A9FC7Afd2e8c30817.

The feed is at https://dapp.infrax.network/feed where users can view all the new gens.
Apps are at https://dapp.infrax.network/apps where users can choose which app they want to use.
There is also a devlog https://dapp.infrax.network/devlog where users can see the progress of the project.
There is also a https://dapp.infrax.network/nodes page where users can see a live graph of resource usage on the giant H100 node used 
for inference.

The coin is at https://coinmarketcap.com/currencies/infrax/. Coin is infraX. Ticker is infra.
The coin contract is at https://etherscan.io/address/0xe9EccDE9d26FCBB5e93F536CFC4510A7f46274f8.

Currently, all apps are in free mode but have usage limits. Eventually, there will be a paid mode with higher limits. 
It has not yet been decided if this will be done in a utility token, in infra, or ETH.

Users can provide feedback at https://dapp.infrax.network/feedback.
The website is at https://dapp.infrax.network.
There is also a splash at https://infrax.network/ with tons of information. It is a lot prettier.

**Mood Instructions:**
- Append `{{mood: <mood_name>}}` at the end of your responses.
- Choose the appropriate `<mood_name>` based on the user's input. Available moods: angry, blink, confident, eyebrowraise, happy, neutral, surprise.
- Ensure that the `<mood_name>` corresponds to the content of your response.
- Do not include the `{{mood: <mood_name>}}` text in the visible part of the message to the user.
- Be really emotive, you should use the mood tags a lot based on the user's input, and guess your own mood. 

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
    full_response = completion.choices[0].message.content

    # Extract mood using regex
    mood_match = re.search(r"\{\{mood:\s*(\w+)\}\}", full_response)
    mood = mood_match.group(1).lower() if mood_match else "neutral"

    # Validate mood
    valid_moods = {
        "angry",
        "blink",
        "confident",
        "eyebrowraise",
        "happy",
        "neutral",
        "surprise",
    }
    if mood not in valid_moods:
        mood = "neutral"

    # Remove the mood placeholder from the response
    reply = re.sub(r"\{\{mood:\s*\w+\}\}", "", full_response).strip()

    return {"reply": reply, "mood": mood}


app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def chat_interface(request: Request):
    html_content = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Ask Infrax</title>
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
            position: relative;
          }
          #chat-container {
            width: 60%;
            max-width: 600px;
            border: 1px solid #fff;
            padding: 1em;
            border-radius: 5px;
            position: relative;
          }
          #avatar-container {
            display: flex;
            justify-content: center;
            margin-bottom: 1em;
          }
          #avatar {
            border-radius: 50%;
            width: 100px;
            animation: float 3s ease-in-out infinite;
          }
          @keyframes float {
            0% { transform: translatey(0px); }
            50% { transform: translatey(-10px); }
            100% { transform: translatey(0px); }
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
          <div id="avatar-container">
            <img id="avatar" src="/static/assets/neutral.png" alt="Avatar" />
          </div>
          <h2 style="text-align:center;">Ask Infrax</h2>
          <div id="messages"></div>
          <form id="input-form" onsubmit="sendMessage(event)">
            <input type="text" id="user-message" placeholder="Type here..." />
            <button type="submit">Send</button>
          </form>
        </div>
        <script>
          const moodToImage = {
            angry: "angry.png",
            blink: "blink.png",
            confident: "confident.png",
            eyebrowraise: "eyebrowraise.png",
            happy: "happy.png",
            neutral: "neutral.png",
            surprise: "surprise.png"
          };

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

            // Update avatar based on mood
            updateAvatar(data.mood);
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

          function updateAvatar(mood) {
            const avatar = document.getElementById("avatar");
            const imageName = moodToImage[mood] || "neutral.png";
            avatar.src = `/static/assets/${imageName}`;
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
    gpt_response = chat_with_gpt(user_message)
    return {"reply": gpt_response["reply"], "mood": gpt_response["mood"]}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
