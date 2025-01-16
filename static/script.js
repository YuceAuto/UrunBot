/***************************************************
 * 1) Code fence ("```json") veya { ... } JSON çıkarma
 *    Regex'i "``` ?json" (boşluklu) durumları da kapsar
 ***************************************************/
function extractJsonPlain(text) {
  // 1) Ek notasyonları temizle
  let cleaned = text.replace(/\[TextContentBlock[\s\S]*?\)\]/g, "");
  cleaned = cleaned.replace(/\[FileCitationAnnotation[\s\S]*?\)\]/g, "");
  cleaned = cleaned.replace(/【\d+:\d+†.*?】/g, "");

  // 2) "``` json" veya "```json" fence'i yakalamak için
  //    /``` ?json([\s\S]*?)```/i
  //    \s* => olası boşluk
  const fenceRegex = /```\s*json([\s\S]*?)```/i;
  const fenceMatch = fenceRegex.exec(cleaned);
  if (fenceMatch && fenceMatch[1]) {
    return fenceMatch[1].trim();
  }

  // 3) code fence yoksa => { ... } arayalım
  const curlyRegex = /\{[\s\S]*\}/m;
  const curlyMatch = curlyRegex.exec(cleaned);
  if (curlyMatch && curlyMatch[0]) {
    return curlyMatch[0].trim();
  }

  // JSON bulunamadı
  return null;
}

/***************************************************
 * 2) JSON'u tabloya dönüştüren (özyinelemeli) fonksiyon
 ***************************************************/
function generateHTMLFromJSON(data) {
  if (data == null) {
    return "<i>null</i>";
  }
  if (typeof data !== "object") {
    return String(data);
  }
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

  // object
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
 * 3) processBotMessage: JSON bul -> parse -> tablo
 ***************************************************/
function processBotMessage(fullText) {
  const maybeJson = extractJsonPlain(fullText);
  console.log("maybeJson:", maybeJson); // <--- Ekledik

  if (maybeJson) {
    try {
      const jsonData = JSON.parse(maybeJson);
      const tableHtml = generateHTMLFromJSON(jsonData);
      $("#botMessageContent").html(tableHtml);
      return;
    } catch (err) {
      console.warn("JSON.parse hatası:", err);
      $("#botMessageContent").text(fullText);
      return;
    }
  }

  // JSON bulamadıysak ham metin
  $("#botMessageContent").text(fullText);
}

/***************************************************
 * 4) readChunk() + form submit
 ***************************************************/
$(document).ready(function () {
  $("#messageArea").on("submit", function (e) {
    e.preventDefault();

    const inputField = $("#text");
    let rawText = inputField.val().trim();
    if (!rawText) return;

    // Kullanıcı (yeşil balon)
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

    // Bot yanıt balonu
    const botHtml = `
      <div class="d-flex justify-content-start mb-4">
        <img src="{{ url_for('static', filename='images/fotograf.png') }}"
             class="rounded-circle user_img_msg"
             alt="bot image">
        <div class="msg_cotainer" id="botMessageContainer">
          <span id="botMessageContent"></span>
        </div>
        <span class="msg_time">${currentTime}</span>
      </div>
    `;
    $("#messageFormeight").append(botHtml);
    $("#messageFormeight").scrollTop($("#messageFormeight")[0].scrollHeight);

    // /ask endpoint -> fetch
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
        throw new Error("Sunucu hatası: " + response.status);
      }
      return response.body; // ReadableStream
    })
    .then(stream => {
      const reader = stream.getReader();
      const decoder = new TextDecoder("utf-8");
      let botMessage = "";

      function readChunk() {
        return reader.read().then(({ done, value }) => {
          if (done) {
            // Tüm chunk bitti
            console.log("Final botMessage:", botMessage); // <--- Önemli
            processBotMessage(botMessage);
            return;
          }

          const chunkText = decoder.decode(value, { stream: true });
          botMessage += chunkText;

          // Anlık metin göster
          $("#botMessageContent").text(botMessage);
          $("#messageFormeight").scrollTop($("#messageFormeight")[0].scrollHeight);

          return readChunk();
        });
      }
      return readChunk();
    })
    .catch(err => {
      console.error("Hata:", err);
      $("#botMessageContent").text("Bir hata oluştu: " + err.message);
    });
  });
});
