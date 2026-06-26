/**
 * Unified Hamyon payment controller — shared across all modules.
 */
(function (global) {
    'use strict';

    const FINAL_UI_STATUSES = new Set(['SUCCESS', 'FAILED', 'CANCELLED', 'EXPIRED']);

    function getCsrfToken() {
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        if (input && input.value) return input.value;
        const hidden = document.getElementById('csrfToken');
        if (hidden && hidden.value) return hidden.value;
        const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : '';
    }

    function notify(message, type) {
        if (global.Toast) {
            new global.Toast(message, type || 'info');
            return;
        }
        if (type === 'danger' || type === 'error') {
            console.error(message);
        } else {
            console.log(message);
        }
    }

    class HamyonPaymentController {
        constructor(config) {
            this.config = Object.assign({
                pollIntervalMs: 5000,
                fastPollIntervalMs: 2000,
                statusUrlTemplate: '/payments/hamyon/{id}/status/',
                cancelUrlTemplate: '/payments/hamyon/{id}/cancel/',
                createUrl: '/payments/hamyon/create/',
            }, config || {});

            this.activePaymentPk = null;
            this.pollTimer = null;
            this.countdownTimer = null;
            this.requestInFlight = false;
            this.pollingActive = false;
            this.paymentSucceeded = false;
            this.currentPollDelay = this.config.pollIntervalMs;
            this.modalEl = null;
        }

        urlFromTemplate(template, paymentPk) {
            return String(template).replace('{id}', paymentPk);
        }

        normalizePaymentData(data) {
            if (data.payment) {
                const src = data.payment;
                const paymentPk = src.payment_pk || src.payment_id || src.id;
                return {
                    payment_pk: paymentPk,
                    payment_id: paymentPk,
                    external_id: src.external_id || '',
                    card: src.card || '',
                    amount: src.amount || '',
                    expires_at: src.expires_at_epoch || src.expires_at || null,
                };
            }

            const paymentPk = data.payment_pk || data.payment_id || data.id;
            return {
                payment_pk: paymentPk,
                payment_id: paymentPk,
                external_id: (data.payment_pk && data.payment_id && String(data.payment_id) !== String(data.payment_pk))
                    ? data.payment_id
                    : (data.external_id || ''),
                card: data.card || '',
                amount: data.amount || '',
                expires_at: data.expires_at_epoch || data.expires_at || null,
            };
        }

        async createPayment(formData) {
            const response = await fetch(this.config.createUrl, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json',
                },
                credentials: 'same-origin',
                body: formData || undefined,
            });

            const data = await response.json().catch(() => ({}));
            if (!response.ok || !data.success) {
                throw new Error(data.message || `Server error ${response.status}`);
            }
            return this.normalizePaymentData(data);
        }

        async fetchStatus(paymentPk) {
            const url = this.urlFromTemplate(this.config.statusUrlTemplate, paymentPk) + '?refresh=1';
            const response = await fetch(url, {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                },
                credentials: 'same-origin',
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok || data.success === false) {
                throw new Error(data.message || `Status check failed (${response.status})`);
            }
            return data;
        }

        async cancelPayment(paymentPk) {
            const url = this.urlFromTemplate(this.config.cancelUrlTemplate, paymentPk);
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json',
                },
                credentials: 'same-origin',
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok || !data.success) {
                throw new Error(data.message || 'Cancel failed');
            }
            return data;
        }

        stopPolling() {
            this.pollingActive = false;
            if (this.pollTimer) {
                clearTimeout(this.pollTimer);
                this.pollTimer = null;
            }
            this.requestInFlight = false;
        }

        stopCountdown() {
            if (this.countdownTimer) {
                clearInterval(this.countdownTimer);
                this.countdownTimer = null;
            }
        }

        showRetryAction(uiStatus) {
            const actions = this.modalEl && this.modalEl.querySelector('.hamyon-pay-actions');
            if (!actions || actions.querySelector('[data-hamyon-retry]')) return;

            const retryBtn = document.createElement('button');
            retryBtn.type = 'button';
            retryBtn.className = 'hamyon-pay-btn hamyon-pay-btn--primary';
            retryBtn.setAttribute('data-hamyon-retry', '1');
            retryBtn.textContent = uiStatus === 'FAILED' ? 'Qayta urinish' : 'Yopish';
            retryBtn.addEventListener('click', () => {
                this.closeModal();
                if (typeof this.config.onRetry === 'function') {
                    this.config.onRetry(uiStatus);
                }
            });

            const cancelBtn = actions.querySelector('[data-hamyon-cancel]');
            if (cancelBtn) cancelBtn.remove();
            actions.appendChild(retryBtn);
        }

        closeModal() {
            this.stopPolling();
            this.stopCountdown();
            if (this.modalEl) {
                this.modalEl.remove();
                this.modalEl = null;
            }
        }

        setStatusText(message, variant) {
            const el = this.modalEl && this.modalEl.querySelector('[data-hamyon-status]');
            if (!el) return;
            el.textContent = message;
            el.classList.remove('is-error', 'is-success', 'is-processing');
            if (variant) el.classList.add(variant);
        }

        updateTimeline(deliveryStatus) {
            const container = this.modalEl && this.modalEl.querySelector('[data-hamyon-timeline]');
            if (!container) return;

            const steps = this.config.timelineSteps || [
                { key: 'waiting', label: "To'lov kutilmoqda" },
                { key: 'paid', label: "To'lov tasdiqlandi" },
                { key: 'processing', label: 'Yetkazish boshlandi' },
                { key: 'completed', label: 'Bajarildi' },
            ];

            const order = ['waiting', 'waiting_payment', 'pending', 'paid', 'processing', 'completed', 'delivered'];
            const current = String(deliveryStatus || 'waiting').toLowerCase();
            const currentIndex = Math.max(0, order.indexOf(current));

            container.innerHTML = steps.map((step, idx) => {
                const stepIndex = order.indexOf(step.key);
                const isDone = stepIndex >= 0 && stepIndex < currentIndex;
                const isActive = step.key === current || stepIndex === currentIndex;
                const cls = isDone ? 'is-done' : (isActive ? 'is-active' : '');
                return `<div class="hamyon-pay-step ${cls}"><span class="hamyon-pay-step-dot"></span><span>${step.label}</span></div>`;
            }).join('');
        }

        renderGiftAdminContact(contactPayload) {
            if (!this.modalEl) return;
            const payload = contactPayload || this.config.giftAdminContact || null;
            if (!payload || !payload.is_visible) {
                const existing = this.modalEl.querySelector('[data-hamyon-gift-admin]');
                if (existing) existing.remove();
                return;
            }

            const statusWrap = this.modalEl.querySelector('.hamyon-pay-status');
            if (!statusWrap) return;

            let container = this.modalEl.querySelector('[data-hamyon-gift-admin]');
            if (!container) {
                container = document.createElement('div');
                container.setAttribute('data-hamyon-gift-admin', '1');
                statusWrap.insertAdjacentElement('afterend', container);
            }

            const successMessage = String(payload.success_message || '').replace(/\n/g, '<br>');
            const statusEl = this.modalEl.querySelector('[data-hamyon-status]');
            if (statusEl) {
                statusEl.innerHTML = successMessage;
                statusEl.className = 'hamyon-pay-status__text is-success';
            }

            container.innerHTML = `
                <div style="margin-top:14px;padding:14px 14px 12px;border-radius:16px;background:linear-gradient(135deg,rgba(59,130,246,.2),rgba(37,99,235,.12));border:1px solid rgba(96,165,250,.25);box-shadow:0 18px 40px rgba(37,99,235,.16);">
                    <div style="font-size:12px;line-height:1.65;color:#eff6ff;font-weight:700;margin-bottom:10px;white-space:pre-line;">${successMessage}</div>
                    <a href="${payload.url || '#'}" target="_blank" rel="noopener noreferrer" style="width:100%;height:52px;border-radius:14px;display:inline-flex;align-items:center;justify-content:center;gap:10px;color:#fff;font-weight:800;font-size:14px;text-decoration:none;background:linear-gradient(135deg,#60a5fa 0%,#2563eb 100%);border:1px solid rgba(255,255,255,.18);box-shadow:0 14px 32px rgba(37,99,235,.26);transition:transform .2s ease,box-shadow .2s ease;animation:giftContactModalGlow 2.3s ease-in-out infinite;">
                        <span style="font-size:14px;">✈</span>
                        <span>${payload.button_label || '💬 Adminga yozish'}</span>
                    </a>
                </div>
            `;

            const styleId = 'hamyon-gift-contact-style';
            if (!document.getElementById(styleId)) {
                const style = document.createElement('style');
                style.id = styleId;
                style.textContent = '@keyframes giftContactModalGlow{0%,100%{box-shadow:0 14px 32px rgba(37,99,235,.26)}50%{box-shadow:0 18px 42px rgba(59,130,246,.4)}}';
                document.head.appendChild(style);
            }
        }

        showConfetti() {
            const container = document.createElement('div');
            container.className = 'fixed inset-0 pointer-events-none z-[110]';
            const colors = ['#60a5fa', '#34d399', '#fbbf24', '#f87171', '#a78bfa'];
            for (let i = 0; i < 24; i++) {
                const piece = document.createElement('div');
                piece.style.cssText = `
                    position:absolute;width:8px;height:8px;top:-10px;left:${Math.random() * 100}%;
                    background:${colors[Math.floor(Math.random() * colors.length)]};
                    animation:hamyonConfetti 2.8s ease-in forwards;
                    animation-delay:${Math.random() * 0.4}s;
                `;
                container.appendChild(piece);
            }
            if (!document.getElementById('hamyon-confetti-style')) {
                const style = document.createElement('style');
                style.id = 'hamyon-confetti-style';
                style.textContent = '@keyframes hamyonConfetti{to{transform:translateY(100vh) rotate(720deg);opacity:0}}';
                document.head.appendChild(style);
            }
            document.body.appendChild(container);
            setTimeout(() => container.remove(), 3200);
        }

        openModal(payment, meta) {
            this.closeModal();
            this.activePaymentPk = payment.payment_pk || payment.payment_id || payment.id;
            this.paymentSucceeded = false;
            this.currentPollDelay = this.config.pollIntervalMs;
            this.pollingActive = true;

            const title = meta.title || "Hamyon To'lovi";
            const subtitle = meta.subtitle || 'Avtomatik tekshiruv';
            const serviceLabel = meta.serviceLabel || '';
            const actualAmount = payment.actual_amount || payment.amount || '';
            const requestedAmount = payment.requested_amount || '';
            const amountLabel = meta.amountLabel || `${actualAmount} UZS`;
            const cardHolder = payment.card_holder || '';
            const paymentCode = payment.payment_code || '';
            const showRequested = requestedAmount && String(requestedAmount) !== String(actualAmount);

            const wrapper = document.createElement('div');
            wrapper.innerHTML = `
                <div class="hamyon-pay-overlay" data-hamyon-modal>
                    <div class="hamyon-pay-modal" role="dialog" aria-modal="true">
                        <div class="hamyon-pay-modal__header">
                            <div>
                                <h3 style="color:#fff;font-weight:800;font-size:1.05rem;margin:0;">${title}</h3>
                                <p style="color:rgba(255,255,255,.45);font-size:.65rem;text-transform:uppercase;letter-spacing:.14em;margin:.25rem 0 0;">${subtitle}</p>
                            </div>
                            <button type="button" class="hamyon-pay-btn hamyon-pay-btn--ghost" style="flex:0 0 auto;width:2.25rem;height:2.25rem;padding:0;" data-hamyon-close>&times;</button>
                        </div>
                        <div class="hamyon-pay-modal__body">
                            <div class="hamyon-pay-details">
                                ${serviceLabel ? `<div class="hamyon-pay-row"><span>Xizmat:</span><strong>${serviceLabel}</strong></div>` : ''}
                                ${showRequested ? `<div class="hamyon-pay-row"><span>So'ralgan:</span><strong>${requestedAmount} UZS</strong></div>` : ''}
                                <div>
                                    <div style="font-size:.625rem;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.12em;margin-bottom:.35rem;">Aniq to'lov summasi</div>
                                    <div class="hamyon-pay-card-box hamyon-pay-amount-box">
                                        <code data-hamyon-amount style="font-size:1.15rem;font-weight:800;">${actualAmount} UZS</code>
                                        <button type="button" class="hamyon-pay-btn hamyon-pay-btn--ghost" style="flex:0 0 auto;width:auto;padding:0 .5rem;" data-hamyon-copy-amount>Nusxa</button>
                                    </div>
                                </div>
                                ${cardHolder ? `<div class="hamyon-pay-row"><span>Karta egasi:</span><strong>${cardHolder}</strong></div>` : ''}
                                <div>
                                    <div style="font-size:.625rem;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.12em;margin-bottom:.35rem;">Karta raqami</div>
                                    <div class="hamyon-pay-card-box">
                                        <code data-hamyon-card>${payment.card || ''}</code>
                                        <button type="button" class="hamyon-pay-btn hamyon-pay-btn--ghost" style="flex:0 0 auto;width:auto;padding:0 .5rem;" data-hamyon-copy>Nusxa</button>
                                    </div>
                                </div>
                                ${paymentCode ? `<div class="hamyon-pay-row"><span>Kod:</span><strong style="font-family:monospace;">${paymentCode}</strong></div>` : ''}
                                <div class="hamyon-pay-row"><span>Payment ID:</span><strong style="font-family:monospace;font-size:.75rem;">${payment.external_id || ''}</strong></div>
                            </div>
                            <div class="hamyon-pay-status">
                                <div class="hamyon-pay-status__row">
                                    <span class="hamyon-pay-status__text" data-hamyon-status>To'lov kutilmoqda...</span>
                                    <span class="hamyon-pay-countdown hamyon-pay-countdown--lg" data-hamyon-countdown>05:00</span>
                                </div>
                                <p class="hamyon-pay-hint">Aynan ko'rsatilgan summani karta raqamiga o'tkazing. Tizim har 5 soniyada avtomatik tekshiradi.</p>
                            </div>
                            <div class="hamyon-pay-timeline" data-hamyon-timeline></div>
                            <div class="hamyon-pay-actions">
                                <button type="button" class="hamyon-pay-btn" data-hamyon-cancel>Bekor qilish</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(wrapper.firstElementChild);
            this.modalEl = document.querySelector('[data-hamyon-modal]');

            this.modalEl.querySelector('[data-hamyon-close]').addEventListener('click', () => this.closeModal());
            this.modalEl.querySelector('[data-hamyon-cancel]').addEventListener('click', () => this.handleCancel());
            this.modalEl.querySelector('[data-hamyon-copy]').addEventListener('click', (e) => {
                const card = payment.card || '';
                if (global.copyToClipboard) {
                    global.copyToClipboard(card, e.currentTarget);
                } else if (navigator.clipboard) {
                    navigator.clipboard.writeText(card);
                }
            });
            const copyAmountBtn = this.modalEl.querySelector('[data-hamyon-copy-amount]');
            if (copyAmountBtn) {
                copyAmountBtn.addEventListener('click', (e) => {
                    const amountText = String(actualAmount).replace(/[^\d]/g, '') || String(actualAmount);
                    if (global.copyToClipboard) {
                        global.copyToClipboard(amountText, e.currentTarget);
                    } else if (navigator.clipboard) {
                        navigator.clipboard.writeText(amountText);
                    }
                });
            }

            const expiresAt = payment.expires_at_epoch || payment.expires_at;
            if (expiresAt) {
                const endTs = typeof expiresAt === 'number' ? expiresAt : Math.floor(new Date(expiresAt).getTime() / 1000);
                this.startCountdown(endTs);
            }

            this.updateTimeline('waiting');
            this.schedulePoll();
        }

        startCountdown(endTs) {
            this.stopCountdown();
            const tick = () => {
                const el = this.modalEl && this.modalEl.querySelector('[data-hamyon-countdown]');
                if (!el) return;
                const now = Math.floor(Date.now() / 1000);
                const left = endTs - now;
                if (left <= 0) {
                    el.textContent = '00:00';
                    this.setStatusText("To'lov muddati tugadi", 'is-error');
                    this.stopPolling();
                    return;
                }
                const m = String(Math.floor(left / 60)).padStart(2, '0');
                const s = String(left % 60).padStart(2, '0');
                el.textContent = `${m}:${s}`;
            };
            tick();
            this.countdownTimer = setInterval(tick, 1000);
        }

        schedulePoll() {
            if (!this.pollingActive) return;
            if (this.pollTimer) clearTimeout(this.pollTimer);
            this.pollTimer = setTimeout(() => this.poll(), this.currentPollDelay);
        }

        async poll() {
            if (!this.pollingActive || this.requestInFlight || !this.activePaymentPk) return;
            this.requestInFlight = true;
            try {
                const data = await this.fetchStatus(this.activePaymentPk);
                const uiStatus = String(data.ui_status || '').toUpperCase();
                const deliveryStatus = data.delivery_status || data.order_status || '';

                this.updateTimeline(deliveryStatus || (uiStatus === 'WAITING' ? 'waiting' : 'paid'));

                if (uiStatus === 'WAITING') {
                    this.setStatusText(data.message || "To'lov kutilmoqda...", '');
                } else if (uiStatus === 'PROCESSING') {
                    if (!this.paymentSucceeded) {
                        this.paymentSucceeded = true;
                        this.currentPollDelay = this.config.fastPollIntervalMs;
                        notify("✅ To'lov tasdiqlandi!", 'success');
                    }
                    this.setStatusText(data.message || 'Yetkazish jarayoni davom etmoqda...', 'is-processing');
                } else if (uiStatus === 'SUCCESS') {
                    this.renderGiftAdminContact(data.gift_admin_contact || this.config.giftAdminContact || null);
                    this.setStatusText(data.message || "To'lov yakunlandi!", 'is-success');
                    this.showConfetti();
                    this.stopPolling();
                    this.stopCountdown();
                    if (typeof this.config.onSuccess === 'function') {
                        this.config.onSuccess(data);
                    } else {
                        notify("Hisobingiz muvaffaqiyatli to'ldirildi.", 'success');
                        setTimeout(() => {
                            if (data.redirect_url) {
                                window.location.href = data.redirect_url;
                            } else {
                                window.location.reload();
                            }
                        }, 1800);
                    }
                    return;
                } else if (FINAL_UI_STATUSES.has(uiStatus)) {
                    this.setStatusText(data.message || `Holat: ${uiStatus}`, 'is-error');
                    this.stopPolling();
                    this.showRetryAction(uiStatus);
                    return;
                }
            } catch (error) {
                console.error('Hamyon poll error', error);
                this.setStatusText(`Tarmoq xatosi: ${error.message}`, 'is-error');
            } finally {
                this.requestInFlight = false;
                if (this.pollingActive) this.schedulePoll();
            }
        }

        async handleCancel() {
            if (!this.activePaymentPk) return;
            try {
                await this.cancelPayment(this.activePaymentPk);
                this.setStatusText('To\'lov bekor qilindi', 'is-error');
                this.stopPolling();
                notify('To\'lov bekor qilindi', 'info');
            } catch (error) {
                notify(error.message, 'danger');
            }
        }

        async start(formData, meta) {
            let payment;
            if (typeof this.config.createPaymentFn === 'function') {
                payment = this.normalizePaymentData(await this.config.createPaymentFn());
            } else {
                payment = await this.createPayment(formData);
            }
            this.openModal(payment, meta || {});
            return payment;
        }
    }

    global.HamyonPaymentController = HamyonPaymentController;
    global.getHamyonCsrfToken = getCsrfToken;
})(window);
