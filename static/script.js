/***************************************************
 * 1) [TextContentBlock(...)] içinde "value" içeriğini çıkarma (opsiyonel)
 ***************************************************/
function extractTextContentBlock(fullText) {
  const regex = /\[TextContentBlock\(.*?value=(['"])([\s\S]*?)\1.*?\)\]/;
  const match = regex.exec(fullText);
  if (match && match[2]) {
    return match[2];
  }
  return null;
}

/***************************************************
 * 2) Markdown tabloları HTML'e çevirme (basit yaklaşım)
 ***************************************************/
function markdownTableToHTML(mdTable) {
  const lines = mdTable.trim().split("\n").map(line => line.trim());
  if (lines.length < 2) {
    return `<p>${mdTable}</p>`;
  }

  const headerLine = lines[0];
  const headerCells = headerLine.split("|").map(cell => cell.trim()).filter(Boolean);
  const bodyLines = lines.slice(2);

  let html = `<table class="table table-bordered table-sm my-blue-table">\n<thead><tr>`;
  headerCells.forEach(cell => {
    html += `<th>${cell}</th>`;
  });
  html += `</tr></thead>\n<tbody>\n`;

  bodyLines.forEach(line => {
    if (!line.trim()) return;
    const cols = line.split("|").map(col => col.trim()).filter(Boolean);
    if (cols.length === 0) return;

    html += `<tr>`;
    cols.forEach(col => {
      html += `<td>${col}</td>`;
    });
    html += `</tr>\n`;
  });

  html += `</tbody>\n</table>`;
  return html;
}

/***************************************************
 * 3) Metnin içindeki Markdown tabloyu bulma (basit yol)
 ***************************************************/
function processBotMessage(fullText, uniqueId) {
  // \n kaçışlarını gerçek satır sonlarına çevir
  const normalizedText = fullText.replace(/\\n/g, "\n");

  // 1) [TextContentBlock(... value="...")] yapısını yakalayalım (opsiyonel)
  const extractedValue = extractTextContentBlock(normalizedText);

  const textToCheck = extractedValue || normalizedText;

  // 2) Basit bir regex ile tabloyu bulma
  const tableRegex = /(\|.*?\|\n\|.*?\|\n[\s\S]+)/;
  const tableMatch = tableRegex.exec(textToCheck);

  if (tableMatch && tableMatch[1]) {
    // Tam tablo bölgesi
    const markdownTable = tableMatch[1];

    const beforeTable = textToCheck.slice(0, tableMatch.index).trim();
    const afterTable = textToCheck.slice(tableMatch.index + markdownTable.length).trim();

    const tableHTML = markdownTableToHTML(markdownTable);

    let finalHTML = "";
    if (beforeTable) finalHTML += `<p>${beforeTable}</p>`;
    finalHTML += tableHTML;
    if (afterTable) finalHTML += `<p>${afterTable}</p>`;

    $(`#botMessageContent-${uniqueId}`).html(finalHTML);
  } else {
    // Tablolu regex tutmadı
    $(`#botMessageContent-${uniqueId}`).text(textToCheck);
  }
}

/***************************************************
 * 4) Form submit -> /ask -> chunk read
 ***************************************************/
$(document).ready(function () {
  $("#messageArea").on("submit", function (e) {
    e.preventDefault();

    const inputField = $("#text");
    let rawText = inputField.val().trim();
    if (!rawText) return;

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
            // Burada "【...】" gibi şeyleri temizleyebilirsiniz
            botMessage = botMessage.replace(/【.*?】/g, "");
            // Tabloları dönüştür
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
  });

  // 9. dakikada uyarı gösterme
  setTimeout(() => {
    document.getElementById('notificationBar').style.display = 'block';
  }, 9 * 60 * 1000);
});
