/***************************************************
 * 1) Extract JSON or plain text
 ***************************************************/
function extractJsonPlain(text) {
  // Remove unnecessary annotations
  let cleaned = text.replace(/\[FileCitationAnnotation[\s\S]*?\)\]/g, "")
                    .replace(/【\d+:\d+†.*?】/g, "")
                    .replace(/\[TextContentBlock[\s\S]*?\)\]/g, "");

  // Match and extract JSON using code fences
  const fenceRegex = /```(?:json)?([\s\S]*?)```/i;
  const fenceMatch = fenceRegex.exec(cleaned);
  if (fenceMatch && fenceMatch[1]) {
    return fenceMatch[1].trim();
  }

  // If no code fences, search for JSON-like structure
  const curlyRegex = /\{[\s\S]*\}/m;
  const curlyMatch = curlyRegex.exec(cleaned);
  if (curlyMatch && curlyMatch[0]) {
    return curlyMatch[0].trim();
  }

  // No valid JSON found
  return null;
}

/***************************************************
 * 2) Generate HTML from JSON (recursively)
 ***************************************************/
function generateHTMLFromJSON(data) {
  if (data == null) return "<i>null</i>";
  if (typeof data !== "object") return String(data);
  
  if (Array.isArray(data)) {
    let html = `
      <table class="table table-bordered table-sm" style="background-color:#fff; color:#000;">
        <thead class="thead-light">
          <tr><th style="width:50px;">#</th><th>Değer</th></tr>
        </thead>
        <tbody>
    `;
    data.forEach((item, index) => {
      html += `
        <tr>
          <td>${index}</td>
          <td>${generateHTMLFromJSON(item)}</td>
        </tr>
      `;
    });
    html += "</tbody></table>";
    return html;
  }

  // For objects, create a key-value table
  let html = `
    <table class="table table-bordered table-sm" style="background-color:#fff; color:#000;">
      <tbody>
  `;
  for (const [key, value] of Object.entries(data)) {
    html += `
      <tr>
        <th>${key}</th>
        <td>${generateHTMLFromJSON(value)}</td>
      </tr>
    `;
  }
  html += "</tbody></table>";
  return html;
}

/***************************************************
 * 3) Process bot messages for JSON or text
 ***************************************************/
function processBotMessage(fullText, uniqueId) {
  let parsedResponse;

  try {
      // Parse the JSON response
      parsedResponse = JSON.parse(fullText);
  } catch (err) {
      console.error("JSON.parse error:", err);
      $(`#botMessageContent-${uniqueId}`).text("Response is not in JSON format: " + fullText);
      return;
  }

  // Extract response text
  const botMessageContent = parsedResponse.response || "No response available.";

  // Display the response on the frontend
  let htmlContent = `<p>${botMessageContent.replace(/\n/g, "<br>")}</p>`;
  $(`#botMessageContent-${uniqueId}`).html(htmlContent);
}


/***************************************************
 * 4) Handle user input and server communication
 ***************************************************/
$(document).ready(function () {
  $("#messageArea").on("submit", function (e) {
    e.preventDefault();

    const inputField = $("#text");
    let rawText = inputField.val().trim();
    if (!rawText) return;

    // User message bubble
    const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const userHtml = `
      <div class="d-flex justify-content-end mb-4">
        <div class="msg_cotainer_send">
          ${rawText}
          <span class="msg_time_send">${currentTime}</span>
        </div>
        <img src="https://i.ibb.co/d5b84Xw/Untitled-design.png"
             class="rounded-circle user_img_msg"
             alt="user image">
      </div>
    `;
    $("#messageFormeight").append(userHtml);
    inputField.val("");

    // Bot message bubble
    const uniqueId = Date.now();
    const botHtml = `
      <div class="d-flex justify-content-start mb-4">
        <img src="static/images/fotograf.png"
             class="rounded-circle user_img_msg"
             alt="bot image">
        <div class="msg_cotainer">
          <span id="botMessageContent-${uniqueId}"></span>
        </div>
        <span class="msg_time">${currentTime}</span>
      </div>
    `;
    $("#messageFormeight").append(botHtml);
    $("#messageFormeight").scrollTop($("#messageFormeight")[0].scrollHeight);

    // Send request to server
    fetch("/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: rawText,
        user_id: "default_user"
      })
    })
    .then(response => {
      if (!response.ok) {
        throw new Error("Server error: " + response.status);
      }
      return response.body;
    })
    .then(stream => {
      const reader = stream.getReader();
      const decoder = new TextDecoder("utf-8");
      let botMessage = "";

      function readChunk() {
        return reader.read().then(({ done, value }) => {
          if (done) {
            processBotMessage(botMessage, uniqueId);
            return;
          }
          botMessage += decoder.decode(value, { stream: true });
          $(`#botMessageContent-${uniqueId}`).text(botMessage);
          $("#messageFormeight").scrollTop($("#messageFormeight")[0].scrollHeight);

          return readChunk();
        });
      }
      return readChunk();
    })
    .catch(err => {
      console.error("Error:", err);
      $(`#botMessageContent-${uniqueId}`).text("An error occurred: " + err.message);
    });
  });

  // Notification for session expiry
  setTimeout(() => {
    document.getElementById('notificationBar').style.display = 'block';
  }, 9 * 60 * 1000);
});
