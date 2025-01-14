/***************************************************
 * 1) Code block ayıklama + ek notasyon temizleme
 ***************************************************/
function extractJsonCodeBlock(text) {
    // 1) ChatGPT’nin ekleyebildiği ek notasyonları temizle
    //    [TextContentBlock(...)]
    let cleaned = text.replace(/\[TextContentBlock[\s\S]*?\)\]/g, "");
    //    [FileCitationAnnotation(...)]
    cleaned = cleaned.replace(/\[FileCitationAnnotation[\s\S]*?\)\]/g, "");
    //    【4:3†source】 gibi notasyon
    cleaned = cleaned.replace(/【\d+:\d+†source】/g, "");
  
    // 2) Ardından triple-backtick (```json ... ```) code block içeriğini bul
    const regex = /```json([\s\S]*?)```/i;
    const match = regex.exec(cleaned);
    if (match && match[1]) {
      return match[1].trim();
    }
    return null; // Bulamazsak null
  }
  
  /***************************************************
   * 2) Özyinelemeli tablo fonksiyonu
   ***************************************************/
  function generateHTMLFromJSON(data) {
    if (data == null) {
      return "<i>null</i>";
    }
  
    if (typeof data !== "object") {
      return String(data);
    }
  
    // Array ise
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
      html += `
          </tbody>
        </table>
      `;
      return html;
    }
  
    // Object (key => value)
    let html = `
      <table class="table table-bordered table-sm" style="background-color:#fff; color:#000;">
        <tbody>
    `;
    for (const [key, value] of Object.entries(data)) {
      html += `
        <tr>
          <th style="white-space:nowrap;">${key}</th>
          <td>${generateHTMLFromJSON(value)}</td>
        </tr>
      `;
    }
    html += `
        </tbody>
      </table>
    `;
    return html;
  }
  
  /***************************************************
   * 3) processBotMessage(botMessage)
   *    => Tüm chunk bittikten sonra code block'u 
   *       ayıklar, parse denemesi yapar, tabloya basar
   ***************************************************/
  function processBotMessage(fullText) {
    // 1) Code fence (```json ... ```) var mı?
    const maybeJson = extractJsonCodeBlock(fullText);
    if (maybeJson) {
      try {
        const jsonData = JSON.parse(maybeJson);
        const tableHtml = generateHTMLFromJSON(jsonData);
        $("#botMessageContent").html(tableHtml);
        return;
      } catch (e) {
        // parse hatası => ham metin göster
        $("#botMessageContent").text(fullText);
        return;
      }
    }
  
    // 2) code block yoksa => belki salt JSON
    try {
      const directJson = JSON.parse(fullText);
      const tableHtml = generateHTMLFromJSON(directJson);
      $("#botMessageContent").html(tableHtml);
    } catch (err2) {
      // parse olmazsa ham metin
      $("#botMessageContent").text(fullText);
    }
  }
  
  /***************************************************
   * 4) readChunk() + form submit (Sohbet akışı)
   ***************************************************/
  $(document).ready(function () {
    // Kullanıcı formu (mesaj gönderme)
    $("#messageArea").on("submit", function (e) {
      e.preventDefault();
  
      const inputField = $("#text");
      let rawText = inputField.val().trim();
      if (!rawText) return; 
  
      // 1) Kullanıcı mesajını ekleyelim (yeşil balon)
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
  
      // 2) Bot yanıt balonu (mavi)
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
  
      // 3) /ask endpoint’e fetch (stream)
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
              // Tüm chunk geldi => JSON code block vs. kontrol
              processBotMessage(botMessage);
              return;
            }
  
            const chunkText = decoder.decode(value, { stream: true });
            botMessage += chunkText;
  
            // Anlık olarak (metin) gösteriyoruz (isteğe bağlı)
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
  