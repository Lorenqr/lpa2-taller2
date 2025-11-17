// Frontend JS: muestra el nombre de la empresa y genera vista previa del PDF

document.addEventListener('DOMContentLoaded', function () {
	const companyEl = document.getElementById('company-name');
	const previewBtn = document.getElementById('preview-btn');
	const idInput = document.getElementById('id_factura');
	const previewContainer = document.querySelector('.preview-container');
	const iframe = document.getElementById('pdf-preview');


	// Handler de vista previa: envía el formulario por fetch a /generar-pdf y
	// muestra el PDF resultante en un iframe usando un blob URL.
	if (previewBtn) {
		previewBtn.addEventListener('click', async function () {
			const id = idInput.value && idInput.value.trim();


					try {
						// Primero intentar obtener el nombre de la empresa para este id
						const nameRes = await fetch(`/api/empresa?id=${encodeURIComponent(id)}`);
						if (nameRes.ok) {
							const j = await nameRes.json();
							if (j.nombre && companyEl) companyEl.textContent = j.nombre;
						}

						const form = new FormData();
						form.append('id_factura', id);

						const res = await fetch('/generar-pdf', { method: 'POST', body: form });
				if (!res.ok) {
					const text = await res.text();
					alert('Error al generar vista previa: ' + res.status + '\n' + text);
					return;
				}

				const blob = await res.blob();
				const url = URL.createObjectURL(blob);
				iframe.src = url;
				if (previewContainer) previewContainer.style.display = 'block';
			} catch (err) {
				alert('Error al generar la vista previa: ' + err.message);
			}
		});
	}
});
