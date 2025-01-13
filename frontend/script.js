document.getElementById('askButton').addEventListener('click', async () => {
  const question = document.getElementById('question').value;
  const responseBox = document.getElementById('response');

  // Kullanıcı boş bir soru gönderirse uyarı ver
  if (!question.trim()) {
      responseBox.style.display = 'block';
      responseBox.className = 'response-box error';
      responseBox.innerText = 'Lütfen bir soru yazın!';
      return;
  }

  // Soru gönderimden önce yanıt kutusunu sıfırla
  responseBox.style.display = 'none';

  try {
      // Backend'e POST isteği gönder
      const response = await fetch('http://127.0.0.1:5000/ask', {
          method: 'POST',
          headers: {
              'Content-Type': 'application/json',
          },
          body: JSON.stringify({ question }),
      });

      // Yanıtı JSON olarak al
      const data = await response.json();

      // Yanıtı ekrana yazdır
      responseBox.style.display = 'block';
      responseBox.className = 'response-box';
      responseBox.innerHTML = `<p>${data.response}</p>`; // innerHTML kullanımı
  } catch (error) {
      // Hata durumunda mesaj göster
      responseBox.style.display = 'block';
      responseBox.className = 'response-box error';
      responseBox.innerText = `Hata: ${error.message}`;
  }
});
