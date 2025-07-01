// web/static/js/display.js

// --- Variables Globales y Configuración ---
let ads = [];
let currentAdIndex = 0;
let callHistory = [];
const MAX_HISTORY = 5; // Número de llamados a mostrar en el historial

// --- Elementos del DOM ---
const clockElement = document.getElementById('clock');
const adContainer = document.getElementById('ad-content');
const adDescriptionElement = document.getElementById('ad-description');
const ticketNumberElement = document.getElementById('ticket-number');
const ticketLocationElement = document.getElementById('ticket-location');
const historyListElement = document.getElementById('history-list');
const ringSound = new Audio('/static/media/ring.mp3');
// Precargamos el audio para que esté listo para ser reproducido
ringSound.preload = 'auto';

/**
 * Actualiza el reloj en la pantalla cada segundo.
 */
function updateClock() {
    const now = new Date();
    const timeString = now.toLocaleTimeString('es-VE', { hour: '2-digit', minute: '2-digit' });
    if (clockElement) {
        clockElement.textContent = timeString;
    }
}

/**
 * Muestra el siguiente anuncio (imagen o video) en el carrusel.
 */
function showNextAd() {
    if (ads.length === 0) return;
    
    const ad = ads[currentAdIndex];
    adContainer.innerHTML = ''; // Limpiamos el contenedor

    if (ad.media && ad.media.length > 0) {
        const mediaFile = ad.media[0]; // Por ahora, mostramos solo el primer archivo
        if (mediaFile.type.startsWith('video/')) {
            const video = document.createElement('video');
            video.src = mediaFile.path;
            video.autoplay = true;
            video.muted = true;
            video.loop = true;
            video.className = 'w-full h-full object-cover';
            adContainer.appendChild(video);
        } else if (mediaFile.type.startsWith('image/')) {
            const img = document.createElement('img');
            img.src = mediaFile.path;
            img.className = 'w-full h-full object-cover';
            adContainer.appendChild(img);
        }
    }
    
    adDescriptionElement.textContent = ad.description;
    currentAdIndex = (currentAdIndex + 1) % ads.length;
}

/**
 * Actualiza la información del ticket llamado en pantalla.
 * @param {object} callData - Datos del llamado { ticket_number, location }.
 */
function updateCallDisplay(callData) {
    ticketNumberElement.textContent = callData.ticket_number;
    ticketLocationElement.textContent = callData.location;

    // Animación de resaltado
    const displayBox = document.getElementById('call-display');
    if (displayBox) {
        displayBox.classList.remove('ticket-number');
        void displayBox.offsetWidth; // Truco para reiniciar la animación
        displayBox.classList.add('ticket-number');
    }
    
    // --- INICIO DE CORRECCIÓN DE AUDIO ---
    // La reproducción de audio debe ser iniciada por una interacción.
    // Aunque el WebSocket no es una interacción directa, podemos intentar
    // reproducir el audio y manejar cualquier error que surja.
    // La mejor práctica es pedir al usuario que haga clic en la pantalla una vez
    // para "habilitar" el audio.
    const playPromise = ringSound.play();

    if (playPromise !== undefined) {
        playPromise.then(_ => {
            // La reproducción comenzó exitosamente
            console.log("Audio de llamado reproducido.");
        }).catch(error => {
            // La reproducción automática fue bloqueada.
            console.error("Error al reproducir el sonido:", error);
            // Podríamos mostrar un ícono de "audio desactivado" para que el usuario
            // haga clic y lo habilite.
        });
    }
    // --- FIN DE CORRECCIÓN DE AUDIO ---

    // Actualizar historial
    callHistory.unshift(callData); // Añade al principio
    if (callHistory.length > MAX_HISTORY) {
        callHistory.pop(); // Elimina el más antiguo
    }
    updateHistoryList();
}

/**
 * Renderiza la lista del historial de llamados.
 */
function updateHistoryList() {
    historyListElement.innerHTML = '';
    callHistory.forEach(call => {
        const li = document.createElement('li');
        li.className = 'text-2xl font-bold p-2 bg-gray-700 rounded-md';
        li.innerHTML = `<span class="text-cyan-400">${call.ticket_number}</span> &rarr; <span class="text-white">${call.location}</span>`;
        historyListElement.appendChild(li);
    });
}

/**
 * Conecta al WebSocket y maneja los mensajes entrantes.
 * @param {number} companyId - El ID de la compañía.
 */
function connectWebSocket(companyId) {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/api/v1/ws/display/${companyId}`;
    const socket = new WebSocket(wsUrl);

    socket.onmessage = function(event) {
        try {
            const message = JSON.parse(event.data);
            if (message.event === 'new_call') {
                updateCallDisplay(message.data);
            }
        } catch (e) {
            console.error('Error al procesar mensaje del WebSocket:', e);
        }
    };

    socket.onclose = function() {
        console.log('WebSocket desconectado. Intentando reconectar en 5 segundos...');
        setTimeout(() => connectWebSocket(companyId), 5000);
    };

    socket.onerror = function(error) {
        console.error('Error en WebSocket:', error);
    };
}

/**
 * Obtiene la lista de anuncios desde la API.
 * @param {number} companyId - El ID de la compañía.
 */
async function fetchAdvertisements(companyId) {
    try {
        const response = await fetch(`/api/v1/get-ads/${companyId}`);
        if (!response.ok) {
            throw new Error(`Error en la red: ${response.statusText}`);
        }
        ads = await response.json();
        if (ads.length > 0) {
            showNextAd();
            setInterval(showNextAd, 15000); // Cambiar de anuncio cada 15 segundos
        } else {
            adDescriptionElement.textContent = "No hay anuncios para mostrar.";
        }
    } catch (error) {
        console.error('No se pudieron cargar los anuncios:', error);
        adDescriptionElement.textContent = "Error al cargar publicidad.";
    }
}

/**
 * Función principal que inicializa el display.
 * @param {number} companyId - El ID de la compañía.
 */
function initializeDisplay(companyId) {
    // Inicializar reloj
    updateClock();
    setInterval(updateClock, 1000);

    // Conectar WebSocket
    connectWebSocket(companyId);

    // Cargar anuncios
    fetchAdvertisements(companyId);

    // Se añade un evento para que, al primer clic del usuario en cualquier
    // parte de la pantalla, se intente reproducir y pausar el audio.
    // Esto "desbloquea" la capacidad del navegador para reproducir sonidos más tarde.
    document.body.addEventListener('click', () => {
        ringSound.play();
        ringSound.pause();
    }, { once: true });
}