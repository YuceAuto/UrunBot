/***************************************************
 * 1) "value=''' ... '''" arasında geçen metni çekip al
 ***************************************************/
function extractJsonPlain(text) {
  // 1) FileCitationAnnotation vb. gereksiz notasyonları silelim
  let cleaned = text.replace(/\[FileCitationAnnotation[\s\S]*?\)\]/g, "");
  cleaned = cleaned.replace(/【\d+:\d+†.*?】/g, "");

  // 2) [TextContentBlock(...)] sarmalını da silebiliriz (sunucuda büyük ölçüde temizlendi)
  cleaned = cleaned.replace(/\[TextContentBlock[\s\S]*?\)\]/g, "");

  // 3) triple backtick code fence yakala -> ```json ... ```
  const fenceRegex = /```(?:json)?([\s\S]*?)```/i;
  const fenceMatch = fenceRegex.exec(cleaned);
  if (fenceMatch && fenceMatch[1]) {
    return fenceMatch[1].trim();
  }

  // 4) code fence yoksa => { ... } arayalım
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
function processBotMessage(fullText, uniqueId) {
  let parsedResponse;

  try {
    // JSON parse etmeye çalış
    parsedResponse = JSON.parse(fullText);
  } catch (err) {
    console.error("JSON.parse hatası:", err);
    console.log("Gelen metin:", fullText); // Yanıtın ne olduğunu gör
    $(`#botMessageContent-${uniqueId}`).text("Yanıt JSON formatında değil: " + fullText);
    return;
  }

  // Yanıt JSON formatındaysa metni işleyin
  const botMessageContent = parsedResponse.response || "Yanıt alınamadı.";
  const images = parsedResponse.images || [];

  if (botMessageContent === "Preparing response...") {
    $(`#botMessageContent-${uniqueId}`).text(botMessageContent);

    if (images.length > 0) {
      let imageHtml = `<div class="image-container" style="margin-top: 10px;">`;
      images.forEach(image => {
        imageHtml += `
          <div style="display: inline-block; margin: 5px;">
            <img src="${image.url}" alt="${image.name}" style="max-width: 100px; max-height: 100px; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" />
            <p style="text-align: center; font-size: 12px; color: #555;">${image.name}</p>
          </div>
        `;
      });
      imageHtml += `</div>`;
      $(`#botMessageContent-${uniqueId}`).append(imageHtml);
    }

    return;
  }

  // Tam yanıt ve resimleri göster
  let htmlContent = `<p>${botMessageContent}</p>`;
  if (images.length > 0) {
    htmlContent += `<div class="image-container" style="margin-top: 10px;">`;
    images.forEach(image => {
      htmlContent += `
        <div style="display: inline-block; margin: 5px;">
          <img src="${image.url}" alt="${image.name}" style="max-width: 100px; max-height: 100px; border: 1px solid #ddd; border-radius: 4px; padding: 5px;" />
          <p style="text-align: center; font-size: 12px; color: #555;">${image.name}</p>
        </div>
      `;
    });
    htmlContent += `</div>`;
  }

  $(`#botMessageContent-${uniqueId}`).html(htmlContent);
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

    // BOT yanıtı için benzersiz ID (her mesaj ayrı)
    const uniqueId = Date.now();  // Basit yöntem

    // Bot yanıt balonu (her seferinde yeni HTML oluşturuyoruz!)
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
            // Tüm chunk bitti -> final parse
            processBotMessage(botMessage, uniqueId);
            return;
          }

          const chunkText = decoder.decode(value, { stream: true });
          botMessage += chunkText;

          // Anlık metni ID'si unique olan span'e yaz
          $(`#botMessageContent-${uniqueId}`).text(botMessage);
          $("#messageFormeight").scrollTop($("#messageFormeight")[0].scrollHeight);

          return readChunk();
        });
      }
      return readChunk();
    })
    .catch(err => {
      console.error("Hata:", err);
      $(`#botMessageContent-${uniqueId}`).text("Bir hata oluştu: " + err.message);
    });
  });

  // Örnek: 9. dakikada notification göster
  setTimeout(() => {
    document.getElementById('notificationBar').style.display = 'block';
  }, 9 * 60 * 1000);
});
