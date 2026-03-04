// ============================================================
// DON VITAL - App JavaScript principal
// ============================================================

'use strict';

// ---- Registro del Service Worker ----
if ('serviceWorker' in navigator) {
  window.addEventListener('load', async () => {
    try {
      const reg = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
      console.log('[PWA] Service Worker registrado:', reg.scope);
    } catch (err) {
      console.warn('[PWA] Error registrando SW:', err);
    }
  });
}

// ---- PWA Install Prompt ----
let deferredPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  mostrarBannerInstall();
});

function mostrarBannerInstall() {
  const banner = document.getElementById('pwa-install-banner');
  if (banner) {
    banner.style.display = 'flex';
  }
}

function instalarApp() {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  deferredPrompt.userChoice.then((result) => {
    if (result.outcome === 'accepted') {
      console.log('[PWA] App instalada');
      ocultarBannerInstall();
    }
    deferredPrompt = null;
  });
}

function ocultarBannerInstall() {
  const banner = document.getElementById('pwa-install-banner');
  if (banner) banner.style.display = 'none';
  sessionStorage.setItem('pwa-banner-cerrado', '1');
}

// ---- Sidebar Mobile ----
const menuBtn = document.getElementById('menu-btn');
const sidebar = document.querySelector('.sidebar');
const sidebarOverlay = document.querySelector('.sidebar-overlay');

if (menuBtn && sidebar) {
  menuBtn.addEventListener('click', toggleSidebar);
}

if (sidebarOverlay) {
  sidebarOverlay.addEventListener('click', closeSidebar);
}

function toggleSidebar() {
  sidebar.classList.toggle('open');
  sidebarOverlay.classList.toggle('visible');
  document.body.style.overflow = sidebar.classList.contains('open') ? 'hidden' : '';
}

function closeSidebar() {
  sidebar.classList.remove('open');
  sidebarOverlay.classList.remove('visible');
  document.body.style.overflow = '';
}

// ---- Accesibilidad: fuente grande y alto contraste ----
function aplicarPreferencias() {
  const body = document.body;
  
  // Leer preferencias del servidor (data attributes)
  const fuenteGrande = body.dataset.fuenteGrande === 'true';
  const altoContraste = body.dataset.altoContraste === 'true';
  
  if (fuenteGrande) body.classList.add('fuente-grande');
  if (altoContraste) body.classList.add('alto-contraste');
}

// ---- Auto-cerrar alertas ----
function initAlertas() {
  const alertas = document.querySelectorAll('.alert[data-auto-close]');
  alertas.forEach(alerta => {
    const delay = parseInt(alerta.dataset.autoClose) || 4000;
    setTimeout(() => {
      alerta.style.opacity = '0';
      alerta.style.transform = 'translateY(-10px)';
      alerta.style.transition = 'all 0.3s ease';
      setTimeout(() => alerta.remove(), 300);
    }, delay);
  });
}

// ---- OTP Input: saltar al siguiente input automáticamente ----
function initOTPInput() {
  const otpInput = document.querySelector('.otp-input');
  if (!otpInput) return;
  
  otpInput.addEventListener('input', (e) => {
    const val = e.target.value.replace(/\D/g, '');
    e.target.value = val;
    if (val.length === 6) {
      e.target.form?.submit();
    }
  });
  
  otpInput.focus();
}

// ---- Confirmar cita - AJAX ----
function initConfirmarCita() {
  const btnsConfirmar = document.querySelectorAll('[data-confirmar-cita]');
  btnsConfirmar.forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const citaId = btn.dataset.confirmarCita;
      const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value 
        || getCookie('csrftoken');
      
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span>';
      
      try {
        const resp = await fetch(`/citas/${citaId}/confirmar/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
          }
        });
        
        if (resp.ok || resp.redirected) {
          window.location.reload();
        } else {
          throw new Error('Error al confirmar');
        }
      } catch (err) {
        btn.disabled = false;
        btn.innerHTML = '✅ Confirmar';
        mostrarToast('Error al confirmar la cita. Intenta de nuevo.', 'error');
      }
    });
  });
}

// ---- Marcar notificación leída - AJAX ----
function initNotificaciones() {
  const btnsLeer = document.querySelectorAll('[data-marcar-leida]');
  btnsLeer.forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const notifId = btn.dataset.marcarLeida;
      const csrfToken = getCookie('csrftoken');
      
      try {
        await fetch(`/notificaciones/${notifId}/leer/`, {
          method: 'POST',
          headers: { 'X-CSRFToken': csrfToken, 'X-Requested-With': 'XMLHttpRequest' }
        });
        
        const item = btn.closest('.notif-item');
        if (item) item.classList.remove('no-leida');
        
        const badge = document.querySelector('.badge-count');
        if (badge) {
          const count = parseInt(badge.textContent) - 1;
          if (count <= 0) badge.remove();
          else badge.textContent = count;
        }
      } catch (err) {
        console.error('Error marcando notif:', err);
      }
    });
  });
}

// ---- Registrar FCM Token ----
async function registrarFCMToken() {
  if (!('Notification' in window) || !navigator.serviceWorker) return;
  
  const permission = await Notification.requestPermission();
  if (permission !== 'granted') return;
  
  // Token FCM real requiere Firebase SDK - aquí solo guardamos la intención
  console.log('[FCM] Permiso de notificaciones concedido');
}

// ---- Toast messages ----
function mostrarToast(mensaje, tipo = 'info') {
  const toast = document.createElement('div');
  const tipos = {
    success: { icon: '✅', class: 'alert-success' },
    error: { icon: '❌', class: 'alert-error' },
    warning: { icon: '⚠️', class: 'alert-warning' },
    info: { icon: 'ℹ️', class: 'alert-info' },
  };
  const t = tipos[tipo] || tipos.info;
  
  toast.className = `alert ${t.class}`;
  toast.style.cssText = `
    position: fixed; top: 80px; right: 1rem; z-index: 9999;
    max-width: 360px; animation: fadeIn 0.3s ease;
  `;
  toast.innerHTML = `<span>${t.icon}</span> <span>${mensaje}</span>`;
  
  document.body.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ---- Utilidades ----
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return '';
}

// ---- Contador regresivo para citas del día ----
function initCountdowns() {
  const countdowns = document.querySelectorAll('[data-countdown]');
  countdowns.forEach(el => {
    const targetTime = new Date(el.dataset.countdown);
    
    function actualizar() {
      const diff = targetTime - new Date();
      if (diff <= 0) {
        el.textContent = '¡Ahora!';
        return;
      }
      const h = Math.floor(diff / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      el.textContent = h > 0 ? `${h}h ${m}m` : `${m} min`;
    }
    
    actualizar();
    setInterval(actualizar, 60000);
  });
}

// ---- Inicializar todo ----
document.addEventListener('DOMContentLoaded', () => {
  aplicarPreferencias();
  initAlertas();
  initOTPInput();
  initConfirmarCita();
  initNotificaciones();
  initCountdowns();
  
  // Cerrar banner si ya fue cerrado
  if (sessionStorage.getItem('pwa-banner-cerrado')) {
    ocultarBannerInstall();
  }
  
  // Exponer funciones globales
  window.instalarApp = instalarApp;
  window.ocultarBannerInstall = ocultarBannerInstall;
  window.closeSidebar = closeSidebar;
  window.mostrarToast = mostrarToast;
});
