// ----------------------------------------------------
// script.js (Tablolu cevap + özel parçalama yaklaşımı)
// ----------------------------------------------------

function extractTextContentBlock(fullText) {
  const regex = /\[TextContentBlock\(.*?value=(['"])([\s\S]*?)\1.*?\)\]/;
  const match = regex.exec(fullText);
  if (match && match[2]) {
    return match[2];
  }
  return null;
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
  html += `</tr></thead><tbody>\n`;

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

function splitNonTableTextIntoBubbles(fullText) {
  const trimmedText = fullText.trim();
  const lines = trimmedText.split(/\r?\n/);

  let firstColonIndex = -1;
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].trim().match(/:$/)) {
      firstColonIndex = i;
      break;
    }
  }

  function findMoreInfoLineIndex(startIndex, arr) {
    for (let i = startIndex; i < arr.length; i++) {
      if (arr[i].toLowerCase().includes("daha fazla bilgi almak istediğiniz")) {
        return i;
      }
    }
    return -1;
  }

  let resultBubbles = [];
  if (firstColonIndex !== -1) {
    const bubble1 = lines[firstColonIndex].trim();
    resultBubbles.push(bubble1);

    const restLines = lines.slice(firstColonIndex + 1);
    const moreInfoIndex = findMoreInfoLineIndex(0, restLines);
    if (moreInfoIndex !== -1) {
      const bubble2 = restLines.slice(0, moreInfoIndex).join("\n").trim();
      if (bubble2) {
        resultBubbles.push(bubble2);
      }
      const bubble3 = restLines[moreInfoIndex].trim();
      resultBubbles.push(bubble3);
      if (moreInfoIndex + 1 < restLines.length) {
        const bubble4 = restLines.slice(moreInfoIndex + 1).join("\n").trim();
        if (bubble4) {
          resultBubbles.push(bubble4);
        }
      }
    } else {
      const bubble2 = restLines.join("\n").trim();
      if (bubble2) {
        resultBubbles.push(bubble2);
      }
    }
  } else {
    const moreInfoIndex = findMoreInfoLineIndex(0, lines);
    if (moreInfoIndex !== -1) {
      const bubble1 = lines.slice(0, moreInfoIndex).join("\n").trim();
      if (bubble1) {
        resultBubbles.push(bubble1);
      }
      resultBubbles.push(lines[moreInfoIndex].trim());
      if (moreInfoIndex + 1 < lines.length) {
        const bubble3 = lines.slice(moreInfoIndex + 1).join("\n").trim();
        if (bubble3) {
          resultBubbles.push(bubble3);
        }
      }
    } else {
      resultBubbles.push(trimmedText);
    }
  }
  return resultBubbles;
}

function processBotMessage(fullText, uniqueId) {
  const normalizedText = fullText
    .replace(/\\n/g, "\n")
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/[–—]/g, '-');

  const extractedValue = extractTextContentBlock(normalizedText);
  const textToCheck = extractedValue ? extractedValue : normalizedText;

  const tableRegexGlobal = /(\|.*?\|\n\|.*?\|\n[\s\S]+?)(?=\n\n|$)/g;
  let newBubbles = [];
  let lastIndex = 0;
  let match;

  while ((match = tableRegexGlobal.exec(textToCheck)) !== null) {
    const tableMarkdown = match[1];
    const textBefore = textToCheck.substring(lastIndex, match.index).trim();
    if (textBefore) {
      const splittedTextBubbles = splitNonTableTextIntoBubbles(textBefore);
      splittedTextBubbles.forEach(subPart => {
        newBubbles.push({ type: 'text', content: subPart });
      });
    }
    newBubbles.push({ type: 'table', content: tableMarkdown });
    lastIndex = tableRegexGlobal.lastIndex;
  }

  if (lastIndex < textToCheck.length) {
    const textAfter = textToCheck.substring(lastIndex).trim();
    if (textAfter) {
      const splittedTextBubbles = splitNonTableTextIntoBubbles(textAfter);
      splittedTextBubbles.forEach(subPart => {
        newBubbles.push({ type: 'text', content: subPart });
      });
    }
  }

  // -- ÖZEL KONTROL: 2. baloncuk varsa, son satırı '-' ile başlamıyorsa 3. baloncuğa taşı
  if (newBubbles.length >= 3) {
    let secondBubble = newBubbles[1];
    let thirdBubble  = newBubbles[2];
    if (secondBubble.type === "text" && thirdBubble.type === "text") {
      let lines = secondBubble.content.split(/\r?\n/).map(line => line.trim());
      if (lines.length > 0) {
        let lastLine = lines[lines.length - 1];
        if (!lastLine.startsWith('-')) {
          lines.pop();
          secondBubble.content = lines.join('\n');
          if (thirdBubble.content.trim()) {
            thirdBubble.content = lastLine + '\n' + thirdBubble.content;
          } else {
            thirdBubble.content = lastLine;
          }
        }
      }
    }
  }

  // EĞER 2. BALONCUĞUN SON SATIRINI ZORLA KOPARMAK İSTİYORSANIZ
  if (newBubbles.length === 2) {
    let secondBubble = newBubbles[1];
    if (secondBubble.type === "text") {
      let lines = secondBubble.content.split(/\r?\n/).map(l => l.trim());
      if (lines.length > 0) {
        let lastLine = lines[lines.length - 1];
        if (!lastLine.startsWith('-')) {
          lines.pop();
          secondBubble.content = lines.join('\n');
          if (newBubbles[2]) {
            newBubbles[2].content = lastLine + '\n' + newBubbles[2].content;
          } else {
            // Yeni bir baloncuk yarat
            newBubbles.push({ type: 'text', content: lastLine });
          }
        }
      }
    }
  }

  $(`#botMessageContent-${uniqueId}`).closest(".d-flex").remove();

  newBubbles.forEach((bubble) => {
    const bubbleId = "separateBubble_" + Date.now() + "_" + Math.random();
    const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    let bubbleContent = "";
    if (bubble.type === "table") {
      bubbleContent = markdownTableToHTML(bubble.content);
    } else {
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

    setTimeout(() => {
      document.getElementById('notificationBar').style.display = 'block';
    }, 9 * 60 * 1000);
  });
});