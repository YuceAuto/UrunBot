function extractTextContentBlock(fullText) {
  // Sadece "value" değerini yakalamak için regex
  const regex = /\[TextContentBlock\(.*?value=(['"])([\s\S]*?)\1.*?\)\]/;
  const match = regex.exec('assets/curr_text.txt', fullText);
  console.log(`Dosya yolu yazıldı`);

  saveToFile('/assets/curr_text.txt', fullText);
  if (match && match[2]) {
    return match[2];
  }
  return null;
}

function saveToFile(fileName, content) {
  // Gerekli modülleri fonksiyon içinde çağır
  const fs = require('fs');
  const path = require('path');

  // Dosya yolu oluştur
  const filePath = path.join(__dirname, fileName);
  console.log(`Dosya yolu yazıldı: ${filePath}`);

  // İçeriği dosyaya yaz (varsa üzerine yazar)
  try {
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`Dosya başarıyla yazıldı: ${filePath}`);
  } catch (error) {
    console.error(`Dosyaya yazılırken bir hata oluştu: ${error.message}`);
  }
}

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

function processBotMessage(fullText, uniqueId) {
  // API'den gelen "\\n" ifadelerini normal "\n" ile değiştiriyoruz
  const normalizedText = fullText.replace(/\\n/g, "\n");

  // Sadece value içeriğini çekiyoruz
  const extractedValue = extractTextContentBlock(normalizedText);

  // Eğer value bulunursa onu, bulunmazsa tüm mesajı kullan
  const textToCheck = extractedValue ? extractedValue : normalizedText;

  // Markdown tablosu var mı diye kontrol
  const tableRegex = /(\|.*?\|\n\|.*?\|\n[\s\S]+)/;
  const tableMatch = tableRegex.exec(textToCheck);

  if (tableMatch && tableMatch[1]) {
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
    // Tablo yoksa normal metni <br> ile dönüştürerek ekle
    const formattedText = textToCheck.replace(/\n/g, "<br>");
    $(`#botMessageContent-${uniqueId}`).html(formattedText);
  }
}

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
        <img src="static/images/fotograf.png"
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

    // 9. dakikada uyarı gösterme
    setTimeout(() => {
      document.getElementById('notificationBar').style.display = 'block';
    }, 9 * 60 * 1000);
  });
});
