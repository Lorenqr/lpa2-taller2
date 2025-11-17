document.addEventListener('DOMContentLoaded', function () {
    const previewBtn = document.getElementById('preview-btn');
    const downloadBtn = document.getElementById('download-btn');
    const closeBtn = document.getElementById('close-preview');
    const idInput = document.getElementById('id_factura');
    const previewContainer = document.getElementById('preview-container');
    const iframe = document.getElementById('pdf-preview');

    // Vista Previa
    if (previewBtn) {
        previewBtn.addEventListener('click', async function () {
            const id = idInput.value && idInput.value.trim();

            if (!id) {
                alert('Por favor, ingresa un ID de factura');
                return;
            }

            try {
                // Mostrar loading
                previewBtn.textContent = 'Generando...';
                previewBtn.disabled = true;

                const form = new FormData();
                form.append('id_factura', id);

                const res = await fetch('/vista-previa-pdf', { method: 'POST', body: form });

                if (!res.ok) {
                    const text = await res.text();
                    alert('Error al generar vista previa: ' + res.status + '\n' + text);
                    return;
                }

                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                iframe.src = url;
                previewContainer.style.display = 'flex';

            } catch (err) {
                alert('Error al generar la vista previa: ' + err.message);
            } finally {
                previewBtn.textContent = 'Vista Previa';
                previewBtn.disabled = false;
            }
        });
    }

    // Descargar PDF
    if (downloadBtn) {
        downloadBtn.addEventListener('click', async function () {
            const id = idInput.value && idInput.value.trim();

            if (!id) {
                alert('Por favor, ingresa un ID de factura');
                return;
            }

            try {
                downloadBtn.textContent = 'Descargando...';
                downloadBtn.disabled = true;

                const form = new FormData();
                form.append('id_factura', id);

                const res = await fetch('/generar-pdf', { method: 'POST', body: form });

                if (!res.ok) {
                    const text = await res.text();
                    alert('Error al descargar PDF: ' + res.status + '\n' + text);
                    return;
                }

                const blob = await res.blob();
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `factura_${id}.pdf`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);

            } catch (err) {
                alert('Error al descargar: ' + err.message);
            } finally {
                downloadBtn.textContent = 'Descargar PDF';
                downloadBtn.disabled = false;
            }
        });
    }

    // Cerrar vista previa
    if (closeBtn) {
        closeBtn.addEventListener('click', function () {
            previewContainer.style.display = 'none';
            iframe.src = '';
        });
    }

    // Cerrar con tecla ESC
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && previewContainer.style.display === 'flex') {
            previewContainer.style.display = 'none';
            iframe.src = '';
        }
    });
});
