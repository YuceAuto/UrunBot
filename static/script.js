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
  // 1) Satır bazlı parçalayalım
  const lines = mdTable.trim().split("\n").map(line => line.trim());
  if (lines.length < 2) {
    return `<p>${mdTable}</p>`;
  }

  // 2) İlk satır: başlık satırı
  const headerLine = lines[0];
  const headerCells = headerLine.split("|").map(cell => cell.trim()).filter(Boolean);

  // 3) Gövde satırları (2. satır "---" gibi tablo ayırıcı olabilir, o yüzden 2'den sonrasını alırız)
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
 * kısımlarını ayrı baloncuklar hâlinde gösterir.
 */
function processBotMessage(fullText, uniqueId) {
  // 1) Metni normalleştirme
  const normalizedText = fullText.replace(/\\n/g, "\n");
  const extractedValue = extractTextContentBlock(normalizedText);
  const textToCheck = extractedValue ? extractedValue : normalizedText;

  // 2) Birden çok tablo aramak için global regex
  const tableRegexGlobal = /(\|.*?\|\n\|.*?\|\n[\s\S]+?)(?=\n\n|$)/g;

  // 3) Yeni baloncuklar listesi
  let newBubbles = [];
  let lastIndex = 0;
  let match;

  // 4) Her tabloyu tek tek yakala ve önce/sonra parçaları ayır
  while ((match = tableRegexGlobal.exec(textToCheck)) !== null) {
    const tableMarkdown = match[1];

    // "Tablodan önceki metin" -> ilk baloncuk
    const textBefore = textToCheck.substring(lastIndex, match.index).trim();
    if (textBefore) {
      newBubbles.push({
        type: 'text',
        content: textBefore
      });
    }

    // "Tablonun kendisi" -> ikinci baloncuk
    newBubbles.push({
      type: 'table',
      content: tableMarkdown
    });

    lastIndex = tableRegexGlobal.lastIndex;
  }

  // "Tablo sonrası kalan metin" -> üçüncü (son) baloncuk
  if (lastIndex < textToCheck.length) {
    const textAfter = textToCheck.substring(lastIndex).trim();
    if (textAfter) {
      newBubbles.push({
        type: 'text',
        content: textAfter
      });
    }
  }

  // 5) Daha önceki "botMessageContent-uniqueId" baloncuğunu kaldır
  //    (Çünkü artık birden fazla baloncuğa böleceğiz.)
  $(`#botMessageContent-${uniqueId}`).closest(".d-flex").remove();

  // 6) Tüm parçaları yeni baloncuklar olarak ekrana bas
  newBubbles.forEach((bubble) => {
    const bubbleId = "separateBubble_" + Date.now() + "_" + Math.random();
    const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    let bubbleContent = "";
    if (bubble.type === "table") {
      bubbleContent = markdownTableToHTML(bubble.content);
    } else {
      bubbleContent = bubble.content;
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
