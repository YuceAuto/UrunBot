document.getElementById('askButton').addEventListener('click', async () => {
    const question = document.getElementById('question').value;
    const responseBox = document.getElementById('response');

    // Validate empty question
    if (!question.trim()) {
        responseBox.style.display = 'block';
        responseBox.className = 'response-box error';
        responseBox.innerText = 'Lütfen bir soru yazın!';
        return;
    }

    // Reset response box before sending
    responseBox.style.display = 'none';

    try {
        // Send POST request to the backend
        const response = await fetch('http://127.0.0.1:5000/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question }),
        });

        const data = await response.json();

        // Show the response
        responseBox.style.display = 'block';
        responseBox.className = 'response-box';

        // Build the response output
        let htmlOutput = `<p>${data.response}</p>`;

        // If images are returned, display them
        if (data.images && data.images.length > 0) {
            htmlOutput += '<h3>Eşleşen Resimler:</h3><div class="image-gallery">';
            data.images.forEach((img) => {
                htmlOutput += `<div class="image-item">
                    <p>${img.name}</p>
                    <img src="${img.path}" alt="${img.name}">
                </div>`;
            });
            htmlOutput += '</div>';
        }

        responseBox.innerHTML = htmlOutput;

    } catch (error) {
        responseBox.style.display = 'block';
        responseBox.className = 'response-box error';
        responseBox.innerText = `Hata: ${error.message}`;
    }
});
