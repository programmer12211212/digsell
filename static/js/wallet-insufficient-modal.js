/**
 * Shared insufficient-balance modal with auto top-up and manual receipt options.
 */
(function (global) {
    'use strict';

    function getCsrfToken() {
        if (global.getHamyonCsrfToken) return global.getHamyonCsrfToken();
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        return input ? input.value : '';
    }

    class WalletInsufficientModal {
        constructor(config) {
            this.config = Object.assign({
                minTopup: 5000,
                topupUrl: '/payments/wallet/auto-topup/',
                receiptUrl: '/payments/topup/',
                walletUrl: '/payments/wallet/',
            }, config || {});
            this.modalEl = null;
        }

        close() {
            if (this.modalEl) {
                this.modalEl.remove();
                this.modalEl = null;
            }
        }

        open(options) {
            this.close();
            const required = Number(options.requiredAmount || 0);
            const balance = Number(options.walletBalance || 0);
            const shortfall = Math.max(required - balance, this.config.minTopup);
            const suggested = Math.max(this.config.minTopup, Math.ceil(shortfall / 1000) * 1000);

            const wrapper = document.createElement('div');
            wrapper.innerHTML = `
                <div class="hamyon-pay-overlay wallet-insufficient-overlay" data-wallet-insufficient-modal>
                    <div class="hamyon-pay-modal wallet-insufficient-modal" role="dialog" aria-modal="true">
                        <div class="hamyon-pay-modal__header">
                            <div>
                                <h3 style="color:#fff;font-weight:800;font-size:1.05rem;margin:0;">Balans yetarli emas</h3>
                                <p style="color:rgba(255,255,255,.45);font-size:.65rem;text-transform:uppercase;letter-spacing:.14em;margin:.25rem 0 0;">Hisobingizni to'ldiring</p>
                            </div>
                            <button type="button" class="hamyon-pay-btn hamyon-pay-btn--ghost" style="flex:0 0 auto;width:2.25rem;height:2.25rem;padding:0;" data-wallet-close>&times;</button>
                        </div>
                        <div class="hamyon-pay-modal__body">
                            <p style="color:rgba(255,255,255,.75);font-size:.875rem;line-height:1.5;margin:0 0 1rem;">
                                Hisobingizda mablag' yetarli emas. Xaridni davom ettirish uchun hamyoningizni to'ldiring.
                            </p>
                            <div class="hamyon-pay-details">
                                <div class="hamyon-pay-row"><span>Joriy balans:</span><strong>${balance.toLocaleString('uz-UZ')} UZS</strong></div>
                                <div class="hamyon-pay-row"><span>Kerak:</span><strong>${required.toLocaleString('uz-UZ')} UZS</strong></div>
                            </div>
                            <label style="display:block;font-size:.625rem;color:rgba(255,255,255,.4);text-transform:uppercase;letter-spacing:.12em;margin:1rem 0 .35rem;">
                                Hisobingizni qancha summaga to'ldirmoqchisiz?
                            </label>
                            <input type="number" min="${this.config.minTopup}" step="1000" value="${suggested}"
                                data-wallet-topup-amount
                                class="w-full bg-black/30 border border-white/10 rounded-xl px-4 py-3 text-white outline-none focus:border-sky-400/50" />
                            <p style="font-size:.65rem;color:rgba(255,255,255,.35);margin:.5rem 0 0;">Minimal: ${this.config.minTopup.toLocaleString('uz-UZ')} so'm</p>
                            <div class="hamyon-pay-actions" style="margin-top:1.25rem;">
                                <button type="button" class="hamyon-pay-btn hamyon-pay-btn--primary" data-wallet-auto-topup>Avto to'lov</button>
                                <button type="button" class="hamyon-pay-btn" data-wallet-receipt>Chek yuborish</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            document.body.appendChild(wrapper.firstElementChild);
            this.modalEl = document.querySelector('[data-wallet-insufficient-modal]');

            this.modalEl.querySelector('[data-wallet-close]').addEventListener('click', () => this.close());
            this.modalEl.querySelector('[data-wallet-receipt]').addEventListener('click', () => {
                this.close();
                if (typeof options.onReceipt === 'function') {
                    options.onReceipt();
                } else {
                    window.location.href = this.config.walletUrl;
                }
            });
            this.modalEl.querySelector('[data-wallet-auto-topup]').addEventListener('click', async () => {
                const amount = this.modalEl.querySelector('[data-wallet-topup-amount]').value;
                if (!amount || Number(amount) < this.config.minTopup) {
                    alert(`Minimal summa ${this.config.minTopup.toLocaleString('uz-UZ')} so'm`);
                    return;
                }
                if (typeof options.onAutoTopup === 'function') {
                    await options.onAutoTopup(amount);
                    return;
                }
                if (global.walletHamyonController) {
                    this.close();
                    const formData = new FormData();
                    formData.append('amount', amount);
                    formData.append('format', 'json');
                    await global.walletHamyonController.start(formData, {
                        title: "Hamyon To'lovi",
                        subtitle: 'Balans to\'ldirish',
                        serviceLabel: 'Hamyon balansi',
                        amountLabel: `${amount} UZS`,
                    });
                }
            });
        }
    }

    global.WalletInsufficientModal = WalletInsufficientModal;
})(window);
