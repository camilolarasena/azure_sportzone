'use strict';
(() => {
  const meta = document.querySelector('meta[name="csrf-token"]');
  const csrfToken = meta?.content || '';
  const notify = (message, type = 'success') => {
    let holder = document.querySelector('.alerts');
    if (!holder) { holder = document.createElement('div'); holder.className = 'container alerts'; document.querySelector('main')?.prepend(holder); }
    const node = document.createElement('div'); node.className = `alert alert-${type}`;
    node.textContent = message; holder.prepend(node);
    window.setTimeout(() => node.remove(), 4500);
  };
  const post = async (url, data) => {
    const response = await fetch(url, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrfToken }, body: JSON.stringify(data) });
    let result;
    try { result = await response.json(); } catch { throw new Error('No se pudo interpretar la respuesta del servidor.'); }
    if (!response.ok || !result.ok) throw new Error(result.message || 'No fue posible completar la operación.');
    if (typeof result.cart_count === 'number') { const badge = document.querySelector('#cart-count'); if (badge) badge.textContent = String(result.cart_count); }
    return result;
  };
  document.querySelectorAll('.add-to-cart').forEach(button => button.addEventListener('click', async () => {
    const input = document.getElementById(button.dataset.quantityInput || '');
    const quantity = input ? Number(input.value) : 1;
    if (!Number.isInteger(quantity) || quantity < 1) return notify('Indica una cantidad válida.', 'warning');
    button.disabled = true;
    try { const result = await post('/api/carrito/agregar', { product_id: Number(button.dataset.productId), quantity }); notify(result.message); }
    catch (error) { notify(error.message, 'danger'); }
    finally { button.disabled = false; }
  }));
  document.querySelectorAll('.cart-quantity').forEach(input => input.addEventListener('change', async () => {
    try { await post('/api/carrito/actualizar', { product_id: Number(input.dataset.productId), quantity: Number(input.value) }); window.location.reload(); }
    catch (error) { notify(error.message, 'danger'); }
  }));
  document.querySelectorAll('.remove-from-cart').forEach(button => button.addEventListener('click', async () => {
    try { await post('/api/carrito/actualizar', { product_id: Number(button.dataset.productId), quantity: 0 }); window.location.reload(); }
    catch (error) { notify(error.message, 'danger'); }
  }));
  document.querySelectorAll('.thumbnail').forEach(button => button.addEventListener('click', () => {
    const image = document.getElementById('active-product-image');
    if (image) image.src = button.dataset.imageSrc;
  }));
  const toggle = document.getElementById('nav-toggle');
  const nav = document.getElementById('primary-nav');
  toggle?.addEventListener('click', () => { const active = nav?.classList.toggle('open'); toggle.setAttribute('aria-expanded', String(Boolean(active))); });
})();
