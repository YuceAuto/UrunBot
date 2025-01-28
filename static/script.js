// ----------------------------------------------------
// script.js
// ----------------------------------------------------
function extractTextContentBlock(fullText) {
  const regex = /\[TextContentBlock\(.*?value=(['"])([\s\S]*?)\1.*?\)\]/;
  const match = regex.exec(fullText);
  if (match && match[2]) {
    return match[2];
  }
  return null;
}

/**
 * Gelen tek bir Markdown tablosunu HTML'e çevirir.
 */
function markdownTableToHTML(mdTable) {
  const lines = mdTable.trim().split("\n").map(line => line.trim());
  if (lines.length < 2) {
    return `<p>${mdTable}</p>`;
  }

  const headerLine = lines[0];
  const headerCells = headerLine.split("|").map(cell => cell.trim()).filter(Boolean);
  const bodyLines = lines.slice(2);

  let html = `<table class="table table-bordered table-sm my-blue-table">
<thead><tr>`;
  headerCells.forEach(cell => {
    html += `<th>${cell}</th>`;
  });
  html += `</tr></thead>
<tbody>
`;

  bodyLines.forEach(line => {
    if (!line.trim()) return;
    const cols = line.split("|").map(col => col.trim()).filter(Boolean);
    if (cols.length === 0) return;

    html += `<tr>`;
    cols.forEach(col => {
      html += `<td>${col}</td>`;
    });
    html += `</tr>
`;
  });

  html += `</tbody>
</table>`;
  return html;
}

/**
 * processBotMessage: Backend'den gelen cevabı parçalayıp
 * tabloları bulup işleyen fonksiyon. Eğer tablo
 * altına gelen metin varsa, onu ayrı bir baloncuya koyar.
 */
function processBotMessage(fullText, uniqueId) {
  // Normalleştirme
  const normalizedText = fullText.replace(/\\n/g, "\n");
  const extractedValue = extractTextContentBlock(normalizedText);
  const textToCheck = extractedValue ? extractedValue : normalizedText;

  // Birden çok tablo aramak için global regex
  const tableRegexGlobal = /(\|.*?\|\n\|.*?\|\n[\s\S]+?)(?=\n\n|$)/g;

  let finalHTML = "";
  let newBubbles = [];  // Tablonun altındaki metin veya son satırları burada toplayacağız
  let lastIndex = 0;
  let match;

  while ((match = tableRegexGlobal.exec(textToCheck)) !== null) {
    const tableMarkdown = match[1];

    // 1) Tablonun öncesindeki düz metin (tablodan önceki kısım)
    const textBefore = textToCheck.substring(lastIndex, match.index);
    if (textBefore.trim()) {
      finalHTML += `<p>${textBefore.trim()}</p>`;
    }

    // 2) Tabloyu satır satır kontrol edip "Bu bilgiler ışığında..." satırını ayıralım
    let lines = tableMarkdown.split("\n");
    let lastLine = lines[lines.length - 1].trim();

    // Son satır "Bu bilgiler ışığında..." gibi başlıyorsa tablo dışına al
    if (lastLine.toLowerCase().startsWith("bu bilgiler ışığında")) {
      lines.pop();
      newBubbles.push(lastLine);
    }

    // 3) Temizlenmiş tablo HTML'e dönüştür
    const cleanedTable = lines.join("\n");
    const tableHTML = markdownTableToHTML(cleanedTable);
    finalHTML += tableHTML;

    lastIndex = tableRegexGlobal.lastIndex;
  }

  // 4) Tablo(lar)dan sonra kalan düz metin => yeni baloncuk
  if (lastIndex < textToCheck.length) {
    const textAfter = textToCheck.substring(lastIndex);
    if (textAfter.trim()) {
      newBubbles.push(textAfter.trim());
    }
  }

  // 5) Ana baloncuya (mesaja) finalHTML'i yerleştir
  $(`#botMessageContent-${uniqueId}`).html(finalHTML);

  // 6) newBubbles içindeki metinleri ayrı baloncuklar olarak ekrana yansıtalım
  if (newBubbles.length > 0) {
    newBubbles.forEach(msg => {
      const newBubbleId = "separateBubble_" + Date.now() + "_" + Math.random();
      const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const botHtml = `
        <div class="d-flex justify-content-start mb-4">
          <img src="static/images/fotograf.png"
               class="rounded-circle user_img_msg"
               alt="bot image">
          <div class="msg_cotainer">
            <span id="botMessageContent-${newBubbleId}">${msg}</span>
          </div>
          <span class="msg_time">${currentTime}</span>
        </div>
      `;
      $("#messageFormeight").append(botHtml);
      $("#messageFormeight").scrollTop($("#messageFormeight")[0].scrollHeight);
    });
  }
}

/**
 * Mesaj gönderme işlevleri (kullanıcıdan input alıp sunucuya /ask endpoint'ine POST vb.)
 */
$(document).ready(function () {
  $("#messageArea").on("submit", function (e) {
    e.preventDefault();
    const inputField = $("#text");
    let rawText = inputField.val().trim();
    if (!rawText) return;

    const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    // Kullanıcı baloncuğu
    const userHtml = `
      <div class="d-flex justify-content-end mb-4">
        <div class="msg_cotainer_send">
          ${rawText}
          <span class="msg_time_send">${currentTime}</span>
        </div>
        <img src="static/images/fotograf.png"
             class="rounded-circle user_img_msg"
             alt="user image">
      </div>
    `;
    $("#messageFormeight").append(userHtml);
    inputField.val("");

    // Bot mesajı için unique ID
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

    // Sunucuya POST isteği
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
        return response.body;
      })
      .then(stream => {
        const reader = stream.getReader();
        const decoder = new TextDecoder("utf-8");
        let botMessage = "";

        function readChunk() {
          return reader.read().then(({ done, value }) => {
            if (done) {
              // Tüm yanıtı aldık; işliyoruz
              processBotMessage(botMessage, uniqueId);
              return;
            }
            const chunkText = decoder.decode(value, { stream: true });
            botMessage += chunkText;
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

    // Örnek: 9. dakika uyarısı
    setTimeout(() => {
      document.getElementById('notificationBar').style.display = 'block';
    }, 9 * 60 * 1000);
  });
});
