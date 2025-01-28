// ----------------------------------------------------
// script.js (Birinci Kod'daki gibi)
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
 * Gelen tek bir Markdown tablosunu HTML'e çevirir (Birinci Kod).
 */
function markdownTableToHTML(mdTable) {
  // 1) Satır bazlı parçalayalım
  const lines = mdTable.trim().split("\n").map(line => line.trim());
  if (lines.length < 2) {
    return `<p>${mdTable}</p>`;
  }

  // 2) İlk satır: başlık satırı
  const headerLine = lines[0];
  const headerCells = headerLine.split("|").map(cell => cell.trim()).filter(Boolean);

  // 3) Gövde satırları (2. satır "---" gibi tablo ayırıcı olabilir)
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
 * tabloları bulup, tablo öncesi / tablo / tablo sonrası
 * kısımlarını ayrı baloncuklar hâlinde gösterir. (Birinci Kod yaklaşımı)
 */
function processBotMessage(fullText, uniqueId) {
  // 1) Metni normalleştirme
  const normalizedText = fullText.replace(/\\n/g, "\n");

  // 2) (Birinci Kod) "TextContentBlock" varsa çek
  const extractedValue = extractTextContentBlock(normalizedText);
  const textToCheck = extractedValue ? extractedValue : normalizedText;

  // 3) Birden çok tablo aramak için global regex
  const tableRegexGlobal = /(\|.*?\|\n\|.*?\|\n[\s\S]+?)(?=\n\n|$)/g;

  // 4) Yeni baloncuklar listesi
  let newBubbles = [];
  let lastIndex = 0;
  let match;

  // 5) Her tabloyu tek tek yakala ve önce/sonra parçaları ayır
  while ((match = tableRegexGlobal.exec(textToCheck)) !== null) {
    const tableMarkdown = match[1];

    // "Tablodan önceki metin"
    const textBefore = textToCheck.substring(lastIndex, match.index).trim();
    if (textBefore) {
      newBubbles.push({
        type: 'text',
        content: textBefore
      });
    }

    // "Tablonun kendisi"
    newBubbles.push({
      type: 'table',
      content: tableMarkdown
    });

    lastIndex = tableRegexGlobal.lastIndex;
  }

  // "Tablo sonrası kalan metin"
  if (lastIndex < textToCheck.length) {
    const textAfter = textToCheck.substring(lastIndex).trim();
    if (textAfter) {
      newBubbles.push({
        type: 'text',
        content: textAfter
      });
    }
  }

  // 6) Daha önce oluşturduğumuz "botMessageContent-uniqueId" baloncuğunu kaldır
  //    (Çünkü artık birden çok baloncuk ekleyeceğiz.)
  $(`#botMessageContent-${uniqueId}`).closest(".d-flex").remove();

  // 7) Tüm parçaları yeni baloncuklar olarak ekrana bas
  newBubbles.forEach((bubble) => {
    const bubbleId = "separateBubble_" + Date.now() + "_" + Math.random();
    const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    let bubbleContent = "";
    if (bubble.type === "table") {
      bubbleContent = markdownTableToHTML(bubble.content);
    } else {
      // Metin normal '\n' -> <br> dönüşümü
      bubbleContent = bubble.content.replace(/\n/g, "<br>");
    }

    const botHtml = `
      <div class="d-flex justify-content-start mb-4">
        <img src="static/images/fotograf.png"
             class="rounded-circle user_img_msg"
             alt="bot image">
        <div class="msg_cotainer">
          <span id="botMessageContent-${bubbleId}">${bubbleContent}</span>
        </div>
        <span class="msg_time">${currentTime}</span>
      </div>
    `;
    $("#messageFormeight").append(botHtml);
    $("#messageFormeight").scrollTop($("#messageFormeight")[0].scrollHeight);
  });
}

/**
 * Mesaj gönderme işlevleri (Birinci Kod'a benzer)
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

    // Bot baloncuğu (önce bir geçici baloncuk)
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

    // Sunucuya POST (stream response)
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
              // Tüm yanıt geldi; işliyoruz
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
